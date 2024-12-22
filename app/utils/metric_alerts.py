from typing import Dict, Any, List
from datetime import datetime
from app.services.slack_service import SlackService

class MetricAlertManager:
    def __init__(self, slack_service: SlackService):
        self.slack_service = slack_service
        self.alert_thresholds = {
            "velocity_drop": 20,  # Percentage drop in velocity
            "high_rework_rate": 0.3,  # 30% rework rate
            "low_test_coverage": 80,  # Below 80% coverage
            "review_time_exceeded": 48,  # Hours
            "team_health_critical": 0.6  # Below 60% health score
        }

    async def check_velocity_alerts(self, current_velocity: float, historical_velocity: float) -> List[Dict]:
        """Check for velocity-related alerts"""
        alerts = []
        if historical_velocity > 0:
            velocity_drop = (historical_velocity - current_velocity) / historical_velocity * 100
            if velocity_drop > self.alert_thresholds["velocity_drop"]:
                alerts.append({
                    "type": "velocity_drop",
                    "severity": "high",
                    "message": f"Velocity dropped by {velocity_drop:.1f}%",
                    "metrics": {"current": current_velocity, "historical": historical_velocity}
                })
        return alerts

    async def check_quality_alerts(self, quality_metrics: Dict) -> List[Dict]:
        """Check for quality-related alerts"""
        alerts = []
        
        # Check test coverage
        if quality_metrics["test_coverage"] < self.alert_thresholds["low_test_coverage"]:
            alerts.append({
                "type": "low_test_coverage",
                "severity": "medium",
                "message": f"Test coverage below threshold: {quality_metrics['test_coverage']}%"
            })
        
        # Check rework rate
        if quality_metrics["rework_rate"] > self.alert_thresholds["high_rework_rate"]:
            alerts.append({
                "type": "high_rework_rate",
                "severity": "high",
                "message": f"High rework rate detected: {quality_metrics['rework_rate']*100:.1f}%"
            })
        
        return alerts

    async def send_alerts(self, alerts: List[Dict], channel: str):
        """Send alerts to appropriate channels"""
        for alert in alerts:
            message = self._format_alert_message(alert)
            await self.slack_service.send_message(
                channel=channel,
                text=message,
                blocks=self._create_alert_blocks(alert)
            )

    def _format_alert_message(self, alert: Dict) -> str:
        """Format alert message for Slack"""
        severity_emoji = {
            "low": "ℹ️",
            "medium": "⚠️",
            "high": "🚨"
        }
        return f"{severity_emoji[alert['severity']]} *{alert['type']}*: {alert['message']}" 