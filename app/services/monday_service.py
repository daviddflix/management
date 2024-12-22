from typing import List, Optional, Dict, Any
from monday import MondayClient
from datetime import datetime
import logging
from enum import Enum
import json

from app.models.task import Task, TaskCreate, TaskUpdate, TaskStatus, TaskPriority
from app.core.config import settings

logger = logging.getLogger(__name__)

class MondayColumnIds(str, Enum):
    """Monday.com column IDs mapping."""
    STATUS = "status"
    PRIORITY = "priority"
    ASSIGNEE = "person"
    DESCRIPTION = "text"
    SPRINT = "sprint"
    STORY_POINTS = "numbers"
    DUE_DATE = "date"
    LABELS = "tags"

class MondayService:
    def __init__(self, api_key: str):
        self.client = MondayClient(api_key)
        self.board_id = settings.MONDAY_BOARD_ID

    async def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        priority: Optional[TaskPriority] = None
    ) -> List[Task]:
        """
        Get tasks with optional filtering.
        
        Args:
            status: Filter by task status
            assignee_id: Filter by assignee
            sprint_id: Filter by sprint
            priority: Filter by priority
        """
        try:
            query = """
            query ($boardId: ID!) {
                boards(ids: [$boardId]) {
                    items {
                        id
                        name
                        created_at
                        updated_at
                        column_values {
                            id
                            text
                            value
                        }
                        subitems {
                            id
                            name
                        }
                    }
                }
            }
            """
            
            variables = {"boardId": self.board_id}
            response = await self.client.execute_query(query, variables)
            
            if not response.get("data", {}).get("boards"):
                logger.error("No boards found in Monday.com response")
                return []
                
            tasks = []
            for item in response["data"]["boards"][0]["items"]:
                task = self._monday_item_to_task(item)
                
                # Apply filters
                if status and task.status != status:
                    continue
                if assignee_id and task.assignee_id != assignee_id:
                    continue
                if sprint_id and task.sprint_id != sprint_id:
                    continue
                if priority and task.priority != priority:
                    continue
                    
                tasks.append(task)
                
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks from Monday.com: {str(e)}")
            raise

    async def create_task(self, task: TaskCreate) -> Task:
        """
        Create a new task in Monday.com.
        
        Args:
            task: Task creation data
        """
        try:
            mutation = """
            mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
                create_item (
                    board_id: $boardId,
                    item_name: $itemName,
                    column_values: $columnValues
                ) {
                    id
                    name
                    created_at
                    updated_at
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
            """
            
            variables = {
                "boardId": self.board_id,
                "itemName": task.title,
                "columnValues": self._task_to_monday_values(task)
            }
            
            response = await self.client.execute_mutation(mutation, variables)
            
            if not response.get("data", {}).get("create_item"):
                raise Exception("Failed to create task in Monday.com")
                
            return self._monday_item_to_task(response["data"]["create_item"])
            
        except Exception as e:
            logger.error(f"Error creating task in Monday.com: {str(e)}")
            raise

    async def update_task(self, task_id: str, task_update: TaskUpdate) -> Task:
        """
        Update an existing task in Monday.com.
        
        Args:
            task_id: Monday.com item ID
            task_update: Task update data
        """
        try:
            mutation = """
            mutation ($itemId: ID!, $columnValues: JSON!) {
                change_multiple_column_values (
                    item_id: $itemId,
                    board_id: $boardId,
                    column_values: $columnValues
                ) {
                    id
                    name
                    updated_at
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
            """
            
            variables = {
                "itemId": task_id,
                "boardId": self.board_id,
                "columnValues": self._update_to_monday_values(task_update)
            }
            
            response = await self.client.execute_mutation(mutation, variables)
            
            if not response.get("data", {}).get("change_multiple_column_values"):
                raise Exception("Failed to update task in Monday.com")
                
            return self._monday_item_to_task(response["data"]["change_multiple_column_values"])
            
        except Exception as e:
            logger.error(f"Error updating task in Monday.com: {str(e)}")
            raise

    def _monday_item_to_task(self, item: Dict[str, Any]) -> Task:
        """Convert Monday.com item to Task model."""
        column_values = {cv["id"]: cv for cv in item["column_values"]}
        
        return Task(
            id=item["id"],
            title=item["name"],
            description=self._get_column_text(column_values, MondayColumnIds.DESCRIPTION),
            status=TaskStatus(self._get_column_text(column_values, MondayColumnIds.STATUS, "todo")),
            priority=TaskPriority(self._get_column_text(column_values, MondayColumnIds.PRIORITY, "medium")),
            assignee_id=self._get_column_value(column_values, MondayColumnIds.ASSIGNEE, "personsAndTeams", [{}])[0].get("id"),
            sprint_id=self._get_column_text(column_values, MondayColumnIds.SPRINT),
            story_points=float(self._get_column_text(column_values, MondayColumnIds.STORY_POINTS, "0")),
            due_date=self._parse_monday_date(self._get_column_text(column_values, MondayColumnIds.DUE_DATE)),
            labels=self._get_column_value(column_values, MondayColumnIds.LABELS, "tags", []),
            monday_item_id=item["id"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"])
        )

    def _task_to_monday_values(self, task: TaskCreate) -> Dict[str, Any]:
        """Convert Task creation data to Monday.com column values."""
        values = {
            MondayColumnIds.DESCRIPTION: task.description,
            MondayColumnIds.STATUS: {"label": task.status},
            MondayColumnIds.PRIORITY: {"label": task.priority},
            MondayColumnIds.STORY_POINTS: str(task.story_points) if task.story_points else "0"
        }
        
        if task.assignee_id:
            values[MondayColumnIds.ASSIGNEE] = {"personsAndTeams": [{"id": task.assignee_id}]}
            
        if task.sprint_id:
            values[MondayColumnIds.SPRINT] = {"text": task.sprint_id}
            
        if task.due_date:
            values[MondayColumnIds.DUE_DATE] = {"date": task.due_date.isoformat()}
            
        if task.labels:
            values[MondayColumnIds.LABELS] = {"tags": task.labels}
            
        return values

    def _update_to_monday_values(self, update: TaskUpdate) -> Dict[str, Any]:
        """Convert Task update data to Monday.com column values."""
        values = {}
        
        if update.description is not None:
            values[MondayColumnIds.DESCRIPTION] = update.description
            
        if update.status is not None:
            values[MondayColumnIds.STATUS] = {"label": update.status}
            
        if update.priority is not None:
            values[MondayColumnIds.PRIORITY] = {"label": update.priority}
            
        if update.assignee_id is not None:
            values[MondayColumnIds.ASSIGNEE] = {"personsAndTeams": [{"id": update.assignee_id}] if update.assignee_id else []}
            
        if update.sprint_id is not None:
            values[MondayColumnIds.SPRINT] = {"text": update.sprint_id} if update.sprint_id else {"text": ""}
            
        if update.story_points is not None:
            values[MondayColumnIds.STORY_POINTS] = str(update.story_points)
            
        if update.due_date is not None:
            values[MondayColumnIds.DUE_DATE] = {"date": update.due_date.isoformat()} if update.due_date else {"date": ""}
            
        if update.labels is not None:
            values[MondayColumnIds.LABELS] = {"tags": update.labels}
            
        return values

    @staticmethod
    def _get_column_text(columns: Dict[str, Any], column_id: str, default: str = "") -> str:
        """Safely get column text value."""
        return columns.get(column_id, {}).get("text", default)

    @staticmethod
    def _get_column_value(columns: Dict[str, Any], column_id: str, key: str, default: Any = None) -> Any:
        """Safely get column value by key."""
        try:
            return json.loads(columns.get(column_id, {}).get("value", "{}")).get(key, default)
        except:
            return default

    @staticmethod
    def _parse_monday_date(date_str: str) -> Optional[datetime]:
        """Parse Monday.com date string to datetime."""
        try:
            return datetime.fromisoformat(date_str) if date_str else None
        except:
            return None

# Create a global instance
monday_service = MondayService(settings.MONDAY_API_KEY)
    



