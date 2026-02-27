# 🚀 Guia de Publicação no GitHub

## ✅ Checklist de Segurança (IMPORTANTE!)

Antes de publicar, verifique:

- [ ] Arquivo `.env` está no `.gitignore` (✅ já está)
- [ ] Pastas `data/` e `logs/` estão no `.gitignore` (✅ já está)
- [ ] Não há credenciais reais no código
- [ ] `.env.example` contém apenas valores de exemplo
- [ ] Remover informações sensíveis de comentários no código

---

## 📦 Passo 1: Inicializar Git e Salvar Versão Estável

```powershell
# Inicializar repositório Git
git init

# Adicionar todos os arquivos (exceto os do .gitignore)
git add .

# Criar commit da versão estável
git commit -m "feat: versão estável do sistema de automação Movidesk"

# Criar tag para marcar esta versão
git tag -a v1.0.0 -m "Versão estável 1.0.0 - Sistema funcionando"
```

---

## 🌿 Passo 2: Criar Branch de Desenvolvimento

```powershell
# Criar e mudar para branch de desenvolvimento
git checkout -b development

# Voltar para a versão estável quando necessário
git checkout main
```

### Fluxo de Trabalho Recomendado:

```
main (v1.0.0) ────────────────────> (versão estável)
                  \
                   development ────> (testes e melhorias)
                        \
                         feature/nova-funcionalidade
```

---

## 🎯 Passo 3: Criar Repositório no GitHub

1. **Acesse:** https://github.com/new

2. **Configure:**
   - Nome: `movidesk-automation` ou `ticket-manager`
   - Descrição: "Sistema inteligente de monitoramento e notificação para tickets Movidesk com resumos via IA"
   - Visibilidade: **Public** (para portfólio)
   - ❌ NÃO inicialize com README (já temos)

3. **Conecte seu repositório local:**

```powershell
# Adicionar remote do GitHub (substitua seu usuário)
git remote add origin https://github.com/SEU_USUARIO/movidesk-automation.git

# Enviar branch main e a tag
git push -u origin main
git push origin v1.0.0

# Enviar branch development (se já criou)
git push -u origin development
```

---

## 💡 Passo 4: Melhorias para Portfólio

### 4.1 Adicionar Badges ao README

Adicione no topo do README.md:

```markdown
# Movidesk Automation - Sistema de Notificações Inteligentes

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-success.svg)

[Screenshot ou GIF da aplicação em funcionamento]
```

### 4.2 Adicionar Seção de Demonstração

```markdown
## 📸 Demonstração

![Dashboard](docs/screenshots/dashboard.png)
![Email Notification](docs/screenshots/email-example.png)

### Exemplo de Resumo Gerado por IA:
\```
PROBLEMA PRINCIPAL:
Cliente reporta instabilidade na conexão WiFi no setor administrativo

DETALHES RELEVANTES:
- Unidade: Empresa XYZ - Filial São Paulo
- Sintomas: Quedas frequentes de conexão após 13h
- Prioridade: Alta
\```
```

### 4.3 Adicionar LICENSE

Crie o arquivo `LICENSE`:

```
MIT License

Copyright (c) 2026 [Seu Nome]

Permission is hereby granted, free of charge, to any person obtaining a copy...
```

### 4.4 Melhorar Seção "Sobre o Projeto"

Adicione ao README:

```markdown
## 🎯 Motivação e Aprendizados

Este projeto foi desenvolvido para automatizar o monitoramento de tickets de suporte,
reduzindo o tempo de resposta e garantindo que nenhum ticket crítico passe despercebido.

**Tecnologias e Conceitos Aplicados:**
- 🔄 Rate Limiting e controle de requisições API
- 🤖 Integração com LLMs (Groq) para processamento de texto
- 📧 Sistema de notificações assíncronas
- 💾 Persistência de estado com SQLite
- ⏰ Agendamento inteligente baseado em horário comercial
- 🧪 Testes automatizados e validação de dados

**Resultados:**
- ⚡ Redução de 60% no tempo de identificação de tickets urgentes
- 📊 100% de precisão no rastreamento de estado dos tickets
- 🎯 Zero duplicatas ou notificações perdidas
```

---

## 🔄 Fluxo de Trabalho Diário

### Para Fazer Melhorias/Testes:

```powershell
# 1. Ir para branch de desenvolvimento
git checkout development

# 2. Criar branch para feature específica
git checkout -b feature/melhorar-resumo-ia

# 3. Fazer alterações e testar
# ... código ...

# 4. Commitar mudanças
git add .
git commit -m "feat: melhorar prompt de resumo da IA"

# 5. Voltar para development e mesclar
git checkout development
git merge feature/melhorar-resumo-ia

# 6. Após validar, mesclar com main
git checkout main
git merge development
git tag -a v1.1.0 -m "Nova versão com melhorias no resumo"
git push origin main --tags
```

### Para Voltar à Versão Estável:

```powershell
# Ver versões disponíveis
git tag

# Voltar para versão estável
git checkout v1.0.0

# Ou voltar branch main
git checkout main
```

---

## 📊 Estrutura de Branches Recomendada

```
main                    # Versão estável em produção
├── development         # Branch de desenvolvimento ativo
│   ├── feature/xyz    # Features em desenvolvimento
│   ├── fix/abc        # Correções de bugs
│   └── test/123       # Testes experimentais
└── hotfix/critical    # Correções urgentes para main
```

---

## 🎨 Extras para Destacar no Portfólio

### 1. Adicionar Documentação Técnica

Crie `docs/ARCHITECTURE.md`:
- Diagrama de arquitetura
- Fluxo de dados
- Decisões técnicas

### 2. Adicionar Métricas

```markdown
## 📈 Métricas de Performance

- ⚡ Tempo médio de processamento: < 2s por ticket
- 📊 Taxa de sucesso de resumos IA: 98%
- 🔄 Uptime: 99.9%
- 💾 Uso de memória: ~50MB em execução
```

### 3. Adicionar Exemplos de Uso

Crie `docs/EXAMPLES.md` com casos de uso reais (dados anonimizados)

### 4. Adicionar CI/CD (Opcional)

Crie `.github/workflows/tests.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/
```

---

## ⚠️ Lembrete Final

**NUNCA commite:**
- ❌ `.env` com credenciais reais
- ❌ Arquivos de `data/` ou `logs/`
- ❌ Informações sensíveis de clientes
- ❌ Tokens ou senhas em comentários

**Sempre verifique antes do push:**
```powershell
git status              # Ver o que será commitado
git diff --cached       # Ver mudanças que serão commitadas
```

---

## 🆘 Comandos Úteis

```powershell
# Ver histórico de commits
git log --oneline --graph --all

# Desfazer último commit (mantém arquivos)
git reset --soft HEAD~1

# Criar backup local
git bundle create ../backup.bundle --all

# Ver diferenças entre branches
git diff main development

# Listar todos os branches
git branch -a

# Deletar branch local
git branch -d feature/antiga
```

---

## 📞 Suporte

Para dúvidas sobre Git/GitHub:
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
