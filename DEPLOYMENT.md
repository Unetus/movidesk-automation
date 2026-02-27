# 🚀 Guia de Deploy no Railway - Multi-Agent Mode

Este guia explica como fazer deploy do sistema de automação Movidesk no Railway para executar relatórios agendados para múltiplos agentes.

---

## 📋 Pré-requisitos

1. **Conta no Railway**
   - Criar conta em: https://railway.app
   - Conectar com GitHub (recomendado)
   - Free tier: 500h/mês (suficiente para este projeto)

2. **Repositório no GitHub**
   - Código já deve estar no GitHub (público ou privado)
   - Railway vai fazer deploy direto do repo

3. **Credenciais Necessárias**
   - Token da API Movidesk
   - API Key do Groq
   - Credenciais SMTP (Gmail recomendado)
   - Lista de emails dos agentes

---

## 🎯 Passo a Passo - Deploy Inicial

### 1. Criar Novo Projeto no Railway

1. Acesse: https://railway.app/new
2. Clique em **"Deploy from GitHub repo"**
3. Selecione seu repositório: `movidesk-automation`
4. Railway detectará automaticamente que é um projeto Python

### 2. Configurar Variáveis de Ambiente

No Railway Dashboard:
1. Vá em **Settings → Variables**
2. Clique em **"+ New Variable"**
3. Adicione todas as variáveis abaixo:

#### Variáveis Obrigatórias:

```bash
# Movidesk API
MOVIDESK_TOKEN=seu_token_movidesk_aqui
MOVIDESK_BASE_URL=https://api.movidesk.com/public/v1

# Multi-Agent Configuration (SEPARAR POR PONTO-E-VÍRGULA)
AGENTS=agente1@empresa.com;agente2@empresa.com;agente3@empresa.com

# Groq AI
GROQ_API_KEY=sua_chave_groq_aqui

# Email SMTP
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_app_gmail
EMAIL_TO=fallback@empresa.com

# Logging
LOG_LEVEL=INFO
```

**⚠️ IMPORTANTE:** 
- Use **senhas de aplicativo** do Gmail (não senha normal)
- Gerar em: https://myaccount.google.com/apppasswords
- Separe emails dos agentes com `;` (ponto-e-vírgula)

### 3. Configurar Tipo de Serviço

1. Em **Settings → Service**
2. **Service Type:** Cron Job
3. **Start Command:** `python main.py --scheduled-report`
4. **Restart Policy Type:** Never (é um cron, não precisa reiniciar)

### 4. Configurar Agendamento Cron

Railway ainda está desenvolvendo suporte nativo a cron. **Opções disponíveis:**

#### Opção A: GitHub Actions (Recomendado)

Criar arquivo `.github/workflows/scheduled-report.yml`:

```yaml
name: Scheduled Multi-Agent Report

on:
  schedule:
    # Runs at 08:00 AM BRT (11:00 UTC) Monday-Friday
    - cron: '0 11 * * 1-5'
  workflow_dispatch:  # Allow manual trigger

jobs:
  run-report:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Railway Deployment
        run: |
          curl -X POST https://backboard.railway.app/graphql/v2 \
            -H "Authorization: Bearer ${{ secrets.RAILWAY_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"query":"mutation { triggerDeploy(projectId: \"${{ secrets.RAILWAY_PROJECT_ID }}\") { id } }"}'
```

Configurar secrets no GitHub:
- `RAILWAY_TOKEN`: Token da API Railway
- `RAILWAY_PROJECT_ID`: ID do projeto Railway

#### Opção B: Cron-job.org (Externo)

1. Criar conta em: https://cron-job.org
2. Criar novo cron job:
   - **URL:** Endpoint webhook do Railway (criar um endpoint simples)
   - **Schedule:** `0 8 * * 1-5` (seg-sex às 08h)
   - **Timezone:** America/Sao_Paulo

#### Opção C: Railway Scheduled Deployments (Beta)

Em Railway Dashboard:
1. **Settings → Deployments**
2. **Schedule:** `0 8 * * 1-5`
3. **Timezone:** America/Sao_Paulo

### 5. Adicionar Volume Persistente (SQLite)

Para manter o banco de dados entre execuções:

1. **Settings → Volumes**
2. **+ New Volume**
3. **Mount Path:** `/app/data`
4. **Size:** 1GB (mais que suficiente)

Isso garante que:
- Cache de resumos IA persiste
- Histórico de relatórios mantido
- Estado multi-agente preservado

### 6. Deploy

1. Clique em **"Deploy"** ou faça push no GitHub
2. Railway fará build e deploy automático
3. Aguarde conclusão (~2-3 minutos)

---

## ✅ Verificação Pós-Deploy

### 1. Verificar Logs

Em **Deployments → Latest → Logs**:

```
✅ Buscar por:
- "Multi-Agent Scheduled Report Mode"
- "Total de agentes: X"
- "Relatório para agente@email.com enviado com sucesso"
- "Execution completed"

❌ Erros comuns:
- "No agent emails configured" → Verificar variável AGENTS
- "SMTP authentication failed" → Senha de app incorreta
- "API request failed" → Token Movidesk inválido
```

### 2. Testar Manualmente

Trigger manual via Railway CLI:

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link ao projeto
railway link

# Executar comando manualmente
railway run python main.py --scheduled-report --dry-run
```

### 3. Verificar Emails

- Cada agente deve receber relatório no próprio email
- Subject: "Relatório Diário - Tickets do dia (DD/MM/YYYY)"
- Formato HTML com resumos IA

---

## 🔧 Manutenção

### Adicionar/Remover Agentes

1. **Settings → Variables**
2. Editar variável `AGENTS`
3. Formato: `email1@;email2@;email3@`
4. Railway redeploy automático

### Ver Estatísticas por Agente

Acessar banco SQLite remotamente:

```bash
# Via Railway CLI
railway run python -c "
from src.database import DatabaseRepository
from src.polling.agent_orchestrator import AgentReportOrchestrator

orch = AgentReportOrchestrator()
summary = orch.get_agent_summary('agente@email.com')
print(summary)
"
```

### Mudar Horário do Cron

Editar expressão cron no GitHub Actions ou cron-job.org:

```
Formato: minuto hora dia mês dia-da-semana
Exemplos:
- 0 8 * * 1-5   # 08h seg-sex
- 0 9 * * *     # 09h todo dia
- 0 8,14 * * *  # 08h e 14h todo dia
- 30 7 * * 1-5  # 07:30 seg-sex
```

**Timezone:** Lembre de ajustar para UTC se necessário
- BRT (UTC-3): 08:00 BRT = 11:00 UTC

### Backup do Banco de Dados

```bash
# Download do volume
railway run cat /app/data/tickets.db > backup.db

# Upload manual (se necessário)
railway run "cat > /app/data/tickets.db" < backup.db
```

---

## 🐛 Troubleshooting

### Erro: "No module named 'src'"

**Solução:** Verificar que `sys.path.insert` está em `main.py`

### Erro: "Permission denied: data/tickets.db"

**Solução:** Volume não montado corretamente
1. **Settings → Volumes** → Verificar mount path `/app/data`
2. Redeployar

### Erro: "SMTP authentication failed"

**Soluções:**
1. Usar senha de aplicativo Gmail (não senha normal)
2. Verificar 2FA habilitado no Gmail
3. Testar com outro provedor SMTP (Outlook, SendGrid)

### Erro: "Agent email must be provided"

**Solução:** Variável `AGENTS` não configurada ou formato incorreto
- Correto: `email1@dominio.com;email2@dominio.com`
- Incorreto: `email1@dominio.com, email2@dominio.com` (vírgula)

### Relatórios não chegam no horário

**Checklist:**
1. Cron configurado no timezone correto? (America/Sao_Paulo)
2. Logs mostram execução? (Railway → Logs)
3. Emails em spam? (Verificar caixa de spam)
4. EMAIL_ENABLED=true? (Verificar variáveis)

---

## 💰 Custos Railway

**Free Tier (Hobby Plan):**
- 500 horas/mês de execução
- $5 de crédito/mês
- Mais que suficiente para cron jobs diários

**Estimativa para este projeto:**
- Execução: ~2-5 minutos/dia
- Total mensal: ~150 minutos = 2.5 horas
- **Custo: $0** (dentro do free tier)

**Upgrade (se necessário):**
- Developer Plan: $5/mês
- Execuções ilimitadas

---

## 🔐 Segurança

### Boas Práticas:

1. **Nunca commitar .env**
   - Usar variáveis de ambiente Railway
   - .env apenas local

2. **Rotacionar senhas regularmente**
   - Tokens API
   - Senhas SMTP

3. **Monitorar logs**
   - Verificar acessos não autorizados
   - Revisar erros de autenticação

4. **Limitar permissões**
   - Token Movidesk com permissões mínimas
   - Senha Gmail específica para aplicativo

---

## 📊 Monitoramento

### Métricas Importantes:

1. **Taxa de Sucesso**
   - % de relatórios enviados com sucesso
   - Meta: > 98%

2. **Tempo de Execução**
   - Tempo médio por relatório
   - Meta: < 2 minutos por agente

3. **Uso de Cache IA**
   - % de resumos em cache vs novos
   - Meta: > 60% (economia de tokens)

### Dashboard Sugerido:

Railway não tem dashboard nativo, mas pode integrar com:
- **Sentry:** Rastreamento de erros
- **Datadog:** Métricas e logs
- **UptimeRobot:** Monitoramento de disponibilidade

---

## 🆘 Suporte

### Documentação Railway:
- https://docs.railway.app
- https://railway.app/help

### Logs Úteis:
```bash
# Ver últimas 100 linhas de log
railway logs --tail 100

# Filtrar erros
railway logs | grep ERROR

# Seguir logs em tempo real
railway logs --follow
```

### Contato Railway:
- Discord: https://discord.gg/railway
- Twitter: @Railway
- Email: team@railway.app

---

## ✨ Próximos Passos

Após deploy bem-sucedido:

1. ✅ Monitorar primeira execução agendada
2. ✅ Validar recebimento de emails por todos os agentes
3. ✅ Configurar alertas para falhas
4. ✅ Documentar procedimentos para time
5. ✅ Considerar dashboard de métricas (opcional)

---

**Última atualização:** 27/02/2026
**Versão:** 2.0 (Multi-Agent Support)
