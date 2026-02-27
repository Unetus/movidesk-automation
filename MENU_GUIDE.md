# 📋 Guia do Menu Interativo

## 🚀 Como Usar

Execute `run.bat` e você verá o menu principal com as seguintes opções:

## 📑 Opções Disponíveis

### 1️⃣ Consultar últimos 5 tickets (execução única)
- **Uso**: Consulta imediata sob demanda
- **Comportamento**: 
  - Busca os últimos 5 tickets do agente configurado
  - Gera resumos com IA
  - Envia um único e-mail
  - **Retorna ao menu** após conclusão
- **Ideal para**: Quando você quer verificar tickets manualmente

### 2️⃣ Verificar tickets VENCIDOS (overdue)
- **Uso**: Verificação de SLA e tickets atrasados
- **Comportamento**:
  - Busca TODOS os tickets vencidos do agente
  - Ordena por dias de atraso (mais críticos primeiro)
  - Mostra quantos dias após o prazo
  - Gera resumos detalhados com IA
  - Envia e-mail com destaque visual para tickets atrasados
  - **Retorna ao menu** após conclusão
- **Ideal para**: Monitoramento de SLA e priorização de tickets críticos
- **Destaque**: 🔴 Tickets vencidos aparecem com aviso vermelho no e-mail

### 3️⃣ Modo contínuo (polling automático)
- **Uso**: Monitoramento contínuo
- **Comportamento**:
  - Executa consultas automaticamente
  - Intervalo: 6 minutos (horário comercial) / 2 minutos (fora do horário)
  - **Roda até você pressionar Ctrl+C**
- **Ideal para**: Monitoramento durante o expediente

### 4️⃣ Testar conexões
- **Uso**: Validar configurações
- **Testa**:
  - ✅ Conexão SMTP (envio de e-mails)
  - ✅ API Movidesk (acesso aos tickets)
  - ✅ Groq API (geração de resumos)
- **Ideal para**: Após configurar credenciais no `.env`

### 5️⃣ Ver configurações
- **Uso**: Revisar configurações atuais
- **Mostra**:
  - Variáveis do `.env` (credenciais ocultas)
  - Parâmetros principais do `config.yaml`
  - Modelo de IA, intervalos, filtros
- **Ideal para**: Verificar configurações sem abrir arquivos

### 6️⃣ Sair
- Encerra o programa

---

## 🎯 Fluxo Recomendado

### Primeira vez usando:
```
1. Execute install.bat (instalação)
2. Configure o .env com suas credenciais
3. Execute run.bat → Opção 4 (testar conexões)
4. Execute run.bat → Opção 1 (consultar tickets)
```

### Uso diário:
```
1. Execute run.bat
2. Escolha Opção 1 quando quiser consultar tickets
3. Escolha Opção 2 para verificar tickets vencidos (SLA)
4. Repita conforme necessário
```

### Verificação de SLA (Recomendado diariamente):
```
1. Execute run.bat
2. Escolha Opção 2
3. Verifique e-mail com tickets vencidos
4. Priorize atendimento dos tickets mais atrasados
```

### Monitoramento contínuo:
```
1. Execute run.bat
2. Escolha Opção 2
3. Deixe rodando durante seu expediente
4. Pressione Ctrl+C quando quiser parar
```

---

## 💡 Dicas

- **Opção 1** é a mais usada - consulta rápida sob demanda dos últimos tickets
- **Opção 2** é essencial para gestão de SLA - verifique diariamente
- **Opção 3** é útil se você quer receber notificações automáticas durante o expediente
- Use **Opção 4** sempre que mudar credenciais no `.env`
- Use **Opção 5** para confirmar configurações antes de executar

---

## ⚙️ Linha de Comando (Avançado)

Se preferir, você pode executar diretamente via Python:

```bash
# Execução única - últimos 5 tickets (equivalente à Opção 1)
python main.py --once

# Execução única - tickets vencidos (equivalente à Opção 2)
python main.py --once --mode overdue

# Modo contínuo (equivalente à Opção 3)
python main.py

# Teste sem enviar e-mails
python main.py --once --dry-run

# Teste de tickets vencidos sem enviar e-mails
python main.py --once --mode overdue --dry-run

# Teste de conexões (equivalente à Opção 4)
python test_system.py
```

---

## 🔧 Configurações Importantes

### Alterar número de tickets (padrão: 5)
Edite `config.yaml`:
```yaml
filters:
  ticket_limit: 10  # Altere para 10, 20, etc.
```

### Alterar intervalo de polling
Edite `config.yaml`:
```yaml
polling:
  business_hours:
    interval_minutes: 10  # Altere de 6 para 10 minutos
```

### Alterar modelo de IA
Edite `config.yaml`:
```yaml
summarization:
  model: "llama-3.1-8b-instant"  # Ou outro modelo Groq
```

---

## 📧 Resultado

Todos os modos enviam e-mail para o endereço configurado em `.env`:
- **Assunto**: `[Movidesk] N ticket(s) requer(em) atenção`
- **Conteúdo**: Cards com resumo de cada ticket
- **Botão**: Link direto para o ticket no Movidesk

Cada ticket mostra:
- 🎫 Protocolo e assunto
- 👤 Cliente e responsável
- 🎯 Status e urgência
- 🤖 Resumo gerado por IA
- 🔗 Link para abrir no Movidesk
