from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Optional, Dict, Any, List
from enum import Enum
from app.core.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SlackChannelType(str, Enum):
    GENERAL = "general"
    TEAM = "team"
    PROJECT = "project"
    ALERTS = "alerts"
    REPORTS = "reports"
    ANNOUNCEMENTS = "announcements"

class SlackBlockBuilder:
    """Helper class to build Slack Block Kit messages."""
    
    @staticmethod
    def create_header(text: str) -> Dict:
        return {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True
            }
        }
    
    @staticmethod
    def create_section(text: str, fields: Optional[List[str]] = None) -> Dict:
        block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        }
        if fields:
            block["fields"] = [
                {"type": "mrkdwn", "text": field} for field in fields
            ]
        return block
    
    @staticmethod
    def create_divider() -> Dict:
        return {"type": "divider"}
    
    @staticmethod
    def create_context(elements: List[str]) -> Dict:
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": element
                } for element in elements
            ]
        }
    
    @staticmethod
    def create_button(text: str, action_id: str, value: str, style: Optional[str] = None) -> Dict:
        button = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True
            },
            "action_id": action_id,
            "value": value
        }
        if style:
            button["style"] = style
        return button

class SlackTemplates:
    """Templates for different types of Slack messages."""
    
    @staticmethod
    def sprint_report_template(sprint_data: Dict) -> List[Dict]:
        builder = SlackBlockBuilder()
        blocks = [
            builder.create_header(f"Sprint Report: {sprint_data['name']}"),
            builder.create_section(
                f"*Sprint Progress*: {sprint_data['progress']}%",
                [
                    f"*Start Date:* {sprint_data['start_date']}",
                    f"*End Date:* {sprint_data['end_date']}",
                    f"*Status:* {sprint_data['status']}"
                ]
            ),
            builder.create_divider(),
            builder.create_section(
                "*Tasks Overview*",
                [
                    f"*Completed:* {sprint_data['completed_tasks']}",
                    f"*In Progress:* {sprint_data['in_progress_tasks']}",
                    f"*Blocked:* {sprint_data['blocked_tasks']}"
                ]
            ),
            builder.create_context([
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ])
        ]
        return blocks

    @staticmethod
    def task_update_template(task_data: Dict) -> List[Dict]:
        builder = SlackBlockBuilder()
        blocks = [
            builder.create_header("Task Update"),
            builder.create_section(
                f"*{task_data['title']}*\n{task_data['description']}",
                [
                    f"*Status:* {task_data['status']}",
                    f"*Assignee:* {task_data['assignee']}",
                    f"*Priority:* {task_data['priority']}"
                ]
            )
        ]
        if task_data.get('changes'):
            blocks.append(
                builder.create_section("*Changes:*\n" + "\n".join(task_data['changes']))
            )
        return blocks

    @staticmethod
    def daily_summary_template(team_data: Dict) -> List[Dict]:
        builder = SlackBlockBuilder()
        blocks = [
            builder.create_header(f"Daily Summary: {team_data['team_name']}"),
            builder.create_section(
                "*Today's Highlights*",
                [
                    f"*Tasks Completed:* {team_data['completed_today']}",
                    f"*Active Tasks:* {team_data['active_tasks']}",
                    f"*Team Members Active:* {team_data['active_members']}"
                ]
            ),
            builder.create_divider()
        ]
        
        if team_data.get('blockers'):
            blocks.append(
                builder.create_section("*Blockers:*\n" + "\n".join(team_data['blockers']))
            )
            
        blocks.append(
            builder.create_context([
                f"Report generated at {datetime.now().strftime('%H:%M')} • "
                f"Sprint Day {team_data.get('sprint_day', 'N/A')}"
            ])
        )
        return blocks

class SlackService:
    def __init__(self, token: str):
        self.client = WebClient(token=token)
        self._initialize_channels()
        
    def _initialize_channels(self):
        """Initialize default channels configuration."""
        self.channels = {
            SlackChannelType.GENERAL: settings.SLACK_DEFAULT_CHANNEL,
            SlackChannelType.TEAM: settings.SLACK_TEAM_CHANNEL,
            SlackChannelType.PROJECT: settings.SLACK_PROJECT_CHANNEL,
            SlackChannelType.ALERTS: settings.SLACK_ALERTS_CHANNEL,
            SlackChannelType.REPORTS: settings.SLACK_REPORTS_CHANNEL,
            SlackChannelType.ANNOUNCEMENTS: settings.SLACK_ANNOUNCEMENTS_CHANNEL
        }

    def update_channel(self, channel_type: SlackChannelType, channel_id: str):
        """Update channel configuration."""
        self.channels[channel_type] = channel_id

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
        reply_broadcast: bool = False
    ) -> Dict[str, Any]:
        """Send a message to a Slack channel."""
        try:
            response = await self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
                reply_broadcast=reply_broadcast
            )
            return response
        except SlackApiError as e:
            logger.error(f"Failed to send Slack message: {str(e)}")
            raise Exception(f"Failed to send Slack message: {str(e)}")

    async def send_sprint_report(
        self, 
        sprint_data: Dict, 
        channel_type: SlackChannelType = SlackChannelType.REPORTS
    ):
        """Send sprint report using template."""
        blocks = SlackTemplates.sprint_report_template(sprint_data)
        channel = self.channels.get(channel_type, self.channels[SlackChannelType.GENERAL])
        
        await self.send_message(
            channel=channel,
            text=f"Sprint Report: {sprint_data['name']}",
            blocks=blocks
        )

    async def send_task_update(
        self, 
        task_data: Dict, 
        channel_type: SlackChannelType = SlackChannelType.TEAM
    ):
        """Send task update using template."""
        blocks = SlackTemplates.task_update_template(task_data)
        channel = self.channels.get(channel_type, self.channels[SlackChannelType.GENERAL])
        
        await self.send_message(
            channel=channel,
            text=f"Task Update: {task_data['title']}",
            blocks=blocks
        )

    async def send_daily_summary(
        self, 
        team_data: Dict, 
        channel_type: SlackChannelType = SlackChannelType.TEAM
    ):
        """Send daily team summary using template."""
        blocks = SlackTemplates.daily_summary_template(team_data)
        channel = self.channels.get(channel_type, self.channels[SlackChannelType.GENERAL])
        
        await self.send_message(
            channel=channel,
            text=f"Daily Summary: {team_data['team_name']}",
            blocks=blocks
        )

    async def send_thread_reply(
        self,
        channel: str,
        thread_ts: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        broadcast: bool = False
    ):
        """Send a reply in a thread."""
        return await self.send_message(
            channel=channel,
            text=text,
            blocks=blocks,
            thread_ts=thread_ts,
            reply_broadcast=broadcast
        )

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: Optional[List[Dict]] = None
    ):
        """Update an existing message."""
        try:
            return await self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks
            )
        except SlackApiError as e:
            logger.error(f"Failed to update Slack message: {str(e)}")
            raise Exception(f"Failed to update Slack message: {str(e)}")

# Create a global instance
slack_service = SlackService(settings.SLACK_BOT_TOKEN) 