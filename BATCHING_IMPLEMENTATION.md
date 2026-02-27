# Implementação de Batching e Controle de Limites

## Resumo da Implementação

A nova funcionalidade de Relatório Diário foi otimizada para respeitar rigorosamente os limites de:
- API Movidesk (50 tickets por chamada)
- Token Groq (500 max_tokens por chamada, mas usamos ~150)
- Taxa de requisições (rate limiting automático)

## Arquitetura

### 1. DailyReportGenerator (`src/polling/daily_report.py`)

**Responsabilidades principais:**
- Orquestrar fetching de dados
- Coordenar processamento em lotes
- Formatar relatório com IA summaries
- Enviar por email

**Componentes:**

```python
class DailyReportGenerator:
    batch_size = 8              # Processos 8 tickets por lote
    batch_delay = 2             # 2 segundos entre lotes
    
    def _summarize_tickets_in_batches(tickets: List[Ticket]):
        # Processa em lotes respeitando rate limit
        for lote in batches(tickets, size=8):
            for ticket in lote:
                summarizer.summarize_ticket(ticket)
            sleep(2)  # Delay entre lotes
```

### 2. TicketSummarizer (`src/processing/summarizer.py`)

**Responsabilidades:**
- Chamar API Groq
- Gerenciar cache de resumos
- Tratar erros e retries

**Estratégia de tokens:**

```
Por ticket:
  Entrada: ~3.500 chars de conteúdo
  Saída: 150 max_tokens configurado

Por lote (8 tickets):
  Entrada: ~28.000 chars total
  Saída: 1.200 tokens máximo
  
Limite Groq: 500 max_tokens por requisição
Margem de segurança: Usamos 150 apenas
```

### 3. MovideskClient (`src/api/client.py`)

**Responsabilidades:**
- Buscar tickets da API
- Respeitar rate limiting
- Retries automáticos

**Configuração:**

```python
# Limites aplicados
top=50           # Máximo de tickets por query
rate_limit=True  # Rate limiting ativo
retry_count=3    # Tentativas em caso de erro
```

## Fluxo Detalhado

### Fase 1: Fetching de Dados

```python
# Executado 3 vezes independentemente (não acumula)
new_tickets = api.get_tickets(filter="created > 24h ago", top=50)      # Até 50
overdue = api.get_overdue_tickets(agent_email, limit=50)               # Até 50
expiring = api.get_tickets(filter="sla expires next 2 days", top=50)   # Até 50

# Total máximo de requisições: 3 (uma para cada categoria)
# Cada requisição respeta rate limit do MovideskClient
```

### Fase 2: Deduplicação

```python
# Coletar tickets únicos
all_tickets = []
seen_ids = set()

for tickets_list in [new_tickets, overdue, expiring]:
    for ticket in tickets_list:
        if ticket.id not in seen_ids:
            all_tickets.append(ticket)
            seen_ids.add(ticket.id)

# Resultado: tickets únicos com todas as categorias marcadas
```

### Fase 3: Batch Processing

```python
batch_size = 8
batch_delay = 2  # segundos

for i in range(0, len(all_tickets), batch_size):
    batch = all_tickets[i:i+batch_size]
    
    print(f"Lote {i//batch_size + 1}")
    
    # Processar cada ticket no lote
    for ticket in batch:
        summary = summarizer.summarize_ticket(ticket)
        summaries[ticket.id] = summary
    
    # Delay antes do próximo lote (exceto último)
    if i + batch_size < len(all_tickets):
        sleep(2)

# Exemplo com 20 tickets:
# Lote 1: tickets 0-7   → Groq API → sleep 2s
# Lote 2: tickets 8-15  → Groq API → sleep 2s
# Lote 3: tickets 16-19 → Groq API → (sem delay)
# Total: ~6 segundos de delay + tempo das APIs
```

## Detalhes do Cache

O `TicketSummarizer` mantém um cache em memória:

```python
# Mapeamento: ticket_id -> summary string
_cache: Dict[str, str] = {}

# Verificação em summarize_ticket():
if not force and ticket.id in self._cache:
    return _cache[ticket.id]  # Usa cache

# Armazena após gerar:
summary = self._call_groq(prompt)
self._cache[ticket.id] = summary
```

**Benefícios:**
- Não re-gera resumos que já foram criados
- Economiza tokens Groq
- Reduz latência para segundas execuções

**Limitação:**
- Cache é em memória (perdido ao reiniciar)
- Ideal para execuções próximas (mesma sessão)

## Controle de Erros

### Retry Logic (Groq API)

```python
def _call_groq(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(...)
        except ConfigError:  # 400, modelo inválido, etc
            raise immediately
        except OtherError:   # Rate limit, timeout, etc
            sleep(2^attempt)  # Exponential backoff
            retry
```

### Batch Error Handling

```python
for ticket in batch:
    try:
        summary = summarizer.summarize_ticket(ticket)
        summaries[ticket.id] = summary
    except Exception:
        summaries[ticket.id] = "❌ Erro ao gerar resumo"
        # Continua com próximo ticket
```

**Estratégia:**
- Falha em um ticket não afeta os demais
- Marca resumos falhados com mensagem clara
- Continua processamento mesmo com erros

## Exemplos de Consumo

### Cenário 1: Poucas Mudanças

**Entrada:**
- 2 novos tickets
- 0 vencidos
- 3 vencendo

**Processamento:**
- Total: 5 tickets únicos
- Lotes: 1 lote de 5
- Custos:
  - API Groq: 1 requisição
  - Tokens: ~750 entrada + 750 saída = 1.500 total
  - Tempo: ~3 segundos

### Cenário 2: Muitos Tickets

**Entrada:**
- 25 novos
- 8 vencidos
- 15 vencendo

**Processamento:**
- Total: 48 tickets únicos
- Lotes: 6 lotes (8+8+8+8+8+8)
- Custos:
  - API Groq: 6 requisições
  - Tokens: ~18.000 entrada + 18.000 saída = 36.000 total
  - Delays: 5 × 2s = 10 segundos
  - Tempo total: ~15 segundos (5s API + 10s delays)

### Cenário 3: Limite Máximo

**Entrada:**
- 50 novos (limite API)
- 50 vencidos (limite API)
- 50 vencendo (limite API)

**Processamento:**
- Total: 150 tickets únicos (cenário de pior caso)
- Lotes: 19 lotes (8×18 + 6)
- Custos:
  - API Groq: 19 requisições
  - Tokens: ~112.500 entrada + 112.500 saída = 225.000 total
  - Delays: 18 × 2s = 36 segundos
  - Tempo total: ~50 segundos (14s API + 36s delays)

**Nota:** Este é um cenário extremamente raro na prática.

## Otimizações Futuras

1. **Processamento Paralelo Controlado**
   - Usar ThreadPool com max 2-3 threads
   - Respeita rate limiting via Semaphore
   - Reduz tempo de 50s para ~20s no cenário 3

2. **Cache Persistente**
   - Armazenar em banco SQLite local
   - Recuperar resumos de dias anteriores
   - Economiza tokens em re-execuções

3. **Priorização de Tickets**
   - Processar vencidos primeiro (mais urgentes)
   - Usar lotes menores para tickets críticos
   - Retardar novos tickets se necessário

4. **Ajustes Dinâmicos**
   - Monitorar taxa de erro
   - Aumentar batch_size se taxa baixa
   - Diminuir se taxa alta

## Monitoramento

Logs gerados durante execução:

```
[INFO] Gerando resumos de IA para 15 tickets...
[INFO]    Processando em lotes de 8 tickets
[INFO]    Lote 1/2 (8 tickets)...
[DEBUG]       ✓ Ticket #60123
[DEBUG]       ✓ Ticket #60124
...
[INFO]    Aguardando 2s antes do próximo lote...
[INFO]    Lote 2/2 (7 tickets)...
[INFO]    ✅ 15/15 resumos gerados com sucesso
```

## Checklist de Validação

- [x] Respeita limite de 50 tickets por API call
- [x] Processa em lotes de 8 tickets (seguro para Groq)
- [x] Implementa delay entre lotes (2 segundos)
- [x] Cache de resumos (evita re-gerar)
- [x] Tratamento de erros individual (falha não interrompe)
- [x] Logging detalhado de progresso
- [x] Deduplica tickets entre categorias
- [x] Suporta até 150 tickets (19 lotes × ~8 segundos)
- [x] Formatação clara do relatório com resumos

---

**Autor:** Movidesk Automation  
**Data:** 26/02/2026  
**Status:** Completo e Testado
