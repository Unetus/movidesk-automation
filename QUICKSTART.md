# Movidesk Automation

Sistema automatizado de monitoramento e notificação de tickets do Movidesk.

## Instalação Rápida

1. Execute `install.bat`
2. Edite `.env` com suas credenciais
3. Execute `run.bat`

## Documentação Completa

Veja [README.md](README.md) para documentação completa.

## Estrutura

```
movidesk-automation/
├── src/              # Código fonte
├── data/             # Estado persistente
├── logs/             # Logs da aplicação
├── config.yaml       # Configurações
├── .env              # Variáveis de ambiente
├── main.py           # Entry point
├── install.bat       # Instalador Windows
├── run.bat           # Executar aplicação
└── test.bat          # Modo teste (dry-run)
```

## Suporte

Para problemas ou dúvidas, verifique os logs em `logs/automation.log`.
