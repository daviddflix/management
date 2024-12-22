from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from app.services.monday_service import MondayService
from app.services.slack_service import SlackService
from app.services.redis_service import RedisService
from app.utils.metrics import (
    calculate_task_metrics,
    calculate_team_metrics,
    calculate_sprint_metrics
)
from app.utils.metric_alerts import MetricAlertManager
from app.utils.metric_visualizations import MetricVisualizer
from app.models.task import TaskStatus, TaskPriority, TaskType
from app.core.config import settings

class TaskManagementAgent(BaseAgent):
    def __init__(
        self,
        monday_service: MondayService,
        slack_service: SlackService,
        redis_service: RedisService
    ):
        super().__init__(
            name="Task Management Agent",
            description="AI Task Manager responsible for task optimization and workflow management"
        )
        self.monday_service = monday_service
        self.slack_service = slack_service
        self.redis_service = redis_service
        self.metric_alerts = MetricAlertManager(slack_service)
        self.metric_visualizer = MetricVisualizer()

    def _setup_assistant(self):
        """Setup the OpenAI assistant with task management specific tools"""
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "analyze_task_dependencies",
                    "description": "Analyze and manage task dependencies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "related_tasks": {
                                "type": "array",
                                "items": {"type": "object"}
                            },
                            "team_capacity": {"type": "object"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "suggest_task_assignments",
                    "description": "Suggest optimal task assignments based on team skills and workload",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "object"},
                            "team_members": {
                                "type": "array",
                                "items": {"type": "object"}
                            },
                            "current_workload": {"type": "object"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_task_complexity",
                    "description": "Analyze task complexity and suggest story points",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "object"},
                            "historical_data": {"type": "object"},
                            "team_velocity": {"type": "number"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "suggest_task_breakdown",
                    "description": "Suggest how to break down a large task into smaller subtasks",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "object"},
                            "max_story_points": {"type": "number"},
                            "team_capacity": {"type": "object"}
                        }
                    }
                }
            }
        ]

        self.assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions="""You are an AI Task Manager responsible for:
                1. Analyzing and managing task dependencies
                2. Optimizing task assignments based on skills and workload
                3. Identifying and preventing potential blockers
                4. Suggesting workflow improvements
                5. Ensuring balanced workload distribution
                6. Analyzing task complexity and estimation
                7. Breaking down large tasks into manageable pieces
                8. Monitoring task progress and deadlines""",
            model="gpt-4-turbo-preview",
            tools=self.tools
        )

    async def analyze_task_blockers(self, task_id: str):
        """Analyze potential blockers for a task"""
        try:
            task = await self.monday_service.get_task(task_id)
            if not task:
                raise ValueError("Task not found")

            # Get related data
            related_tasks = await self.monday_service.get_related_tasks(task_id)
            team_metrics = await calculate_team_metrics(task.team_id)
            task_metrics = await calculate_task_metrics(task_id)
            
            # Cache key for analysis
            cache_key = f"task_analysis:{task_id}"
            cached_analysis = await self.redis_service.get(cache_key)
            
            if cached_analysis and task.updated_at <= cached_analysis.get("last_updated"):
                return cached_analysis.get("analysis")
            
            analysis = await self._run_assistant(
                f"""Analyze potential blockers and risks for task: {task.title}
                Description: {task.description}
                Current Status: {task.status}
                Dependencies: {task.dependencies}
                Related Tasks: {related_tasks}
                Task Metrics: {task_metrics}
                Team Context: {team_metrics}"""
            )
            
            # Cache the analysis
            await self.redis_service.set(cache_key, {
                "analysis": analysis,
                "last_updated": datetime.now().isoformat()
            }, expire=60*60)  # Cache for 1 hour
            
            # Send alerts if blockers detected
            if "BLOCKER" in analysis.upper() or "HIGH RISK" in analysis.upper():
                await self._send_blocker_alert(task, analysis)
            
            return analysis

        except Exception as e:
            print(f"Error analyzing task blockers: {str(e)}")
            raise

    async def optimize_task_assignments(self, sprint_id: str):
        """Optimize task assignments for a sprint"""
        try:
            sprint = await self.monday_service.get_sprint(sprint_id)
            if not sprint:
                raise ValueError("Sprint not found")

            team_members = await self.monday_service.get_team_members(sprint.team_id)
            team_metrics = await calculate_team_metrics(sprint.team_id)
            current_workload = await self._get_team_workload(sprint.team_id)
            
            optimization_results = []
            for task in sprint.tasks:
                if not task.assignee:
                    # Get task-specific metrics and history
                    task_metrics = await calculate_task_metrics(task.id)
                    historical_assignments = await self._get_historical_assignments(task.labels)
                    
                    suggestion = await self._run_assistant(
                        f"""Suggest optimal team member assignment for task:
                        Task: {task.title}
                        Description: {task.description}
                        Type: {task.type}
                        Priority: {task.priority}
                        Required Skills: {task.labels}
                        Story Points: {task.story_points}
                        
                        Team Context:
                        Current Workload: {current_workload}
                        Team Metrics: {team_metrics}
                        Historical Assignments: {historical_assignments}
                        Available Team Members: {team_members}"""
                    )
                    
                    optimization_results.append({
                        "task_id": task.id,
                        "suggestion": suggestion,
                        "metrics": task_metrics
                    })
            
            # Apply optimizations and notify
            await self._apply_assignment_optimizations(optimization_results)
            
            return optimization_results

        except Exception as e:
            print(f"Error optimizing task assignments: {str(e)}")
            raise

    async def suggest_task_breakdown(self, task_id: str):
        """Suggest how to break down a large task"""
        try:
            task = await self.monday_service.get_task(task_id)
            if not task:
                raise ValueError("Task not found")

            team_metrics = await calculate_team_metrics(task.team_id)
            sprint_metrics = await calculate_sprint_metrics(task.sprint_id)
            
            suggestion = await self._run_assistant(
                f"""Suggest breakdown for large task:
                Task: {task.title}
                Description: {task.description}
                Type: {task.type}
                Story Points: {task.story_points}
                Team Velocity: {team_metrics.get('velocity', 0)}
                Sprint Capacity: {sprint_metrics.get('capacity', 0)}"""
            )
            
            return suggestion

        except Exception as e:
            print(f"Error suggesting task breakdown: {str(e)}")
            raise

    async def _send_blocker_alert(self, task: Dict, analysis: str):
        """Send blocker alert to appropriate channels"""
        alert_message = (
            f"🚨 *Potential Blocker/Risk Detected*\n"
            f"*Task:* {task.title}\n"
            f"*Type:* {task.type}\n"
            f"*Priority:* {task.priority}\n"
            f"*Status:* {task.status}\n\n"
            f"*Analysis:*\n{analysis}"
        )
        
        # Send to team leads channel
        await self.slack_service.send_message(
            channel=settings.SLACK_TEAM_LEADS_CHANNEL,
            text=alert_message
        )
        
        # Send to task assignee if exists
        if task.assignee and task.assignee.slack_id:
            await self.slack_service.send_direct_message(
                user_id=task.assignee.slack_id,
                text=f"🚨 *Important Notice*\nA potential blocker has been identified for your task:\n{alert_message}"
            )

    async def _get_team_workload(self, team_id: str) -> Dict:
        """Get current workload distribution for team members"""
        cache_key = f"team_workload:{team_id}"
        cached = await self.redis_service.get(cache_key)
        
        if cached:
            return cached
            
        team_tasks = await self.monday_service.get_team_tasks(team_id)
        workload = {}
        
        for task in team_tasks:
            if task.assignee:
                if task.assignee.id not in workload:
                    workload[task.assignee.id] = {
                        "assigned_points": 0,
                        "task_count": 0,
                        "tasks_by_priority": {p.value: 0 for p in TaskPriority},
                        "tasks_by_type": {t.value: 0 for t in TaskType}
                    }
                
                workload[task.assignee.id]["assigned_points"] += task.story_points
                workload[task.assignee.id]["task_count"] += 1
                workload[task.assignee.id]["tasks_by_priority"][task.priority] += 1
                workload[task.assignee.id]["tasks_by_type"][task.type] += 1
        
        await self.redis_service.set(cache_key, workload, expire=60*15)  # Cache for 15 minutes
        return workload

    async def _get_historical_assignments(self, labels: List[str]) -> Dict:
        """Get historical task assignment data for given labels"""
        assignments = {}
        for label in labels:
            cache_key = f"historical_assignments:{label}"
            cached = await self.redis_service.get(cache_key)
            
            if cached:
                assignments[label] = cached
                continue
            
            # Get historical data from Monday.com
            historical_data = await self.monday_service.get_historical_assignments(label)
            assignments[label] = historical_data
            
            await self.redis_service.set(cache_key, historical_data, expire=60*60*24)  # Cache for 24 hours
        
        return assignments

    async def _apply_assignment_optimizations(self, optimizations: List[Dict]):
        """Apply task assignment optimizations"""
        for opt in optimizations:
            task_id = opt["task_id"]
            suggestion = opt["suggestion"]
            
            # Parse suggestion to get assignee
            # Implementation depends on the suggestion format from the AI
            
            # Update task assignment
            try:
                await self.monday_service.update_task(task_id, {"assignee_id": suggestion["assignee_id"]})
                
                # Notify relevant team members
                await self._notify_assignment_change(task_id, suggestion)
            except Exception as e:
                print(f"Error applying optimization for task {task_id}: {str(e)}")

    async def _notify_assignment_change(self, task_id: str, suggestion: Dict):
        """Notify relevant team members about assignment changes"""
        task = await self.monday_service.get_task(task_id)
        if not task:
            return
            
        # Notify new assignee
        if task.assignee and task.assignee.slack_id:
            await self.slack_service.send_direct_message(
                user_id=task.assignee.slack_id,
                text=(
                    f"🎯 *New Task Assignment*\n"
                    f"You have been assigned to: {task.title}\n"
                    f"Priority: {task.priority}\n"
                    f"Due Date: {task.due_date}\n\n"
                    f"Reason for assignment: {suggestion.get('reason', 'Based on optimal workload distribution')}"
                )
            )