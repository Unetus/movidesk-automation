# Relatório Diário com Resumos de IA

## Visão Geral

O sistema foi consolidado para utilizar **uma única funcionalidade unificada**: o **Relatório Diário com Resumos de IA**. Esta funcionalidade agrupa todas as informações de tickets relevantes em um único relatório enviado por email, com resumos inteligentes gerados pela IA.

## O que mudou

### Antes
- Três funções separadas:
  - Consulta de últimos 5 tickets
  - Verificação de tickets vencidos
  - Relatório diário (sem IA)
- Menu com múltiplas opções

### Depois
- Uma única funcionalidade: **Relatório Diário Completo com IA**
- Menu simplificado com apenas 4 opções
- Modo padrão: `daily-report` com processamento em lotes

## Características

### Seções do Relatório

O relatório diário inclui **3 seções principais**:

1. **🆕 Novos Tickets (Últimas 24 horas)**
   - Todos os tickets criados no último dia
   - Status, urgência, cliente
   - Data/hora de criação
   - **Resumo de IA para cada ticket**

2. **🔴 Tickets com SLA Vencido**
   - Tickets que já ultrapassaram o prazo
   - Quantos dias vencidos
   - Cliente e status
   - **Resumo de IA para cada ticket**

3. **⚠️ Tickets Vencendo nos Próximos 2 Dias**
   - Tickets em risco nos próximos 2 dias
   - Tempo restante (dias e horas)
   - Cliente e urgência
   - **Resumo de IA para cada ticket**

### Processamento em Lotes (Batch Processing)

Para respeitar os limites da API e dos tokens do Groq:

- **Tamanho de lote**: 8 tickets por vez
- **Atraso entre lotes**: 2 segundos
- **Estratégia**: Processa tickets em paralelo respeitando quotas
- **Cache**: Evita re-gerar resumos para tickets já processados
- **Fallback**: Se houver erro em um resumo, continua com os demais

### Geração de Resumos de IA

Usa a API Groq (llama-3.1-8b-instant):

- **Modelo**: llama-3.1-8b-instant
- **Max tokens**: 150 por resumo
- **Temperatura**: 0.3 (conservador, focado em fatos)
- **Entrada**: Até 3.500 caracteres de conteúdo do ticket
  - Assunto
  - Cliente/Unidade
  - Categoria, urgência, status
  - Últimas 5 interações
  - Histórico de ações

### Fusos Horários

- **Entrada**: API Movidesk retorna em UTC
- **Processamento**: Comparações em UTC (correto)
- **Saída**: Todos os tempos exibidos em **BRT (UTC-3)** para facilitar leitura

## Como Usar

### Via Menu (Recomendado)

```bash
run.bat
```

Escolha a opção **1 - Relatório Diário com IA**

### Via Linha de Comando

```bash
# Modo padrão (daily-report)
python main.py --once

# Explicitamente
python main.py --once --mode daily-report

# Outros modos (legado)
python main.py --once --mode latest      # Últimos tickets
python main.py --once --mode overdue     # Apenas vencidos
```

### Agendamento (Via Tarefa Agendada Windows)

Para executar automaticamente às 8:00 AM (antes do expediente):

```batch
D:\movidesk auto\venv\Scripts\python.exe D:\movidesk auto\main.py --once
```

## Fluxo de Execução

```
1. Iniciar DailyReportGenerator
   │
   ├─ Buscar tickets novos (24h) - Limite: 50 tickets
   ├─ Buscar tickets vencidos - Limite: 50 tickets
   ├─ Buscar tickets vencendo (2 dias) - Limite: 50 tickets
   │
   ├─ Coletar tickets únicos
   │
   ├─ Processar Resumos em Lotes
   │  ├─ Lote 1: 8 tickets → Groq API
   │  ├─ Aguardar 2 segundos
   │  ├─ Lote 2: 8 tickets → Groq API
   │  └─ ... (continuar até fim)
   │
   ├─ Formatar Relatório
   │  ├─ Header com estatísticas
   │  ├─ Seção Novos + IA Summaries
   │  ├─ Seção Vencidos + IA Summaries
   │  └─ Seção Vencendo + IA Summaries
   │
   └─ Enviar por Email
```

## Limites Respeitados

### API Movidesk
- **Máximo por query**: 50 tickets
- **Rate limiting**: Implementado no client
- **Campos otimizados**: Apenas campos necessários

### Groq AI
- **Tokens de entrada**: ~3.500 caracteres por ticket
- **Tokens de saída**: 150 max_tokens por resumo
- **Batch size**: 8 tickets em paralelo
- **Delay**: 2 segundos entre lotes
- **Cache**: Reutiliza resumos (não re-gera)

### Exemplos de Consumo

Com 20 tickets no relatório:
- **Lotes necessários**: 3 (8 + 8 + 4)
- **Tempo estimado**: ~10 segundos (3 lotes × 2s atraso + API)
- **Tokens Groq**: ~3.000 input + 3.000 output = 6.000 total

## Troubleshooting

### Erro: "Insufficient content for ticket"

Significa que o ticket tem muito pouco conteúdo para resumir. O sistema marca como "Resumo não disponível".

### Erro: "Groq API error"

- Verifique a chave da API em `.env`
- Confirme se ainda há quota disponível
- Verifique a conectividade com internet

### Erro: "Could not find field 'slaSolutionDate'"

Significa que o ticket não tem um SLA definido no Movidesk. Normal para alguns tickets.

### Relatório vazio enquanto há tickets

- Verifique se há tickets atribuídos ao agente
- Confirme o email do agente em `.env`
- Verifique se os tickets estão com status "Open" ou similar

## Arquivo de Saída

O relatório é enviado por email com:

- **Formato**: Texto simples com formatação legível
- **Assunto**: `📊 Relatório Diário com IA - X novos | Y vencidos | Z vencendo`
- **Seções**: Organizadas com de separadores visuais
- **Emojis**: Para fácil visualização (opcional)
- **Links**: URLs diretas para cada ticket no Movidesk

## Exemplo de Saída

```
======================================================================
📊 RELATÓRIO DIÁRIO DE TICKETS
======================================================================
Gerado em: 26/02/2026 às 08:15 (Horário de Brasília)
Agente: seu-email@empresa.com
======================================================================

📈 RESUMO GERAL
----------------------------------------------------------------------
   🆕 Novos tickets (últimas 24h): 3
   🔴 Tickets com SLA vencido: 1
   ⚠️  Tickets vencendo (próximos 2 dias): 2
   🤖 Resumos de IA gerados: 6

======================================================================
🆕 NOVOS TICKETS (ÚLTIMAS 24 HORAS)
======================================================================

1. Ticket #60123
   📋 Assunto: Sistema não carrega em alguns navegadores
   👤 Cliente: Cliente XYZ
   📊 Status: Open (New)
   🎯 Urgência: High
   📅 Criado em: 26/02/2026 08:00

   🤖 Resumo IA:
      Usuário relata que o sistema apresenta falhas de carregamento
      em browsers específicos. Afeta funcionalidade de relatórios.
      Requer investigação de compatibilidade de código.

   🔗 https://tickets.movidesk.com/ticket/60123

...
```

## Configuração Avançada

No arquivo `config.yaml`, você pode ajustar:

```yaml
summarization:
  enabled: true                    # Ativar/desativar IA
  model: llama-3.1-8b-instant     # Modelo Groq
  max_tokens: 150                 # Máx tokens por resumo
  temperature: 0.3                # 0=determinístico, 1=criativo
  prompt_template: "..."          # Customizar prompt
```

## Roadmap Futuro

Possíveis melhorias:

- [ ] Notificações push em tempo real
- [ ] Alertas por urgência crítica
- [ ] Customização de seções por usuário
- [ ] Histórico de relatórios (banco de dados)
- [ ] Dashboard web com visualizações
- [ ] Integração com Slack/Teams

---

**Versão**: 2.0  
**Data**: 26 de Fevereiro de 2026  
**Modo**: Produção  
**IA**: Groq llama-3.1-8b-instant
