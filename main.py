"""
Main application entry point.

TAREFA AGENDADA DO WINDOWS
==========================

Para agendar este script para executar diariamente:

OPÇÃO 1: Via GUI (Mais Fácil)
-----------------------------
1. Abra: Windows + R → taskschd.msc → Enter
2. Clique em "Criar Tarefa Básica"
3. Nome: "Movidesk Relatório Diário"
4. Descrição: "Gera relatório diário com resumo de IA"
5. Gatilho:
   - Iniciar uma tarefa: Diariamente
   - Hora: 08:00:00
   - Recorrência: 1 dia
6. Ação:
   - Programa/script: C:\\Windows\\System32\\python.exe
   - Adicionar argumentos: main.py --once
   - Iniciar em: D:\\movidesk auto
7. Condições:
   - ✓ Acordar o computador para executar a tarefa
8. Configurações:
   - ✓ Não inicie uma nova instância se já estiver em execução
   - Timeout: 1 hora

OPÇÃO 2: Via PowerShell (Como Administrador)
---------------------------------------------
$TaskName = "Movidesk Relatorio Diario"
$Action = New-ScheduledTaskAction -Execute "C:\\Python312\\python.exe" `
  -Argument "main.py --once" -WorkingDirectory "D:\\movidesk auto"
$Trigger = New-ScheduledTaskTrigger -Daily -At 8:00AM
Register-ScheduledTask -TaskName $TaskName -Action $Action `
  -Trigger $Trigger -Description "Relatório diário com resumo de IA"

MONITORAMENTO
-------------
- Agendador de Tarefas → Procure "Movidesk Relatorio Diario"
- Aba "Histórico" para ver execuções anteriores
- Logs em: logs/automation.log

NOTA: Por enquanto usar execução MANUAL via run.bat
"""

import sys
import time
import signal
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import get_settings, get_config
from src.utils.logger import setup_logger, get_logger
from src.polling.poller import TicketPoller


class MovideskAutomation:
    """Main automation application."""
    
    def __init__(self, dry_run: bool = False, run_once: bool = False, mode: str = 'daily-report'):
        """
        Initialize application.
        
        Args:
            dry_run: Run in test mode without sending notifications
            run_once: Execute once and exit (no continuous polling)
            mode: Execution mode - 'daily-report' (default, with AI), 'latest', or 'overdue'
        """
        self.dry_run = dry_run
        self.run_once = run_once
        self.mode = mode
        self.running = False
        self.poller: TicketPoller = None
        self.logger = None
    
    def setup(self) -> bool:
        """
        Setup application components.
        
        Returns:
            True if setup successful
        """
        try:
            # Load config
            config = get_config()
            settings = get_settings()
            
            # Setup logging
            log_config = config.get('logging', {})
            log_level = settings.log_level or log_config.get('level', 'INFO')
            log_file = log_config.get('file', './logs/automation.log')
            
            self.logger = setup_logger(
                name="movidesk_automation",
                level=log_level,
                log_file=log_file,
                use_colors=True
            )
            
            mode_desc = "Single Run" if self.run_once else "Continuous Polling"
            self.logger.info("=" * 60)
            self.logger.info(f"Movidesk Automation - Starting ({mode_desc})")
            self.logger.info("=" * 60)
            
            # Validate configuration
            if not self._validate_config(settings):
                return False
            
            # Initialize poller
            self.poller = TicketPoller(dry_run=self.dry_run)
            
            self.logger.info("✅ Application setup complete")
            return True
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Setup failed: {e}", exc_info=True)
            else:
                print(f"Setup failed: {e}")
            return False
    
    def _validate_config(self, settings) -> bool:
        """Validate configuration."""
        required_fields = [
            ('movidesk_token', 'MOVIDESK_TOKEN'),
            ('groq_api_key', 'GROQ_API_KEY'),
            ('movidesk_agent_email', 'MOVIDESK_AGENT_EMAIL'),
            ('email_from', 'EMAIL_FROM'),
            ('email_password', 'EMAIL_PASSWORD'),
            ('email_to', 'EMAIL_TO'),
        ]
        
        missing = []
        for field, env_name in required_fields:
            if not getattr(settings, field, None):
                missing.append(env_name)
        
        if missing:
            self.logger.error(f"❌ Missing required configuration: {', '.join(missing)}")
            self.logger.error("Please check your .env file")
            return False
        
        return True
    
    def run(self):
        """Run the main polling loop."""
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        if self.run_once:
            self.logger.info("⚡ Single execution mode")
            self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
            
            # Execute based on mode
            if self.mode == 'scheduled-report':
                self.logger.info("📊 Multi-Agent Scheduled Report Mode")
                from src.polling.agent_orchestrator import AgentReportOrchestrator
                orchestrator = AgentReportOrchestrator()
                results = orchestrator.generate_reports_for_all_agents()
                
                # Log summary
                if results['failed'] > 0:
                    self.logger.warning(
                        f"⚠️  Completed with {results['failed']} failure(s) out of {results['total_agents']} agent(s)"
                    )
                    sys.exit(1)  # Non-zero exit for monitoring
                else:
                    self.logger.info(f"✅ All {results['successful']} reports sent successfully")
                    
            elif self.mode == 'daily-report':
                self.logger.info("📊 Generating comprehensive daily report with AI summaries")
                from src.polling.daily_report import DailyReportGenerator
                reporter = DailyReportGenerator()
                reporter.send_daily_report()
            elif self.mode == 'overdue':
                self.logger.info("🔴 Checking overdue tickets")
                self.poller.process_overdue_tickets()
            else:
                self.logger.info("📋 Checking latest tickets")
                self.poller.poll_once()
            
            self.logger.info("✅ Execution completed")
            return
        
        self.logger.info("🚀 Starting polling loop")
        self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        
        # Initial poll
        self.poller.poll_once()
        
        # Main loop
        while self.running:
            try:
                # Get poll interval
                interval = self.poller.get_poll_interval()
                is_business_hours = self.poller.is_business_hours()
                
                self.logger.info(
                    f"⏰ Next poll in {interval // 60} minutes "
                    f"({'business hours' if is_business_hours else 'off hours'})"
                )
                
                # Sleep in small increments to allow for graceful shutdown
                for _ in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                
                if self.running:
                    self.poller.poll_once()
            
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying
        
        self.logger.info("Polling loop stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def shutdown(self):
        """Cleanup and shutdown."""
        self.logger.info("Shutting down...")
        
        if self.poller:
            self.poller.cleanup()
        
        self.logger.info("=" * 60)
        self.logger.info("Movidesk Automation - Stopped")
        self.logger.info("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Movidesk Automation - Ticket monitoring and AI summarization'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Execute once and exit (no continuous polling)'
    )
    parser.add_argument(
        '--mode',
        choices=['daily-report', 'latest', 'overdue'],
        default='daily-report',
        help='Execution mode: daily-report (default, with AI summaries), latest, or overdue'
    )
    parser.add_argument(
        '--scheduled-report',
        action='store_true',
        help='Multi-agent scheduled report mode (sends reports to all configured agents)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in test mode without sending notifications'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Alias for --dry-run'
    )
    
    args = parser.parse_args()
    
    dry_run = args.dry_run or args.test
    run_once = args.once or args.scheduled_report  # scheduled-report implies run_once
    mode = 'scheduled-report' if args.scheduled_report else args.mode
    
    app = MovideskAutomation(dry_run=dry_run, run_once=run_once, mode=mode)
    
    if not app.setup():
        sys.exit(1)
    
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        app.shutdown()


if __name__ == '__main__':
    main()
