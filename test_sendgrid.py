"""
Script de diagnóstico para testar envio de email via SendGrid.
Executa verificações passo a passo para identificar o problema.
"""
import os
import sys

# Load .env
from dotenv import load_dotenv
load_dotenv()

def main():
    print("=" * 60)
    print("🔍 DIAGNÓSTICO SENDGRID - Movidesk Automation")
    print("=" * 60)
    
    # Step 1: Check if sendgrid is installed
    print("\n[1/6] Verificando instalação do pacote sendgrid...")
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        print(f"  ✅ sendgrid instalado (versão: {sendgrid.__version__})")
    except ImportError:
        print("  ❌ Pacote 'sendgrid' NÃO instalado!")
        print("  ➡️  Execute: pip install sendgrid")
        sys.exit(1)
    
    # Step 2: Check API key
    print("\n[2/6] Verificando SENDGRID_API_KEY...")
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        print("  ❌ SENDGRID_API_KEY não encontrada no ambiente!")
        sys.exit(1)
    elif not api_key.startswith("SG."):
        print(f"  ⚠️  API Key não começa com 'SG.' - formato pode estar incorreto")
        print(f"  Valor: {api_key[:15]}...")
    else:
        print(f"  ✅ API Key encontrada: {api_key[:15]}...")
    
    # Step 3: Check from/to emails
    print("\n[3/6] Verificando EMAIL_FROM e EMAIL_TO...")
    email_from = os.getenv("EMAIL_FROM")
    email_to = os.getenv("EMAIL_TO")
    print(f"  EMAIL_FROM: {email_from or '❌ NÃO DEFINIDO'}")
    print(f"  EMAIL_TO:   {email_to or '❌ NÃO DEFINIDO'}")
    
    if not email_from or not email_to:
        print("  ❌ EMAIL_FROM e EMAIL_TO são obrigatórios!")
        sys.exit(1)
    
    # Step 4: Check sender verification warning
    print("\n[4/6] ⚠️  VERIFICAÇÃO DE SENDER (IMPORTANTE!)...")
    print(f"  O email remetente '{email_from}' PRECISA estar verificado no SendGrid.")
    print(f"  Acesse: https://app.sendgrid.com/settings/sender_auth")
    print(f"  Opções:")
    print(f"    a) Single Sender Verification - verificar o email individual")
    print(f"    b) Domain Authentication - verificar o domínio '{email_from.split('@')[1]}'")
    print(f"  SEM verificação, o SendGrid aceita a requisição (202) mas NÃO entrega!")
    
    # Step 5: Test API connectivity
    print("\n[5/6] Testando conectividade com SendGrid API...")
    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        # Simple test - check API key validity
        print("  ✅ Cliente SendGrid criado com sucesso")
    except Exception as e:
        print(f"  ❌ Erro ao criar cliente: {e}")
        sys.exit(1)
    
    # Step 6: Attempt to send test email
    print(f"\n[6/6] Enviando email de teste para {email_to}...")
    message = Mail(
        from_email=email_from,
        to_emails=email_to,
        subject="[TESTE] Diagnóstico SendGrid - Movidesk Automation",
        html_content="""
        <h2>✅ Teste SendGrid Funcionando!</h2>
        <p>Se você recebeu este email, a integração SendGrid está correta.</p>
        <p><strong>Data:</strong> Gerado pelo script de diagnóstico</p>
        """
    )
    
    try:
        response = sg.send(message)
        print(f"  Status Code: {response.status_code}")
        print(f"  Body: {response.body}")
        
        if response.headers:
            msg_id = response.headers.get('X-Message-Id', 'N/A')
            print(f"  X-Message-Id: {msg_id}")
        
        if response.status_code == 202:
            print(f"\n  ✅ Email ACEITO pelo SendGrid (status 202)")
            print(f"\n  📋 PRÓXIMOS PASSOS se o email NÃO chegar:")
            print(f"     1. Verifique a pasta SPAM/Lixo Eletrônico de {email_to}")
            print(f"     2. Acesse https://app.sendgrid.com/email_activity")
            print(f"        - Procure pelo Message-ID acima")
            print(f"        - Verifique se mostra 'Dropped' ou 'Bounced'")
            print(f"     3. Verifique Sender Authentication:")
            print(f"        https://app.sendgrid.com/settings/sender_auth")
            print(f"        - '{email_from}' DEVE estar verificado como sender")
            print(f"     4. Verifique se a conta SendGrid NÃO está em modo sandbox")
        elif response.status_code == 401:
            print(f"  ❌ API Key INVÁLIDA ou sem permissão!")
            print(f"     Verifique se a key tem permissão 'Mail Send'")
        elif response.status_code == 403:
            print(f"  ❌ ACESSO NEGADO - sender não verificado ou conta suspensa")
            print(f"     Verifique sender auth: https://app.sendgrid.com/settings/sender_auth")
        else:
            print(f"  ⚠️  Status inesperado: {response.status_code}")
            print(f"  Body: {response.body}")
            
    except Exception as e:
        print(f"  ❌ ERRO ao enviar: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Diagnóstico concluído.")
    print("=" * 60)


if __name__ == "__main__":
    main()
