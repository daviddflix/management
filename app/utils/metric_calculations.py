from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from app.models.task import TaskStatus
from app.models.database.metrics import SprintMetrics, TeamMetrics, TaskMetrics

async def calculate_velocity_metrics(tasks: List[Dict]) -> Dict[str, float]:
    """Calculate velocity-related metrics"""
    completed_points = sum(task.story_points for task in tasks if task.status == TaskStatus.DONE)
    planned_points = sum(task.story_points for task in tasks)
    
    return {
        "completed_points": completed_points,
        "planned_points": planned_points,
        "completion_rate": (completed_points / planned_points * 100) if planned_points > 0 else 0,
        "velocity": completed_points
    }

async def calculate_code_quality_metrics(tasks: List[Dict]) -> Dict[str, Any]:
    """Calculate code quality metrics"""
    metrics = {
        "code_review_time": await calculate_review_time(tasks),
        "rework_rate": await calculate_rework_rate(tasks),
        "defect_density": await calculate_defect_density(tasks),
        "test_coverage": await calculate_test_coverage(tasks),
        "code_complexity": await calculate_code_complexity(tasks)
    }
    return metrics

async def calculate_team_health_metrics(team_id: str) -> Dict[str, Any]:
    """Calculate team health metrics"""
    metrics = {
        "task_distribution": await analyze_task_distribution(team_id),
        "workload_balance": await calculate_workload_balance(team_id),
        "collaboration_score": await calculate_collaboration_score(team_id),
        "knowledge_sharing": await calculate_knowledge_sharing(team_id),
        "team_satisfaction": await calculate_team_satisfaction(team_id)
    }
    return metrics

# Detailed metric calculations
async def calculate_review_time(tasks: List[Dict]) -> Dict[str, float]:
    """Calculate code review time metrics"""
    review_times = [
        (task.review_completed_at - task.review_started_at).total_seconds() / 3600
        for task in tasks
        if task.review_completed_at and task.review_started_at
    ]
    
    return {
        "average_review_time": np.mean(review_times) if review_times else 0,
        "median_review_time": np.median(review_times) if review_times else 0,
        "max_review_time": max(review_times) if review_times else 0
    }

async def calculate_rework_rate(tasks: List[Dict]) -> Dict[str, float]:
    """Calculate rework rate metrics"""
    rework_counts = [task.rework_count for task in tasks if task.rework_count]
    
    return {
        "average_rework_rate": np.mean(rework_counts) if rework_counts else 0,
        "tasks_with_rework": len([t for t in tasks if t.rework_count > 0]),
        "high_rework_tasks": len([t for t in tasks if t.rework_count > 2])
    }

async def calculate_defect_density(tasks: List[Dict]) -> Dict[str, float]:
    """Calculate defect density metrics"""
    total_loc = sum(task.lines_of_code for task in tasks if task.lines_of_code)
    defects = sum(task.defect_count for task in tasks if task.defect_count)
    
    return {
        "defect_density": (defects / total_loc * 1000) if total_loc > 0 else 0,
        "total_defects": defects,
        "defects_per_task": defects / len(tasks) if tasks else 0
    } 