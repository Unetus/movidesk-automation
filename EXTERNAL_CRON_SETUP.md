# Configuração de Cron Externo

Como GitHub Actions não está disponível, usaremos um **serviço externo gratuito de cron** para chamar o Railway.

## 🚀 Como funciona:

1. **Railway** roda um servidor web (`server.py`) 24/7
2. **Serviço de cron** (EasyCron) chama o endpoint `/trigger` às 08:00 BRT
3. **Servidor** executa os relatórios para os 6 agentes
4. **Emails** são enviados via SendGrid

## 📝 Passos de configuração:

### 1️⃣ Configure no Railway:

1. Adicione a variável de ambiente:
   ```
   TRIGGER_TOKEN=seu-token-secreto-aqui-12345
   ```
   ⚠️ **Importante**: Crie um token aleatório forte (mínimo 32 caracteres)

2. Faça deploy do código atualizado (já está no git)

3. Anote a **URL do Railway**, exemplo:
   ```
   https://movidesk-automation-production.up.railway.app
   ```

### 2️⃣ Configure o EasyCron (gratuito):

1. Acesse: https://www.easycron.com/user/register
2. Crie uma conta gratuita
3. Clique em **"Create Cron Job"**
4. Configure:
   - **URL**: `https://SUA-URL-RAILWAY.railway.app/trigger`
   - **Name**: `Movidesk Daily Report`
   - **Cron Expression**: `0 11 * * 1-5` (08:00 BRT = 11:00 UTC, Seg-Sex)
   - **HTTP Method**: `POST`
   - **HTTP Headers**: Clique em "Add Header"
     - Header: `Authorization`
     - Value: `Bearer seu-token-secreto-aqui-12345`
   - **Timezone**: `UTC` (já ajustado no cron expression)
5. Clique em **"Create"**

### 3️⃣ Teste manual:

Você pode testar imediatamente via comando ou navegador:

**Via curl (PowerShell):**
```powershell
$headers = @{
    "Authorization" = "Bearer seu-token-secreto-aqui-12345"
}

Invoke-RestMethod -Uri "https://SUA-URL-RAILWAY.railway.app/trigger" -Method POST -Headers $headers
```

**Resposta esperada:**
```json
{
  "status": "success",
  "message": "Reports sent to all agents"
}
```

## 🔍 Monitoramento:

- **EasyCron Dashboard**: Ver histórico de execuções e logs
- **Railway Logs**: Ver saída do servidor e envio de emails
- **SendGrid Dashboard**: Confirmar emails entregues

## 🆓 Alternativas gratuitas ao EasyCron:

1. **cron-job.org**: https://cron-job.org (80 jobs gratuitos)
2. **UptimeRobot**: https://uptimerobot.com (monitora e pode trigger)
3. **GitHub Actions de outro repo pessoal** (se você tiver um repo pessoal com Actions habilitado)

## ✅ Agentes configurados:

Os 6 agentes receberão relatórios diariamente:
1. matheus.pereira@wifire.me
2. willian.herdy@wifire.me
3. wellington.branco@wifire.me
4. thiago.henrique@wifire.me
5. paulo.lopes@wifire.me
6. matheus.oliveira@wifire.me

## 🔒 Segurança:

- Sempre use um token aleatório forte
- Nunca compartilhe o token publicamente
- Railway só aceita requisições com token válido
- Endpoint `/health` é público (para health checks)
