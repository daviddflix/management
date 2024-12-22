from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from app.utils.templates import (
    SPRINT_REPORT_TEMPLATE,
    KPI_REPORT_TEMPLATE,
    PROGRESS_REPORT_TEMPLATE
)
from app.services.monday_service import MondayService
from app.services.slack_service import SlackService
from app.services.redis_service import RedisService
from app.utils.metrics import (
    calculate_team_metrics,
    calculate_sprint_metrics,
    calculate_task_metrics,
    generate_metrics_report
)
from app.utils.metric_alerts import MetricAlertManager
from app.utils.metric_visualizations import MetricVisualizer
from app.core.config import settings
from app.models.metrics import MetricType, QualityMetrics, PerformanceMetrics
from app.models.sprint import SprintStatus

class TeamLeadAgent(BaseAgent):
    def __init__(
        self,
        monday_service: MondayService,
        slack_service: SlackService,
        redis_service: RedisService
    ):
        super().__init__(
            name="Team Lead Agent",
            description="AI Team Lead responsible for sprint management and team coordination"
        )
        self.monday_service = monday_service
        self.slack_service = slack_service
        self.redis_service = redis_service
        self.metric_alerts = MetricAlertManager(slack_service)
        self.metric_visualizer = MetricVisualizer()

    def _setup_assistant(self):
        """Setup the OpenAI assistant with team lead specific tools"""
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_sprint_progress",
                    "description": "Analyze sprint progress and generate insights",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sprint_data": {
                                "type": "object",
                                "description": "Sprint data including tasks and metrics"
                            },
                            "team_data": {
                                "type": "object",
                                "description": "Team performance data"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_sprint_report",
                    "description": "Generate detailed sprint report",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sprint_data": {"type": "object"},
                            "metrics": {"type": "object"},
                            "template": {"type": "string"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_team_health",
                    "description": "Analyze team health metrics and provide recommendations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team_metrics": {"type": "object"},
                            "historical_data": {"type": "object"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "optimize_workload",
                    "description": "Analyze and optimize team workload distribution",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "team_capacity": {"type": "object"},
                            "current_tasks": {"type": "array"},
                            "team_members": {"type": "array"}
                        }
                    }
                }
            }
        ]

        self.assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions="""You are an AI Team Lead responsible for:
                1. Analyzing sprint progress and team performance
                2. Generating detailed reports and insights
                3. Identifying risks and bottlenecks
                4. Providing actionable recommendations
                5. Ensuring clear communication with stakeholders
                6. Optimizing team workload and capacity
                7. Monitoring team health and satisfaction
                8. Facilitating continuous improvement""",
            model="gpt-4-turbo-preview",
            tools=self.tools
        )

    async def send_friday_sprint_report(self):
        """Send sprint report on Fridays"""
        try:
            teams = await self.monday_service.get_teams()
            for team in teams:
                sprint = await self.monday_service.get_active_sprint(team.id)
                if not sprint:
                    continue

                # Calculate comprehensive metrics
                sprint_metrics = await calculate_sprint_metrics(sprint.id)
                team_metrics = await calculate_team_metrics(team.id)
                
                # Check for alerts
                alerts = await self._check_sprint_alerts(sprint_metrics, team_metrics)
                
                # Generate visualizations
                burndown_chart = self.metric_visualizer.create_burndown_chart(sprint_metrics)
                velocity_trend = self.metric_visualizer.create_velocity_trend(team_metrics["velocity_trend"])
                
                # Generate report using AI
                report_data = {
                    "sprint_data": sprint,
                    "metrics": {
                        "sprint": sprint_metrics,
                        "team": team_metrics,
                        "alerts": alerts
                    },
                    "charts": {
                        "burndown": burndown_chart,
                        "velocity": velocity_trend
                    },
                    "template": SPRINT_REPORT_TEMPLATE
                }
                
                analysis = await self._run_assistant(
                    f"Generate a comprehensive sprint report for {team.name} using the provided data: {report_data}"
                )

                # Cache the report
                cache_key = f"sprint_report:{team.id}:{sprint.id}"
                await self.redis_service.set(cache_key, {
                    "report": analysis,
                    "metrics": report_data["metrics"],
                    "charts": report_data["charts"]
                }, expire=60*60*24*7)  # Cache for 7 days

                # Send to Slack with visualizations
                await self.slack_service.send_message(
                    channel=settings.SLACK_TEAM_LEADS_CHANNEL,
                    text=analysis,
                    blocks=[
                        {"type": "section", "text": {"type": "mrkdwn", "text": analysis}},
                        {"type": "image", "title": "Sprint Burndown", "image_url": burndown_chart},
                        {"type": "image", "title": "Velocity Trend", "image_url": velocity_trend}
                    ]
                )

        except Exception as e:
            print(f"Error sending sprint report: {str(e)}")

    async def send_wednesday_progress_report(self):
        """Send progress report on Wednesdays"""
        try:
            teams = await self.monday_service.get_teams()
            for team in teams:
                sprint = await self.monday_service.get_active_sprint(team.id)
                if not sprint or sprint.status != SprintStatus.IN_PROGRESS:
                    continue

                # Get current progress metrics
                progress_data = await self._get_sprint_progress(sprint.id)
                
                # Generate report using AI
                report = await self._run_assistant(
                    f"Generate a mid-sprint progress report for {team.name} using the data: {progress_data}"
                )

                # Send to Slack
                await self.slack_service.send_message(
                    channel=team.slack_channel_id,
                    text=report
                )

        except Exception as e:
            print(f"Error sending progress report: {str(e)}")

    async def send_next_week_kpis(self):
        """Send next week's KPIs and targets"""
        try:
            teams = await self.monday_service.get_teams()
            for team in teams:
                # Get historical and current metrics
                historical_data = await self._get_historical_metrics(team.id)
                current_metrics = await calculate_team_metrics(team.id)
                
                # Generate KPI targets using AI
                kpi_data = {
                    "historical": historical_data,
                    "current": current_metrics,
                    "team": team
                }
                
                targets = await self._run_assistant(
                    f"Generate KPI targets for next week for {team.name} using the data: {kpi_data}"
                )

                # Send to Slack
                await self.slack_service.send_message(
                    channel=team.slack_channel_id,
                    text=targets
                )

        except Exception as e:
            print(f"Error sending KPI targets: {str(e)}")

    async def _check_sprint_alerts(self, sprint_metrics: Dict, team_metrics: Dict) -> List[Dict]:
        """Check for sprint-related alerts"""
        alerts = []
        
        # Check velocity
        alerts.extend(await self.metric_alerts.check_velocity_alerts(
            sprint_metrics["velocity"],
            team_metrics["average_velocity"]
        ))
        
        # Check quality metrics
        alerts.extend(await self.metric_alerts.check_quality_alerts(
            sprint_metrics["quality"]
        ))
        
        return alerts

    async def _get_sprint_progress(self, sprint_id: str) -> Dict:
        """Get current sprint progress data"""
        sprint = await self.monday_service.get_sprint(sprint_id)
        metrics = await calculate_sprint_metrics(sprint_id)
        tasks = await self.monday_service.get_sprint_tasks(sprint_id)
        
        return {
            "sprint": sprint,
            "metrics": metrics,
            "tasks": tasks,
            "burndown": self.metric_visualizer.create_burndown_chart(metrics)
        }

    async def _get_historical_metrics(self, team_id: str) -> Dict:
        """Get historical team metrics"""
        cache_key = f"historical_metrics:{team_id}"
        cached = await self.redis_service.get(cache_key)
        
        if cached:
            return cached
            
        metrics = await generate_metrics_report(team_id, "last_quarter")
        await self.redis_service.set(cache_key, metrics, expire=60*60*24)  # Cache for 24 hours
        
        return metrics 