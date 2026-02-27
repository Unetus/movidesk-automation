"""Test script to validate configuration and connectivity."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings, get_config
from src.utils.logger import setup_logger
from src.api import MovideskClient
from src.processing.summarizer import TicketSummarizer
from src.notifications.email_notifier import EmailNotifier


def test_config():
    """Test configuration loading."""
    print("=" * 60)
    print("1. Testing Configuration")
    print("=" * 60)
    
    try:
        settings = get_settings()
        config = get_config()
        
        print("✅ Settings loaded successfully")
        print(f"   - Movidesk URL: {settings.movidesk_base_url}")
        print(f"   - Agent Email: {settings.movidesk_agent_email}")
        print(f"   - Email From: {settings.email_from}")
        print(f"   - Email To: {settings.email_to}")
        
        print("\n✅ Config loaded successfully")
        print(f"   - Business hours interval: {config.polling['business_hours']['interval_minutes']} min")
        print(f"   - Off hours interval: {config.polling['off_hours']['interval_minutes']} min")
        print(f"   - Urgencies filter: {config.filters.get('urgencies', [])}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_movidesk_api():
    """Test Movidesk API connectivity."""
    print("\n" + "=" * 60)
    print("2. Testing Movidesk API Connection")
    print("=" * 60)
    
    try:
        client = MovideskClient()
        
        # Try to fetch just 1 ticket to test connectivity
        print("Attempting to fetch tickets...")
        tickets = client.get_tickets(top=1)
        
        print(f"✅ API connection successful")
        print(f"   - Retrieved {len(tickets)} ticket(s)")
        
        if tickets:
            ticket = tickets[0]
            print(f"   - Sample ticket: #{ticket.protocol} - {ticket.subject}")
        
        client.close()
        return True
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False


def test_groq_api():
    """Test Groq API connectivity."""
    print("\n" + "=" * 60)
    print("3. Testing Groq AI Connection")
    print("=" * 60)
    
    try:
        summarizer = TicketSummarizer()
        
        # Test with simple prompt
        test_prompt = "Este é um teste de conexão com a API Groq."
        print("Attempting to generate test summary...")
        
        response = summarizer._call_groq(test_prompt, max_retries=1)
        
        if response:
            print(f"✅ Groq API connection successful")
            print(f"   - Response: {response[:100]}...")
            return True
        else:
            print(f"❌ Groq API returned empty response")
            return False
    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return False


def test_email():
    """Test email SMTP connectivity."""
    print("\n" + "=" * 60)
    print("4. Testing Email SMTP Connection")
    print("=" * 60)
    
    try:
        notifier = EmailNotifier()
        
        if not notifier.enabled:
            print("⚠️  Email notifications are disabled in config")
            return True
        
        print("Attempting SMTP connection...")
        success = notifier.test_connection()
        
        if success:
            print("✅ SMTP connection successful")
            return True
        else:
            print("❌ SMTP connection failed")
            return False
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n🧪 Movidesk Automation - System Test\n")
    
    # Setup logger
    setup_logger(name="test", level="INFO")
    
    # Run tests
    results = {
        "Configuration": test_config(),
        "Movidesk API": test_movidesk_api(),
        "Groq AI": test_groq_api(),
        "Email SMTP": test_email(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20s} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("  1. Run 'test.bat' to test in dry-run mode")
        print("  2. Run 'run.bat' to start production")
    else:
        print("⚠️  Some tests failed. Please check your configuration.")
        print("\nTroubleshooting:")
        print("  1. Review SETUP_GUIDE.md for configuration instructions")
        print("  2. Verify credentials in .env file")
        print("  3. Check logs/automation.log for detailed errors")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
