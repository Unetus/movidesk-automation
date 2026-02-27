# 🎯 Movidesk Automation - Início Rápido

## O Que Este Sistema Faz?

Monitora automaticamente seus tickets do Movidesk e envia notificações por email com resumos gerados por IA, economizando tempo na triagem de demandas.

## ⚡ Início Ultra-Rápido (5 minutos)

### 1. Instalar Dependências
```bash
install.bat
```

### 2. Configurar Credenciais

Edite o arquivo `.env`:

```env
# Movidesk
MOVIDESK_TOKEN=SEU_TOKEN_AQUI
MOVIDESK_AGENT_EMAIL=seu.email@empresa.com

# Groq AI (gratuito)
GROQ_API_KEY=SEU_KEY_AQUI

# Email
EMAIL_FROM=seu.email@gmail.com
EMAIL_PASSWORD=senha_de_app_16_digitos
EMAIL_TO=seu.email@gmail.com
```

**Onde obter as credenciais?** Veja [SETUP_GUIDE.md](SETUP_GUIDE.md)

### 3. Testar Sistema
```bash
run.bat
```
Escolha a **Opção 3** do menu para testar todas as conexões.

Deve mostrar:
```
✅ Configuration
✅ Movidesk API
✅ Groq AI
✅ Email SMTP
```

### 4. Primeira Consulta
```bash
run.bat
```
Escolha a **Opção 1** do menu para buscar os últimos 5 tickets e receber por e-mail.

---

## 📊 Menu Interativo

Ao executar `run.bat`, você verá um menu com 5 opções:

### 1️⃣ Consultar últimos 5 tickets (execução única)
- **Uso diário recomendado**
- Busca tickets sob demanda
- Envia e-mail e retorna ao menu
- Nenhum polling automático

### 2️⃣ Modo contínuo (polling automático)
- Verifica tickets automaticamente
- A cada 6 minutos (horário comercial)
- A cada 2 minutos (fora do horário)
- Para com Ctrl+C

### 3️⃣ Testar conexões
- Valida SMTP, Movidesk API, Groq
- Execute depois de configurar o `.env`

### 4️⃣ Ver configurações
- Mostra config atual
- Útil para verificar parâmetros

### 5️⃣ Sair

**📘 Guia completo:** [MENU_GUIDE.md](MENU_GUIDE.md)

---

## 🎯 Fluxo Recomendado

### Uso Diário (Recomendado)
```
1. Execute run.bat
2. Escolha Opção 1
3. Verifique seu e-mail
4. Repita quando quiser consultar novamente
```

### Monitoramento Contínuo
```
1. Execute run.bat
2. Escolha Opção 2
3. Deixe rodando durante o expediente
4. Ctrl+C para parar
```

---

## 🎛️ Personalizar Filtros

Edite `config.yaml`:

### Monitorar apenas urgências altas:
```yaml
filters:
  urgencies:
    - "High"
    - "Urgent"
    - "Critical"
```

### Monitorar todos os tickets (não só os seus):
```yaml
filters:
  only_assigned_to_me: false
```

### Alterar intervalo de polling:
```yaml
polling:
  business_hours:
    interval_minutes: 10  # Aumentar para 10 minutos
```

---

## 📧 Exemplo de Email Recebido

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎫 Novo Ticket Movidesk
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Protocolo: #12345
Assunto: Sistema lento após atualização
Cliente: Empresa XYZ
Categoria: Suporte Técnico
Status: Em Atendimento
Urgência: 🔴 Alta
Responsável: Você

🤖 Resumo IA:
Cliente reporta lentidão no sistema após 
atualização recente. Última ação configurou 
logs para análise. Próximo passo: verificar 
consumo de recursos no servidor.

[Ver Ticket no Movidesk]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📂 Arquivos Importantes

| Arquivo | O Que É |
|---------|---------|
| `.env` | **Suas credenciais** (nunca compartilhe!) |
| `config.yaml` | Filtros, intervalos, preferências |
| `logs/automation.log` | Histórico de execução |
| `data/state.json` | Estado (último check, tickets notificados) |

---

## 🔧 Comandos Úteis

```bash
# Instalar/atualizar
install.bat

# Testar conexões
test_system.bat

# Executar sem enviar emails (teste)
test.bat

# Executar em produção
run.bat
```

---

## ⛔ Se Algo Não Funcionar

### 1. Verifique os logs:
```bash
type logs\automation.log
```

### 2. Execute o teste de sistema:
```bash
test_system.bat
```

### 3. Problemas comuns:

**"Invalid token"**
→ Token do Movidesk incorreto no `.env`

**"SMTP authentication failed"**  
→ Use Senha de App do Gmail (não sua senha normal)

**"No tickets found"**  
→ Não há tickets atribuídos a você, ou filtros muito restritivos

**"Rate limit exceeded"**  
→ Normal! Sistema aguarda automaticamente

---

## 🚀 Executar Automaticamente no Windows

1. Abra: **Agendador de Tarefas**
2. Criar Tarefa → Nome: "Movidesk Automation"
3. Disparador: **Ao fazer logon**
4. Ação: Iniciar programa → `D:\movidesk auto\run.bat`
5. Iniciar em: `D:\movidesk auto\`
6. OK

Agora inicia automaticamente quando você faz login!

---

## 📖 Documentação Completa

- [README.md](README.md) - Documentação técnica completa
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Guia de configuração detalhado
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Arquitetura do sistema

---

## 💡 Dicas

✅ **Deixe executando em segundo plano** - consome poucos recursos  
✅ **Verifique os logs diariamente** - para garantir que está funcionando  
✅ **Ajuste os filtros** conforme sua necessidade  
✅ **API Groq é gratuita** - sem custos com IA!  

---

## ❓ FAQ Rápido

**Q: Precisa ficar executando o tempo todo?**  
A: Sim, ou agendar para iniciar automaticamente.

**Q: Consome muitos recursos?**  
A: Não! ~50MB RAM, CPU mínima.

**Q: Tem custo?**  
A: Não! Groq é gratuito, usa seu próprio SMTP.

**Q: Funciona com quantos tickets?**  
A: Ilimitado, respeitando apenas os rate limits da API.

**Q: Posso monitorar vários agentes?**  
A: Sim, ajuste os filtros em `config.yaml`.

**Q: E se meu PC desligar?**  
A: Ao religar, retoma de onde parou (estado salvo em `data/state.json`).

**Q: Posso desativar a IA?**  
A: Sim, em `config.yaml` → `summarization.enabled: false`.

---

## 🎉 Pronto!

Execute `test_system.bat` e depois `run.bat`.

**Dúvidas?** Veja [SETUP_GUIDE.md](SETUP_GUIDE.md) para troubleshooting detalhado.

---

**Bom uso! 🚀**
