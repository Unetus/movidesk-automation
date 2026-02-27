# 📁 Estrutura do Projeto

```
movidesk auto/
│
├── 📄 main.py                      # Entry point da aplicação
├── 📄 requirements.txt             # Dependências Python
├── 📄 config.yaml                  # Configurações (filtros, intervalos)
├── 📄 .env.example                 # Template de variáveis de ambiente
├── 📄 .gitignore                   # Arquivos ignorados pelo Git
│
├── 📖 README.md                    # Documentação completa
├── 📖 QUICKSTART.md                # Guia rápido de início
├── 📖 SETUP_GUIDE.md               # Guia detalhado de configuração
│
├── 🔧 install.bat                  # Script de instalação (Windows)
├── 🚀 run.bat                      # Executar em produção
├── 🧪 test.bat                     # Executar em modo dry-run
├── 🧪 test_system.bat              # Testar conexões e configuração
├── 🧪 test_system.py               # Script de testes do sistema
│
├── 📁 src/                         # Código fonte
│   │
│   ├── 📁 api/                     # Cliente API Movidesk
│   │   ├── __init__.py
│   │   ├── client.py               # Cliente HTTP com rate limiting
│   │   └── models.py               # Modelos Pydantic (Ticket, Action, etc)
│   │
│   ├── 📁 config/                  # Gerenciamento de configuração
│   │   ├── __init__.py
│   │   ├── settings.py             # Variáveis de ambiente (.env)
│   │   └── config_loader.py        # Loader YAML (config.yaml)
│   │
│   ├── 📁 notifications/           # Sistema de notificações
│   │   ├── __init__.py
│   │   └── email_notifier.py       # Notificador email SMTP
│   │
│   ├── 📁 polling/                 # Motor de polling
│   │   ├── __init__.py
│   │   ├── poller.py               # Engine principal de polling
│   │   └── state.py                # Gerenciamento de estado (JSON)
│   │
│   ├── 📁 processing/              # Processamento de tickets
│   │   ├── __init__.py
│   │   ├── html_parser.py          # Parser HTML -> texto limpo
│   │   └── summarizer.py           # Integração Groq AI
│   │
│   └── 📁 utils/                   # Utilitários
│       ├── __init__.py
│       ├── logger.py               # Sistema de logs
│       └── rate_limiter.py         # Rate limiter token bucket
│
├── 📁 data/                        # Dados persistentes (criado automaticamente)
│   └── state.json                  # Estado: último poll, tickets notificados
│
├── 📁 logs/                        # Logs da aplicação (criado automaticamente)
│   └── automation.log              # Log rotativo (10MB, 5 backups)
│
└── 📁 venv/                        # Ambiente virtual Python (criado pelo install.bat)
    └── ...
```

## 🎯 Componentes Principais

### 1. **API Client** (`src/api/`)
- Comunicação com API Movidesk via HTTP (httpx)
- Rate limiting inteligente (10 req/min em horário comercial)
- Retry automático com exponential backoff
- Construção de filtros OData
- Modelos Pydantic para validação de dados

### 2. **Polling Engine** (`src/polling/`)
- Polling adaptativo (6 min horário comercial, 2 min fora)
- Detecção de horário comercial via timezone
- Gerenciamento de estado para evitar duplicatas
- Persistência em JSON

### 3. **AI Summarization** (`src/processing/`)
- Integração com Groq (API gratuita)
- Extração de texto de HTML (BeautifulSoup)
- Cache de resumos em memória
- Prompts customizáveis em português
- Tratamento de erros e retry

### 4. **Email Notifications** (`src/notifications/`)
- Templates HTML responsivos
- Modo batch (múltiplos tickets em um email)
- Cores por urgência
- Links diretos para tickets
- Suporte SMTP (Gmail, Outlook, etc)

### 5. **Configuration** (`src/config/`)
- Variáveis de ambiente via `.env`
- Configurações YAML para filtros e comportamento
- Validação de credenciais no startup
- Settings globais thread-safe

### 6. **Utilities** (`src/utils/`)
- Logging estruturado com cores e rotação
- Rate limiter thread-safe token bucket
- Helpers de timezone e datetime

## 📊 Fluxo de Execução

```
┌─────────────┐
│   START     │
│  main.py    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Load Configuration │
│  (.env + config.yaml)│
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Initialize         │
│  - API Client       │
│  - Summarizer       │
│  - Email Notifier   │
│  - State Manager    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Main Poll Loop     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Check Time         │
│  Business Hours?    │
└──────┬──────────────┘
       │
       ├─── Yes ───▶ Wait 6 minutes
       │
       └─── No ────▶ Wait 2 minutes
       │
       ▼
┌─────────────────────┐
│  Fetch Tickets      │
│  (OData filter)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Filter New Tickets │
│  (not in state)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Process Each       │
│  - Parse HTML       │
│  - Generate AI      │
│    Summary (Groq)   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Send Notifications │
│  (Batch or Single)  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Update State       │
│  - Last poll time   │
│  - Notified IDs     │
└──────┬──────────────┘
       │
       ▼
    [LOOP]
```

## 🔒 Segurança

- **Credenciais**: Armazenadas apenas em `.env` (local)
- **Git**: `.env` está no `.gitignore` (não vai pro repositório)
- **Logs**: Não contêm senhas ou tokens
- **Estado**: `state.json` contém apenas IDs de tickets

## 📦 Dependências

| Biblioteca | Versão | Função |
|-----------|--------|--------|
| httpx | 0.27.0 | Cliente HTTP async |
| pydantic | 2.6.1 | Validação de dados |
| pydantic-settings | 2.1.0 | Gerenciamento de .env |
| python-dotenv | 1.0.1 | Carregamento de .env |
| pyyaml | 6.0.1 | Parser YAML |
| apscheduler | 3.10.4 | Agendamento (não usado no MVP) |
| beautifulsoup4 | 4.12.3 | Parser HTML |
| lxml | 5.1.0 | Parser XML/HTML rápido |
| groq | 0.4.2 | Cliente API Groq AI |
| pytz | 2024.1 | Timezone handling |
| colorlog | 6.8.2 | Logs coloridos |

**Total instalado**: ~50MB  
**Uso de RAM**: ~30-50MB durante execução  
**Uso de CPU**: Mínimo (apenas durante polling)

## 🧪 Testes

### Nível 1: Testes de Sistema
```bash
test_system.bat
```
Testa:
- ✅ Carregamento de configuração
- ✅ Conexão API Movidesk
- ✅ Conexão Groq AI
- ✅ Conexão SMTP

### Nível 2: Dry Run
```bash
test.bat
```
Executa polling real mas **não envia emails**.

### Nível 3: Produção
```bash
run.bat
```
Execução completa com emails reais.

## 📈 Métricas e Logs

### Logs Disponíveis

**Console** (colorido):
- INFO: Operações normais
- WARNING: Avisos (rate limit, etc)
- ERROR: Erros recuperáveis
- CRITICAL: Erros fatais

**Arquivo** (`logs/automation.log`):
- Todos os níveis
- Rotação automática (10MB)
- 5 backups mantidos
- Formato: `timestamp - name - level - function:line - message`

### Informações Logadas

- Tickets encontrados e processados
- Resumos gerados
- Notificações enviadas
- Erros de API
- Rate limiting
- Tempo de execução

## 🚀 Deploy

### Local (Windows)
1. Executar via `run.bat`
2. Adicionar ao Agendador de Tarefas

### Servidor Windows
1. Mesmos passos
2. Configurar como Serviço Windows (opcional)

### Docker (futuro)
```yaml
# docker-compose.yml
services:
  movidesk-automation:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

## 📝 Manutenção

### Diária
- [ ] Verificar logs para erros
- [ ] Confirmar notificações recebidas

### Semanal
- [ ] Revisar quantidade de tickets processados
- [ ] Limpar logs antigos (automático)

### Mensal
- [ ] Atualizar dependências: `pip install --upgrade -r requirements.txt`
- [ ] Revisar filtros em `config.yaml`
- [ ] Verificar uso de API Groq (gratuito)

## 🆘 Troubleshooting Rápido

| Problema | Solução |
|---------|---------|
| "Import could not be resolved" | Execute `install.bat` |
| "Invalid token" | Verifique `MOVIDESK_TOKEN` no `.env` |
| "SMTP authentication failed" | Use Senha de App (Gmail) |
| "Rate limit exceeded" | Normal! Sistema aguarda automaticamente |
| "No tickets found" | Verifique filtros em `config.yaml` |
| Emails não chegam | Verifique spam, credenciais SMTP |

## 🎓 Próximos Passos (Futuro)

- [ ] Dashboard web (FastAPI + React)
- [ ] Telegram bot integration
- [ ] PostgreSQL para histórico completo
- [ ] Analytics e métricas (Grafana)
- [ ] Auto-resposta sugerida por IA
- [ ] Webhooks (se Movidesk adicionar suporte)
- [ ] Multi-tenancy (múltiplas contas)
- [ ] Deploy Docker/Kubernetes

---

**Versão**: 1.0.0  
**Python**: 3.10+  
**Plataforma**: Windows (adaptável para Linux/Mac)  
**Licença**: Uso pessoal
