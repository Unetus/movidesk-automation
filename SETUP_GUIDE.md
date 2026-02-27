# 🔧 Guia de Configuração - Movidesk Automation

## 📋 Checklist de Configuração

### 1️⃣ Obter Token do Movidesk

1. Acesse sua conta do Movidesk
2. Vá em **Configurações** (ícone de engrenagem)
3. Clique em **Conta** no menu lateral
4. Selecione **Parâmetros**
5. Vá na aba **Ambiente**
6. Copie o **Token** exibido
7. Cole no arquivo `.env` na linha `MOVIDESK_TOKEN=`

**Exemplo:**
```
MOVIDESK_TOKEN=X7h9K2m4P8qW3eR5tY6uI1oP9aS0dF2gH4jK6lZ8xC1vB3nM5
```

---

### 2️⃣ Obter API Key do Groq (Gratuita)

1. Acesse https://console.groq.com
2. Crie uma conta (pode usar Google/GitHub)
3. Vá em **API Keys** no menu lateral
4. Clique em **Create API Key**
5. Dê um nome (ex: "Movidesk Automation")
6. Copie a chave gerada
7. Cole no arquivo `.env` na linha `GROQ_API_KEY=`

**Exemplo:**
```
GROQ_API_KEY=gsk_abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx
```

⚠️ **Importante**: A API do Groq é **totalmente gratuita** e não requer cartão de crédito!

---

### 3️⃣ Configurar Email (Gmail)

#### Opção A: Gmail com Senha de App (Recomendado)

1. Ative a **Verificação em 2 etapas** na sua conta Google:
   - Acesse https://myaccount.google.com/security
   - Procure por "Verificação em duas etapas"
   - Ative se ainda não estiver ativo

2. Gere uma **Senha de App**:
   - Acesse https://myaccount.google.com/apppasswords
   - Selecione "Email" e "Computador Windows"
   - Clique em "Gerar"
   - Copie a senha de 16 caracteres (ex: `abcd efgh ijkl mnop`)

3. Configure no `.env`:
   ```
   EMAIL_FROM=seu_email@gmail.com
   EMAIL_PASSWORD=abcdefghijklmnop  (sem espaços)
   EMAIL_TO=seu_email@gmail.com
   ```

#### Opção B: Outlook/Hotmail

```
EMAIL_SMTP_SERVER=smtp-mail.outlook.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=seu_email@outlook.com
EMAIL_PASSWORD=sua_senha_normal
EMAIL_TO=destinatario@example.com
```

#### Opção C: Outros Provedores

**Yahoo:**
```
EMAIL_SMTP_SERVER=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587
```

**ProtonMail:**
```
EMAIL_SMTP_SERVER=smtp.protonmail.com
EMAIL_SMTP_PORT=587
```

---

### 4️⃣ Configurar Seu Agente no Movidesk

No arquivo `.env`, configure o email do agente (seu usuário no Movidesk):

```
MOVIDESK_AGENT_EMAIL=seu.nome@empresa.com
```

Isso filtrará apenas os tickets **atribuídos a você**.

---

## ⚙️ Personalizar Filtros (config.yaml)

### Filtrar por Urgência

Edite `config.yaml`:

```yaml
filters:
  urgencies:
    - "High"      # Alta
    - "Urgent"    # Urgente
    - "Critical"  # Crítica
```

Opções disponíveis:
- `Low` - Baixa
- `Medium` - Média
- `High` - Alta
- `Urgent` - Urgente
- `Critical` - Crítica

### Filtrar por Status

```yaml
filters:
  statuses:
    - "New"          # Novo
    - "InAttendance" # Em Atendimento
    - "Stopped"      # Parado
```

Para monitorar **todos** os status, deixe a lista vazia:
```yaml
filters:
  statuses: []
```

### Monitorar TODOS os Tickets (não apenas os seus)

```yaml
filters:
  only_assigned_to_me: false
```

---

## 🧪 Testar a Configuração

### Teste 1: Instalação

```bash
install.bat
```

Deve completar sem erros e criar o ambiente virtual `venv/`.

### Teste 2: Validar Credenciais

```bash
test.bat
```

Este modo **NÃO envia emails**, apenas testa a conexão com a API e mostra os tickets encontrados.

**O que observar:**
- ✅ Deve conectar com sucesso à API do Movidesk
- ✅ Deve listar tickets encontrados (se houver)
- ✅ Deve gerar resumos com a IA Groq
- ❌ **NÃO** deve enviar emails

### Teste 3: Produção

Quando estiver tudo ok:

```bash
run.bat
```

Agora **enviará emails reais** para cada ticket novo/atualizado.

---

## 🔍 Verificar Logs

Os logs são salvos em `logs/automation.log`:

```bash
type logs\automation.log
```

**Exemplo de log bem-sucedido:**
```
2026-02-26 14:30:15 - movidesk_automation - INFO - === Starting polling cycle ===
2026-02-26 14:30:16 - movidesk_automation - INFO - Retrieved 3 tickets
2026-02-26 14:30:16 - movidesk_automation - INFO - 2 new ticket(s) to process
2026-02-26 14:30:18 - movidesk_automation - INFO - Generated summary for ticket abc123
2026-02-26 14:30:20 - movidesk_automation - INFO - Sent batch notification for 2 tickets
```

---

## ❓ Problemas Comuns

### Erro: "Invalid token"

- Verifique se copiou o token completo do Movidesk
- Não deve ter espaços antes/depois
- Token começa geralmente com letras e números misturados

### Erro: "SMTP authentication failed"

- **Gmail**: Certifique-se de usar **Senha de App**, não sua senha normal
- Verifique se a verificação em 2 etapas está ativa
- Para outros: verifique se o servidor SMTP e porta estão corretos

### Erro: "Groq API error"

- Verifique se a chave está correta
- Teste visitando https://console.groq.com/playground
- A chave deve começar com `gsk_`

### Não encontra tickets

- Verifique o filtro `MOVIDESK_AGENT_EMAIL` no `.env`
- Confirme que existem tickets atribuídos a você
- Tente ampliar os filtros em `config.yaml` (mais urgências, mais status)
- Execute com `--dry-run` e veja os logs detalhados

### Rate limit atingido

Se ver mensagens como "Rate limit exceeded":

- Durante o expediente: O sistema automaticamente respeita o limite de 10 req/min
- O polling é configurado para 6 minutos no horário comercial justamente para evitar isso
- Verifique em `config.yaml` se `interval_minutes` está >= 6

---

## 🚀 Executar Automaticamente

### Windows - Agendador de Tarefas

1. Abra **Agendador de Tarefas** (Task Scheduler)
2. Clique em **Criar Tarefa Básica**
3. Nome: "Movidesk Automation"
4. Disparador: **Ao fazer logon**
5. Ação: **Iniciar um programa**
   - Programa: `D:\movidesk auto\run.bat` (ajuste o caminho)
   - Iniciar em: `D:\movidesk auto\`
6. Marque: **Executar com privilégios mais altos** (opcional)
7. Finalizar

Agora o sistema iniciará automaticamente quando você fizer login no Windows.

### Parar a Automação

- Se executando em uma janela: pressione `Ctrl+C`
- Se executando em segundo plano: feche a janela ou use o Gerenciador de Tarefas

---

## 📊 Monitoramento

Recomendações:

1. **Logs**: Verifique `logs/automation.log` diariamente
2. **Espaço**: Os logs rotacionam automaticamente (máx 10MB)
3. **Estado**: O arquivo `data/state.json` armazena qual foi a última verificação
4. **Performance**: O sistema usa ~50MB RAM em média

---

## 🔒 Segurança

⚠️ **Importante:**

- **NUNCA** compartilhe seu arquivo `.env`
- **NUNCA** comite `.env` no Git (já está no `.gitignore`)
- As credenciais são armazenadas apenas localmente
- Revogue tokens/senhas se o computador for comprometido

---

## 📞 Suporte

Se tiver problemas:

1. Verifique os **logs** em `logs/automation.log`
2. Execute em modo teste: `test.bat`
3. Revise este guia
4. Verifique se todas as bibliotecas foram instaladas: `pip list`

**Logs importantes para debug:**
- Conexões com API
- Erros de autenticação
- Tickets encontrados/processados
- Notificações enviadas

---

## ✅ Checklist Final

Antes de colocar em produção, confirme:

- [ ] `install.bat` executado com sucesso
- [ ] Arquivo `.env` configurado com todas as credenciais
- [ ] `test.bat` executado e encontrou tickets
- [ ] Resumos IA sendo gerados corretamente
- [ ] `config.yaml` ajustado com os filtros desejados
- [ ] Teste de email enviado com sucesso
- [ ] Logs sendo gerados em `logs/automation.log`

**Está tudo pronto! Execute `run.bat` e monitore os primeiros minutos.**
