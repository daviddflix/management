from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskType(str, Enum):
    FEATURE = "feature"
    BUG = "bug"
    TECHNICAL_DEBT = "technical_debt"
    IMPROVEMENT = "improvement"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    COMPLEX = "complex" 