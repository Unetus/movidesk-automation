import unittest
from unittest.mock import patch, MagicMock
from src.polling.agent_orchestrator import AgentReportOrchestrator
from src.polling.daily_report import DailyReportGenerator
from src.config.settings import Settings

class TestMultiAgentReport(unittest.TestCase):
    def setUp(self):
        # Mock settings with multiple agents
        self.mock_settings = Settings(
            AGENTS="agent1@empresa.com;agent2@empresa.com",
            EMAIL_ENABLED=True,
            EMAIL_TO="fallback@empresa.com"
        )

    @patch("src.polling.daily_report.DailyReportGenerator.send_daily_report")
    @patch("src.polling.daily_report.DailyReportGenerator.__init__", return_value=None)
    def test_generate_reports_for_all_agents(self, mock_init, mock_send):
        # Simulate successful report sending for each agent
        mock_send.return_value = True
        orchestrator = AgentReportOrchestrator(settings=self.mock_settings)
        stats = orchestrator.generate_reports_for_all_agents(dry_run=True)
        self.assertEqual(stats["total_agents"], 2)
        self.assertEqual(stats["success_count"], 2)
        self.assertEqual(stats["failure_count"], 0)
        mock_send.assert_any_call(dry_run=True)

    @patch("src.polling.daily_report.DailyReportGenerator.send_daily_report")
    @patch("src.polling.daily_report.DailyReportGenerator.__init__", return_value=None)
    def test_error_isolated_per_agent(self, mock_init, mock_send):
        # Simulate one agent failing
        mock_send.side_effect = [True, Exception("SMTP error")]
        orchestrator = AgentReportOrchestrator(settings=self.mock_settings)
        stats = orchestrator.generate_reports_for_all_agents(dry_run=True)
        self.assertEqual(stats["total_agents"], 2)
        self.assertEqual(stats["success_count"], 1)
        self.assertEqual(stats["failure_count"], 1)

    def test_agent_emails_list_property(self):
        self.assertEqual(self.mock_settings.agent_emails_list, ["agent1@empresa.com", "agent2@empresa.com"])
        self.assertTrue(self.mock_settings.is_multi_agent_mode)

if __name__ == "__main__":
    unittest.main()
