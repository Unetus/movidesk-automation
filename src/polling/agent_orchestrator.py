"""Multi-agent report orchestrator for simultaneous agent monitoring."""

from datetime import datetime
from typing import List, Dict, Any
import time

from ..config import get_settings
from ..utils.logger import get_logger
from .daily_report import DailyReportGenerator


class AgentReportOrchestrator:
    """
    Orchestrates report generation for multiple agents simultaneously.
    
    Features:
    - Processes each agent independently
    - Error isolation (one agent failure doesn't block others)
    - Consolidated statistics across all agents
    - Scheduled execution support
    
    Version: 2.0 (Multi-Agent Support)
    """
    
    def __init__(self):
        """Initialize multi-agent orchestrator."""
        self.settings = get_settings()
        self.logger = get_logger()
        
    def generate_reports_for_all_agents(self) -> Dict[str, Any]:
        """
        Generate and send individual reports for all configured agents.
        
        Returns:
            Dictionary with execution statistics:
            - total_agents: Total number of agents processed
            - successful: Number of successful reports
            - failed: Number of failed reports
            - agents_processed: List of agent emails processed
            - agents_failed: List of agent emails that failed
            - execution_time_seconds: Total execution time
            - reports: List of individual report results
        """
        start_time = time.time()
        
        # Get list of agent emails
        agent_emails = self.settings.agent_emails_list
        total_agents = len(agent_emails)
        
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 INICIANDO GERAÇÃO DE RELATÓRIOS MULTI-AGENTE")
        self.logger.info(f"   Total de agentes: {total_agents}")
        self.logger.info(f"   Modo: {'Multi-Agente' if self.settings.is_multi_agent_mode else 'Single-Agente'}")
        self.logger.info("=" * 80)
        
        results = {
            'total_agents': total_agents,
            'successful': 0,
            'failed': 0,
            'agents_processed': [],
            'agents_failed': [],
            'execution_time_seconds': 0,
            'reports': []
        }
        
        # Process each agent independently
        for idx, agent_email in enumerate(agent_emails, 1):
            agent_start = time.time()
            
            self.logger.info("")
            self.logger.info("─" * 80)
            self.logger.info(f"📧 AGENTE {idx}/{total_agents}: {agent_email}")
            self.logger.info("─" * 80)
            
            try:
                # Create dedicated report generator for this agent
                report_gen = DailyReportGenerator(agent_email=agent_email)
                
                # Generate and send report
                report_gen.send_daily_report()
                
                agent_time = time.time() - agent_start
                
                # Record success
                results['successful'] += 1
                results['agents_processed'].append(agent_email)
                results['reports'].append({
                    'agent_email': agent_email,
                    'status': 'success',
                    'execution_time_seconds': agent_time,
                    'error': None
                })
                
                self.logger.info(f"   ✅ Relatório para {agent_email} enviado com sucesso!")
                self.logger.info(f"   ⏱️  Tempo de execução: {agent_time:.1f}s")
                
            except Exception as e:
                agent_time = time.time() - agent_start
                
                # Record failure (but continue with other agents)
                results['failed'] += 1
                results['agents_failed'].append(agent_email)
                results['reports'].append({
                    'agent_email': agent_email,
                    'status': 'failed',
                    'execution_time_seconds': agent_time,
                    'error': str(e)
                })
                
                self.logger.error(f"   ❌ Erro ao processar agente {agent_email}: {e}", exc_info=True)
                self.logger.info(f"   ⏭️  Continuando com próximo agente...")
        
        # Calculate total execution time
        results['execution_time_seconds'] = time.time() - start_time
        
        # Summary
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("📊 RESUMO DA EXECUÇÃO MULTI-AGENTE")
        self.logger.info("=" * 80)
        self.logger.info(f"   Total de agentes processados: {results['total_agents']}")
        self.logger.info(f"   ✅ Sucesso: {results['successful']}")
        self.logger.info(f"   ❌ Falhas: {results['failed']}")
        self.logger.info(f"   ⏱️  Tempo total de execução: {results['execution_time_seconds']:.1f}s")
        
        if results['agents_processed']:
            self.logger.info(f"   📧 Relatórios enviados para: {', '.join(results['agents_processed'])}")
        
        if results['agents_failed']:
            self.logger.warning(f"   ⚠️  Falhas em: {', '.join(results['agents_failed'])}")
        
        self.logger.info("=" * 80)
        
        return results
    
    def get_agent_summary(self, agent_email: str) -> Dict[str, Any]:
        """
        Get statistics summary for a specific agent.
        
        Args:
            agent_email: Email of the agent
        
        Returns:
            Dictionary with agent statistics from database
        """
        from ..database import DatabaseRepository
        
        db = DatabaseRepository()
        
        # Get latest report for agent
        latest_report = db.get_latest_report(agent_email=agent_email)
        
        if not latest_report:
            return {
                'agent_email': agent_email,
                'has_reports': False,
                'message': 'Nenhum relatório encontrado para este agente'
            }
        
        # Get comparison with yesterday
        comparison = db.get_comparison_with_yesterday(agent_email)
        
        # Get trends (last 30 days)
        trends = db.get_trends(agent_email=agent_email, days=30)
        
        return {
            'agent_email': agent_email,
            'has_reports': True,
            'latest_report': {
                'generated_at': latest_report.generated_at,
                'total_new': latest_report.total_new,
                'total_overdue': latest_report.total_overdue,
                'total_expiring': latest_report.total_expiring,
                'total_summarized': latest_report.total_summarized,
                'email_sent': latest_report.email_sent
            },
            'comparison': comparison,
            'trends': trends
        }
