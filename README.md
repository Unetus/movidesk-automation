# Movidesk Automation - Sistema de Notificações Inteligentes

Automação para monitorar tickets do Movidesk via API, gerar resumos com IA (Groq) e enviar notificações por email.

## 🚀 Características

- ✅ Polling inteligente respeitando rate limits da API Movidesk
- ✅ Filtros avançados: urgência, status, atribuição
- ✅ Resumos automáticos com IA (Groq - gratuito)
- ✅ Notificações por email com templates HTML
- ✅ Agendamento adaptativo (horário comercial vs off-hours)
- ✅ Persistência de estado para evitar duplicatas
- ✅ Logs estruturados com rotação automática

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Conta Movidesk com acesso à API
- API Key do Groq (gratuita em https://console.groq.com)
- Conta de email SMTP (Gmail, Outlook, etc.)

## ⚙️ Instalação

### Windows (via scripts fornecidos)

1. **Clone ou baixe este repositório**

2. **Execute o instalador:**
   ```bash
   install.bat
   ```
   Isso criará um ambiente virtual Python e instalará todas as dependências.

3. **Configure suas credenciais:**
   - Copie `.env.example` para `.env`
   - Preencha suas credenciais:
     - `MOVIDESK_TOKEN`: Token da API do Movidesk
     - `GROQ_API_KEY`: Chave da API Groq
     - `EMAIL_*`: Configurações SMTP do seu email
     - `MOVIDESK_AGENT_EMAIL`: Seu email no Movidesk

4. **Ajuste os filtros (opcional):**
   - Edite `config.yaml` para personalizar:
     - Intervalos de polling
     - Filtros de urgência e status
     - Template de resumo da IA
     - Preferências de notificação

## 🏃 Executando

### Modo Manual
```bash
run.bat
```

### Modo Teste (sem enviar notificações)
```bash
venv\Scripts\activate
python main.py --dry-run
```

### Executar automaticamente no Windows

1. Abra o **Agendador de Tarefas** do Windows
2. Crie uma nova tarefa:
   - **Disparador**: "Ao fazer logon"
   - **Ação**: Iniciar programa
   - **Programa**: `D:\movidesk auto\run.bat` (ajuste o caminho)
   - **Iniciar em**: `D:\movidesk auto\`

## 📁 Estrutura do Projeto

```
movidesk-automation/
├── src/
│   ├── api/              # Cliente API Movidesk
│   ├── polling/          # Motor de polling e estado
│   ├── processing/       # Parser HTML e resumidor IA
│   ├── notifications/    # Sistema de notificação email
│   ├── config/           # Gerenciamento de configuração
│   └── utils/            # Utilitários (logger, rate limiter)
├── data/                 # Estado persistente (criado automaticamente)
├── logs/                 # Logs da aplicação (criado automaticamente)
├── config.yaml           # Configurações principais
├── .env                  # Variáveis de ambiente (criar do .env.example)
├── requirements.txt      # Dependências Python
└── main.py              # Entry point

```

## 🔧 Como Obter as Credenciais

### Token Movidesk
1. Acesse o Movidesk
2. Vá em **Configurações** → **Conta** → **Parâmetros**
3. Aba **Ambiente**
4. Copie o **Token**

### API Key Groq
1. Acesse https://console.groq.com
2. Crie uma conta (gratuita)
3. Vá em **API Keys**
4. Crie uma nova chave

### Email SMTP (Gmail)
1. Ative a verificação em 2 etapas na sua conta Google
2. Vá em https://myaccount.google.com/apppasswords
3. Gere uma senha de app para "Mail"
4. Use essa senha no `.env` (não sua senha normal)

## 📊 Logs e Monitoramento

Os logs são salvos em `logs/automation.log` com informações sobre:
- Tickets encontrados e processados
- Resumos gerados pela IA
- Notificações enviadas
- Erros da API ou rate limiting
- Performance e timing

## 🛠️ Troubleshooting

### Erro: "Rate limit exceeded"
- O sistema respeita os limites automaticamente
- Verifique o `config.yaml` - `interval_minutes` deve ser >= 6 em horário comercial

### Não recebo emails
- Verifique as credenciais SMTP no `.env`
- Teste com outro email de destino
- Verifique se o email não está na pasta de spam
- Para Gmail, confirme que gerou uma "Senha de App"

### IA não gera resumos
- Verifique se `GROQ_API_KEY` está correta
- Teste em https://console.groq.com/playground
- Veja os logs para mensagens de erro da API

## 📝 Licença

Este projeto é de uso pessoal. Adapte conforme necessário.
