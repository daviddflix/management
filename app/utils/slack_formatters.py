from typing import Dict, List

def format_sprint_report(sprint_data: Dict) -> List[Dict]:
    """Format sprint data into Slack blocks"""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Sprint Report: {sprint_data['name']}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n{sprint_data['status']}"},
                {"type": "mrkdwn", "text": f"*Velocity:*\n{sprint_data['velocity']}"},
                {"type": "mrkdwn", "text": f"*Completed Tasks:*\n{len(sprint_data['completed_tasks'])}"},
                {"type": "mrkdwn", "text": f"*Remaining Tasks:*\n{len(sprint_data['remaining_tasks'])}"}
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Sprint Goal:*\n{sprint_data['goal']}"
            }
        }
    ]

def format_task_update(task_data: Dict) -> List[Dict]:
    """Format task update into Slack blocks"""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Task Update:* {task_data['title']}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Status:*\n{task_data['status']}"},
                {"type": "mrkdwn", "text": f"*Assignee:*\n{task_data['assignee']}"},
                {"type": "mrkdwn", "text": f"*Priority:*\n{task_data['priority']}"},
                {"type": "mrkdwn", "text": f"*Sprint:*\n{task_data.get('sprint_name', 'Not assigned')}"}
            ]
        }
    ]

def format_daily_summary(team_data: Dict) -> List[Dict]:
    """Format daily team summary into Slack blocks"""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Daily Summary: {team_data['team_name']}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Active Sprint:*\n{team_data['active_sprint']}"},
                {"type": "mrkdwn", "text": f"*Sprint Progress:*\n{team_data['progress']}%"},
                {"type": "mrkdwn", "text": f"*Tasks Completed Today:*\n{len(team_data['completed_today'])}"},
                {"type": "mrkdwn", "text": f"*Tasks In Progress:*\n{len(team_data['in_progress'])}"}
            ]
        }
    ] 