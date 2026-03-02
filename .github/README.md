# GitHub Actions - Daily Report Automation

## ⏰ Agendamento

O relatório diário é executado automaticamente via GitHub Actions:
- **Horário**: 08:45 BRT (Segunda a Sexta-feira)
- **Timezone**: America/Sao_Paulo (GMT-3)
- **Arquivo de configuração**: `.github/workflows/daily-report.yml`

## 🔐 Configuração de Secrets

Para o workflow funcionar, você precisa configurar os seguintes **Repository Secrets**:

### Como adicionar secrets:
1. Vá para o repositório no GitHub
2. Clique em **Settings** → **Secrets and variables** → **Actions**
3. Clique em **New repository secret**
4. Adicione cada secret abaixo:

### Secrets necessários:

| Secret Name | Descrição | Exemplo |
|-------------|-----------|---------|
| `MOVIDESK_TOKEN` | Token de API do Movidesk | `8016392a-75de-4bbb-842e-36653ec34b36` |
| `MOVIDESK_BASE_URL` | URL base da API Movidesk | `https://api.movidesk.com/public/v1` |
| `GROQ_API_KEY` | API Key do Groq (IA) | `gsk_JZ0t...VdXv` |
| `SENDGRID_API_KEY` | API Key do SendGrid (email) | `SG.GGy...Xn3kw` |
| `AGENTS` | Emails dos agentes (separados por `;`) | `matheus.pereira@wifire.me;willian.herdy@wifire.me;wellington.branco@wifire.me` |
| `EMAIL_FROM` | Email remetente verificado no SendGrid | `matheus.pereira@wifire.me` |

## ✅ Verificação

Após configurar os secrets:
1. Vá para **Actions** no repositório
2. Selecione o workflow **Daily Report Cron**
3. Clique em **Run workflow** para testar manualmente
4. Verifique os logs de execução

## 📊 Agentes configurados

Atualmente 3 agentes recebem relatórios individuais:
- matheus.pereira@wifire.me
- willian.herdy@wifire.me
- wellington.branco@wifire.me

## 🐛 Debug

Os logs de execução ficam disponíveis:
- **GitHub**: Na aba Actions, clique na execução específica
- **Artifact**: Se houver falha, logs são salvos como artifact por 7 dias
