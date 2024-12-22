from typing import List, Optional, Dict, Any
from monday import MondayClient
from datetime import datetime
from app.core.logging import app_logger as logger
from enum import Enum
import json

from app.models.task import TaskResponse, TaskCreate, TaskUpdate, TaskStatus, TaskPriority, TaskType
from app.core.config import settings

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
    TYPE = "type"  # New column for task type

class MondayTaskTypeMapping:
    """Mapping between Monday.com task types and our TaskType enum."""
    MONDAY_TO_APP = {
        "Feature": TaskType.FEATURE,
        "Bug": TaskType.BUG,
        "Tech Debt": TaskType.TECH_DEBT,
        "Documentation": TaskType.DOCUMENTATION,
        "Research": TaskType.RESEARCH,
        "Maintenance": TaskType.MAINTENANCE
    }
    
    APP_TO_MONDAY = {v: k for k, v in MONDAY_TO_APP.items()}
    
    @classmethod
    def to_app_type(cls, monday_type: str) -> TaskType:
        """Convert Monday.com type to application TaskType."""
        return cls.MONDAY_TO_APP.get(monday_type, TaskType.FEATURE)
    
    @classmethod
    def to_monday_type(cls, app_type: TaskType) -> str:
        """Convert application TaskType to Monday.com type."""
        return cls.APP_TO_MONDAY.get(app_type, "Feature")

class MondayService:
    def __init__(self, api_key: str):
        self.client = MondayClient(api_key)
        self.board_ids = json.loads(settings.MONDAY_BOARD_IDS)
        self.default_board_id = settings.MONDAY_DEFAULT_BOARD_ID
        self.rate_limit = settings.MONDAY_RATE_LIMIT

    async def get_tasks(
        self,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[str] = None,
        sprint_id: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        board_id: Optional[str] = None
    ) -> List[TaskResponse]:
        """
        Get tasks with optional filtering.
        If board_id is not specified, fetches from all configured boards.
        """
        all_tasks = []
        boards_to_query = [board_id] if board_id else self.board_ids
        
        for board in boards_to_query:
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
                
                variables = {"boardId": board}
                response = await self.client.execute_query(query, variables)
                
                if not response.get("data", {}).get("boards"):
                    logger.error("No boards found in Monday.com response")
                    continue
                    
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
                        
                    all_tasks.append(task)
                    
            except Exception as e:
                logger.error(f"Error fetching tasks from board {board}: {str(e)}")
                continue
        
        return all_tasks

    async def create_task(
        self,
        task: TaskCreate,
        board_id: Optional[str] = None
    ) -> TaskResponse:
        """Create a new task on the specified board or default board."""
        target_board = board_id or self.default_board_id
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
                "boardId": target_board,
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

    async def update_task(
        self,
        task_id: str,
        task: TaskUpdate,
        board_id: Optional[str] = None
    ) -> TaskResponse:
        """
        Update a task on the specified board.
        If board_id is not provided, searches all boards for the task.
        """
        if board_id:
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
                    "boardId": board_id,
                    "columnValues": self._update_to_monday_values(task)
                }
                
                response = await self.client.execute_mutation(mutation, variables)
                
                if not response.get("data", {}).get("change_multiple_column_values"):
                    raise Exception("Failed to update task in Monday.com")
                    
                return self._monday_item_to_task(response["data"]["change_multiple_column_values"])
                
            except Exception as e:
                logger.error(f"Error updating task in Monday.com: {str(e)}")
                raise
        else:
            for board in self.board_ids:
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
                        "boardId": board,
                        "columnValues": self._update_to_monday_values(task)
                    }
                    
                    response = await self.client.execute_mutation(mutation, variables)
                    
                    if not response.get("data", {}).get("change_multiple_column_values"):
                        raise Exception("Failed to update task in Monday.com")
                        
                    return self._monday_item_to_task(response["data"]["change_multiple_column_values"])
                    
                except Exception as e:
                    continue
            
        raise ValueError(f"Task {task_id} not found on any board")

    async def get_board_info(self, board_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get information about one or all boards."""
        boards_to_query = [board_id] if board_id else self.board_ids
        board_info = []
        
        for board in boards_to_query:
            try:
                # Fetch board information
                # ... implementation ...
                pass
            except Exception as e:
                logger.error(f"Error fetching board info for {board}: {str(e)}")
                continue
                
        return board_info

    def _monday_item_to_task(self, item: Dict[str, Any]) -> TaskResponse:
        """Convert Monday.com item to TaskResponse model."""
        column_values = {cv["id"]: cv for cv in item["column_values"]}
        
        return TaskResponse(
            id=item["id"],
            title=item["name"],
            description=self._get_column_text(column_values, MondayColumnIds.DESCRIPTION),
            status=TaskStatus(self._get_column_text(column_values, MondayColumnIds.STATUS, "todo")),
            priority=TaskPriority(self._get_column_text(column_values, MondayColumnIds.PRIORITY, "medium")),
            type=MondayTaskTypeMapping.to_app_type(self._get_column_text(column_values, MondayColumnIds.TYPE)),
            assignee_id=self._get_column_value(column_values, MondayColumnIds.ASSIGNEE, "personsAndTeams", [{}])[0].get("id"),
            sprint_id=self._get_column_text(column_values, MondayColumnIds.SPRINT),
            story_points=float(self._get_column_text(column_values, MondayColumnIds.STORY_POINTS, "0")),
            labels=self._get_column_value(column_values, MondayColumnIds.LABELS, "tags", []),
            monday_task_id=item["id"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            team_id="",  # This should be set from your application context
            creator_id=""  # This should be set from your application context
        )

    def _task_to_monday_values(self, task: TaskCreate) -> Dict[str, Any]:
        """Convert Task creation data to Monday.com column values."""
        values = {
            MondayColumnIds.DESCRIPTION: task.description,
            MondayColumnIds.STATUS: {"label": TaskStatus.BACKLOG.value},
            MondayColumnIds.PRIORITY: {"label": task.priority.value},
            MondayColumnIds.TYPE: {"label": MondayTaskTypeMapping.to_monday_type(task.type)},
            MondayColumnIds.STORY_POINTS: str(task.story_points) if task.story_points else "0"
        }
        
        if task.assignee_id:
            values[MondayColumnIds.ASSIGNEE] = {"personsAndTeams": [{"id": task.assignee_id}]}
            
        if task.sprint_id:
            values[MondayColumnIds.SPRINT] = {"text": task.sprint_id}
            
        if task.labels:
            values[MondayColumnIds.LABELS] = {"tags": task.labels}
            
        return values

    def _update_to_monday_values(self, update: TaskUpdate) -> Dict[str, Any]:
        """Convert Task update data to Monday.com column values."""
        values = {}
        
        if update.description is not None:
            values[MondayColumnIds.DESCRIPTION] = update.description
            
        if update.status is not None:
            values[MondayColumnIds.STATUS] = {"label": update.status.value}
            
        if update.priority is not None:
            values[MondayColumnIds.PRIORITY] = {"label": update.priority.value}
            
        if update.type is not None:
            values[MondayColumnIds.TYPE] = {"label": MondayTaskTypeMapping.to_monday_type(update.type)}
            
        if update.assignee_id is not None:
            values[MondayColumnIds.ASSIGNEE] = {"personsAndTeams": [{"id": update.assignee_id}] if update.assignee_id else []}
            
        if update.sprint_id is not None:
            values[MondayColumnIds.SPRINT] = {"text": update.sprint_id} if update.sprint_id else {"text": ""}
            
        if update.story_points is not None:
            values[MondayColumnIds.STORY_POINTS] = str(update.story_points)
            
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
    



