from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.sprint import SprintResponse, SprintStatus
from app.models.task import TaskResponse, TaskStatus
from app.models.database.sprint import DBSprint
from app.models.database.task import DBTask
from app.models.database.team import Team
from app.core.database import get_db

async def calculate_team_metrics(
    team_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """Calculate comprehensive team metrics"""
    if db is None:
        db = next(get_db())

    metrics = {
        "velocity": await calculate_velocity(team_id, start_date, end_date, db),
        "quality": await calculate_quality_metrics(team_id, db),
        "efficiency": await calculate_efficiency_metrics(team_id, db),
        "health": await calculate_team_health(team_id, db),
        "trends": await calculate_trends(team_id, db)
    }
    return metrics

async def calculate_sprint_metrics(sprint_id: str, db: AsyncSession = None) -> Dict[str, Any]:
    """Calculate sprint-specific metrics"""
    if db is None:
        db = next(get_db())

    metrics = {
        "completion_rate": await calculate_completion_rate(sprint_id, db),
        "velocity": await calculate_sprint_velocity(sprint_id, db),
        "quality_score": await calculate_quality_score(sprint_id, db),
        "burndown": await generate_burndown_data(sprint_id, db),
        "team_satisfaction": await calculate_team_satisfaction(sprint_id, db)
    }
    return metrics

async def calculate_task_metrics(task_id: str, db: AsyncSession = None) -> Dict[str, Any]:
    """Calculate task-specific metrics"""
    if db is None:
        db = next(get_db())

    metrics = {
        "cycle_time": await calculate_cycle_time(task_id, db),
        "quality_score": await calculate_task_quality(task_id, db),
        "complexity": await calculate_task_complexity(task_id, db),
        "rework_rate": await calculate_rework_rate(task_id, db)
    }
    return metrics

async def generate_metrics_report(
    team_id: str,
    time_period: str,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """Generate comprehensive metrics report"""
    if db is None:
        db = next(get_db())

    report = {
        "summary": await generate_summary_metrics(team_id, time_period, db),
        "details": await generate_detailed_metrics(team_id, time_period, db),
        "recommendations": await generate_recommendations(team_id, db),
        "trends": await analyze_trends(team_id, time_period, db)
    }
    return report

# Helper functions for specific metric calculations
async def calculate_velocity(
    team_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = None
) -> float:
    """Calculate team velocity based on completed story points"""
    if db is None:
        db = next(get_db())

    query = select(DBSprint).where(DBSprint.team_id == team_id)
    
    if start_date:
        query = query.where(DBSprint.end_date >= start_date)
    if end_date:
        query = query.where(DBSprint.end_date <= end_date)
    
    query = query.where(DBSprint.status == SprintStatus.COMPLETED)
    
    result = await db.execute(query)
    sprints = result.scalars().all()
    
    if not sprints:
        return 0.0
    
    total_points = sum(sprint.completed_points for sprint in sprints)
    return total_points / len(sprints)

async def calculate_quality_score(sprint_id: str, db: AsyncSession = None) -> float:
    """Calculate quality score for a sprint based on bugs and code review metrics"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(
        DBTask.sprint_id == sprint_id,
        DBTask.status == TaskStatus.DONE
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return 0.0
    
    total_bugs = sum(1 for task in tasks if task.type == "bug")
    code_review_time = sum(task.metrics.get("review_time", 0) for task in tasks)
    test_coverage = sum(task.metrics.get("test_coverage", 0) for task in tasks) / len(tasks)
    
    # Quality score formula: 100 - (bugs * 10) - (review_time_penalty) + (test_coverage_bonus)
    quality_score = 100 - (total_bugs * 10) - (code_review_time * 0.1) + (test_coverage * 0.2)
    return max(0.0, min(100.0, quality_score))

async def calculate_efficiency_metrics(team_id: str, db: AsyncSession = None) -> Dict[str, float]:
    """Calculate team efficiency metrics"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(
        DBTask.team_id == team_id,
        DBTask.status == TaskStatus.DONE
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "cycle_time": 0.0,
            "throughput": 0.0,
            "work_in_progress": 0.0
        }
    
    # Calculate average cycle time
    cycle_times = [
        (task.updated_at - task.created_at).total_seconds() / 3600
        for task in tasks
    ]
    avg_cycle_time = sum(cycle_times) / len(cycle_times)
    
    # Calculate throughput (tasks completed per week)
    earliest_task = min(tasks, key=lambda t: t.created_at)
    latest_task = max(tasks, key=lambda t: t.updated_at)
    total_weeks = ((latest_task.updated_at - earliest_task.created_at).days / 7) or 1
    throughput = len(tasks) / total_weeks
    
    # Calculate average work in progress
    wip_query = select(func.count(DBTask.id)).where(
        DBTask.team_id == team_id,
        DBTask.status == TaskStatus.IN_PROGRESS
    )
    result = await db.execute(wip_query)
    wip = result.scalar() or 0
    
    return {
        "cycle_time": avg_cycle_time,
        "throughput": throughput,
        "work_in_progress": float(wip)
    }

async def calculate_team_health(team_id: str, db: AsyncSession = None) -> Dict[str, float]:
    """Calculate team health metrics"""
    if db is None:
        db = next(get_db())

    # Get team with related data
    query = select(Team).where(Team.id == team_id).options(
        selectinload(Team.members),
        selectinload(Team.sprints)
    )
    
    result = await db.execute(query)
    team = result.scalar_one_or_none()
    
    if not team:
        return {
            "member_satisfaction": 0.0,
            "sprint_completion_rate": 0.0,
            "team_stability": 0.0
        }
    
    # Calculate sprint completion rate
    completed_sprints = [s for s in team.sprints if s.status == SprintStatus.COMPLETED]
    if completed_sprints:
        completion_rate = sum(
            s.completed_points / s.planned_points if s.planned_points else 0
            for s in completed_sprints
        ) / len(completed_sprints)
    else:
        completion_rate = 0.0
    
    # Calculate team stability (member retention)
    current_members = len(team.members)
    total_members = current_members  # This should ideally track historical members
    stability = current_members / total_members if total_members else 1.0
    
    # Member satisfaction would typically come from surveys or other feedback
    # For now, we'll use a placeholder calculation
    satisfaction = completion_rate * 0.7 + stability * 0.3
    
    return {
        "member_satisfaction": satisfaction * 100,
        "sprint_completion_rate": completion_rate * 100,
        "team_stability": stability * 100
    }

async def calculate_trends(team_id: str, db: AsyncSession = None) -> Dict[str, List[float]]:
    """Calculate trend data for various metrics"""
    if db is None:
        db = next(get_db())

    # Get completed sprints for the team
    query = select(DBSprint).where(
        DBSprint.team_id == team_id,
        DBSprint.status == SprintStatus.COMPLETED
    ).order_by(DBSprint.end_date)
    
    result = await db.execute(query)
    sprints = result.scalars().all()
    
    if not sprints:
        return {
            "velocity_trend": [],
            "quality_trend": [],
            "efficiency_trend": []
        }
    
    velocity_trend = [sprint.velocity for sprint in sprints]
    quality_trend = [await calculate_quality_score(sprint.id, db) for sprint in sprints]
    
    efficiency_data = []
    for sprint in sprints:
        metrics = await calculate_efficiency_metrics(team_id, db)
        efficiency_data.append(
            (metrics["throughput"] * 0.4 + 
             (100 - metrics["cycle_time"]) * 0.4 +
             (100 - metrics["work_in_progress"]) * 0.2) / 100
        )
    
    return {
        "velocity_trend": velocity_trend,
        "quality_trend": quality_trend,
        "efficiency_trend": efficiency_data
    }

# Additional helper functions
async def calculate_cycle_time(task_id: str, db: AsyncSession = None) -> float:
    """Calculate cycle time for a task"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(DBTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task or task.status != TaskStatus.DONE:
        return 0.0
    
    cycle_time = (task.updated_at - task.created_at).total_seconds() / 3600
    return cycle_time

async def calculate_task_quality(task_id: str, db: AsyncSession = None) -> float:
    """Calculate quality score for a task"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(DBTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        return 0.0
    
    metrics = task.metrics or {}
    
    # Quality score based on various factors
    review_time = metrics.get("review_time", 0)
    bug_count = metrics.get("bug_count", 0)
    test_coverage = metrics.get("test_coverage", 0)
    
    quality_score = 100 - (bug_count * 10) - (review_time * 0.1) + (test_coverage * 0.2)
    return max(0.0, min(100.0, quality_score))

async def calculate_task_complexity(task_id: str, db: AsyncSession = None) -> float:
    """Calculate complexity score for a task"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(DBTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        return 0.0
    
    # Complexity factors
    story_points = task.story_points
    dependencies = len(task.dependencies or [])
    review_comments = len(task.metrics.get("review_comments", []))
    
    # Complexity score formula
    complexity = (
        (story_points / 13) * 50 +  # Max story points is 13
        (dependencies / 5) * 25 +   # Assume max 5 dependencies
        (review_comments / 10) * 25 # Assume max 10 review comments
    )
    
    return min(100.0, complexity)

async def calculate_rework_rate(task_id: str, db: AsyncSession = None) -> float:
    """Calculate rework rate for a task"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(DBTask.id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        return 0.0
    
    history = task.history or []
    status_changes = [
        h for h in history
        if h.get("field") == "status" and h["new_value"] == TaskStatus.IN_PROGRESS.value
    ]
    
    # Rework is when a task goes back to in progress
    rework_count = max(0, len(status_changes) - 1)
    return rework_count

async def calculate_quality_metrics(team_id: str, db: AsyncSession = None) -> Dict[str, float]:
    """Calculate quality metrics for a team"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(
        DBTask.team_id == team_id,
        DBTask.status == TaskStatus.DONE
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "bug_rate": 0.0,
            "code_quality": 0.0,
            "test_coverage": 0.0
        }
    
    # Calculate bug rate
    total_bugs = sum(1 for task in tasks if task.type == "bug")
    bug_rate = (total_bugs / len(tasks)) * 100
    
    # Calculate code quality based on review metrics
    code_quality = sum(
        100 - (task.metrics.get("review_comments", 0) * 2)  # Each comment reduces quality
        for task in tasks
    ) / len(tasks)
    code_quality = max(0.0, min(100.0, code_quality))
    
    # Calculate average test coverage
    test_coverage = sum(
        task.metrics.get("test_coverage", 0)
        for task in tasks
    ) / len(tasks)
    
    return {
        "bug_rate": bug_rate,
        "code_quality": code_quality,
        "test_coverage": test_coverage
    }

async def calculate_completion_rate(sprint_id: str, db: AsyncSession = None) -> float:
    """Calculate completion rate for a sprint"""
    if db is None:
        db = next(get_db())

    query = select(DBSprint).where(DBSprint.id == sprint_id)
    result = await db.execute(query)
    sprint = result.scalar_one_or_none()
    
    if not sprint or not sprint.planned_points:
        return 0.0
    
    return (sprint.completed_points / sprint.planned_points) * 100

async def calculate_sprint_velocity(sprint_id: str, db: AsyncSession = None) -> float:
    """Calculate velocity for a specific sprint"""
    if db is None:
        db = next(get_db())

    query = select(DBSprint).where(DBSprint.id == sprint_id)
    result = await db.execute(query)
    sprint = result.scalar_one_or_none()
    
    if not sprint:
        return 0.0
    
    return float(sprint.completed_points)

async def generate_burndown_data(sprint_id: str, db: AsyncSession = None) -> Dict[str, List[float]]:
    """Generate burndown chart data for a sprint"""
    if db is None:
        db = next(get_db())

    query = select(DBSprint).where(DBSprint.id == sprint_id).options(
        selectinload(DBSprint.tasks)
    )
    result = await db.execute(query)
    sprint = result.scalar_one_or_none()
    
    if not sprint:
        return {
            "ideal": [],
            "actual": [],
            "dates": []
        }
    
    # Calculate sprint duration in days
    duration = (sprint.end_date - sprint.start_date).days + 1
    total_points = sprint.planned_points
    
    # Generate ideal burndown line
    ideal = [total_points * (1 - i/duration) for i in range(duration + 1)]
    
    # Calculate actual burndown based on task completion history
    actual = []
    dates = []
    remaining_points = total_points
    
    current_date = sprint.start_date
    while current_date <= sprint.end_date:
        # Find tasks completed on or before this date
        completed_points = sum(
            task.story_points
            for task in sprint.tasks
            if task.status == TaskStatus.DONE and task.updated_at.date() <= current_date
        )
        remaining_points = total_points - completed_points
        
        actual.append(remaining_points)
        dates.append(current_date.isoformat())
        current_date += timedelta(days=1)
    
    return {
        "ideal": ideal,
        "actual": actual,
        "dates": dates
    }

async def calculate_team_satisfaction(sprint_id: str, db: AsyncSession = None) -> float:
    """Calculate team satisfaction score for a sprint"""
    if db is None:
        db = next(get_db())

    query = select(DBSprint).where(DBSprint.id == sprint_id).options(
        selectinload(DBSprint.tasks)
    )
    result = await db.execute(query)
    sprint = result.scalar_one_or_none()
    
    if not sprint:
        return 0.0
    
    # Factors affecting team satisfaction:
    # 1. Sprint completion rate
    completion_rate = await calculate_completion_rate(sprint_id, db)
    
    # 2. Overtime work (based on task completion timestamps)
    overtime_penalty = 0.0
    for task in sprint.tasks:
        if task.status == TaskStatus.DONE:
            completion_hour = task.updated_at.hour
            if completion_hour >= 18:  # After 6 PM
                overtime_penalty += 0.5
    
    # 3. Task distribution (even distribution is better)
    assignee_counts = {}
    for task in sprint.tasks:
        assignee_counts[task.assignee_id] = assignee_counts.get(task.assignee_id, 0) + 1
    
    if assignee_counts:
        avg_tasks = sum(assignee_counts.values()) / len(assignee_counts)
        distribution_variance = sum(
            (count - avg_tasks) ** 2 
            for count in assignee_counts.values()
        ) / len(assignee_counts)
        distribution_score = 100 / (1 + distribution_variance)
    else:
        distribution_score = 0.0
    
    # Calculate final satisfaction score
    satisfaction = (
        completion_rate * 0.4 +
        (100 - min(overtime_penalty * 10, 100)) * 0.3 +
        distribution_score * 0.3
    )
    
    return max(0.0, min(100.0, satisfaction))

async def generate_summary_metrics(team_id: str, time_period: str, db: AsyncSession = None) -> Dict[str, Any]:
    """Generate summary metrics for a team"""
    if db is None:
        db = next(get_db())

    # Parse time period
    end_date = datetime.now().date()
    if time_period == "week":
        start_date = end_date - timedelta(days=7)
    elif time_period == "month":
        start_date = end_date - timedelta(days=30)
    elif time_period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:  # Default to last 30 days
        start_date = end_date - timedelta(days=30)
    
    metrics = {
        "velocity": await calculate_velocity(team_id, start_date, end_date, db),
        "quality": await calculate_quality_metrics(team_id, db),
        "efficiency": await calculate_efficiency_metrics(team_id, db),
        "completion_rate": await calculate_team_completion_rate(team_id, start_date, end_date, db)
    }
    
    return metrics

async def generate_detailed_metrics(team_id: str, time_period: str, db: AsyncSession = None) -> Dict[str, Any]:
    """Generate detailed metrics for a team"""
    if db is None:
        db = next(get_db())

    # Parse time period
    end_date = datetime.now().date()
    if time_period == "week":
        start_date = end_date - timedelta(days=7)
    elif time_period == "month":
        start_date = end_date - timedelta(days=30)
    elif time_period == "quarter":
        start_date = end_date - timedelta(days=90)
    else:  # Default to last 30 days
        start_date = end_date - timedelta(days=30)
    
    # Get all sprints in the time period
    query = select(DBSprint).where(
        DBSprint.team_id == team_id,
        DBSprint.start_date >= start_date,
        DBSprint.end_date <= end_date
    ).order_by(DBSprint.start_date)
    
    result = await db.execute(query)
    sprints = result.scalars().all()
    
    sprint_metrics = []
    for sprint in sprints:
        metrics = await calculate_sprint_metrics(sprint.id, db)
        sprint_metrics.append({
            "sprint_id": sprint.id,
            "name": sprint.name,
            "metrics": metrics
        })
    
    return {
        "sprints": sprint_metrics,
        "task_distribution": await calculate_task_distribution(team_id, start_date, end_date, db),
        "bottlenecks": await identify_bottlenecks(team_id, start_date, end_date, db),
        "risk_factors": await identify_risk_factors(team_id, db)
    }

async def generate_recommendations(team_id: str, db: AsyncSession = None) -> List[Dict[str, Any]]:
    """Generate recommendations based on team metrics"""
    if db is None:
        db = next(get_db())

    recommendations = []
    
    # Check velocity stability
    velocity_metrics = await calculate_velocity_stability(team_id, db)
    if velocity_metrics["variability"] > 25:  # More than 25% variation
        recommendations.append({
            "type": "velocity",
            "severity": "high",
            "message": "High velocity variability detected. Consider more consistent sprint planning.",
            "metrics": velocity_metrics
        })
    
    # Check quality metrics
    quality = await calculate_quality_metrics(team_id, db)
    if quality["bug_rate"] > 20:  # More than 20% bug rate
        recommendations.append({
            "type": "quality",
            "severity": "high",
            "message": "High bug rate detected. Consider increasing code review coverage.",
            "metrics": quality
        })
    
    # Check team health
    health = await calculate_team_health(team_id, db)
    if health["member_satisfaction"] < 70:  # Less than 70% satisfaction
        recommendations.append({
            "type": "health",
            "severity": "medium",
            "message": "Team satisfaction is below target. Consider team building activities.",
            "metrics": health
        })
    
    return recommendations

async def analyze_trends(team_id: str, time_period: str, db: AsyncSession = None) -> Dict[str, Any]:
    """Analyze trends in team metrics over time"""
    if db is None:
        db = next(get_db())

    # Parse time period
    end_date = datetime.now().date()
    if time_period == "week":
        start_date = end_date - timedelta(days=7)
        interval = "day"
    elif time_period == "month":
        start_date = end_date - timedelta(days=30)
        interval = "week"
    elif time_period == "quarter":
        start_date = end_date - timedelta(days=90)
        interval = "week"
    else:  # Default to last 30 days
        start_date = end_date - timedelta(days=30)
        interval = "week"
    
    # Get all completed tasks in the time period
    query = select(DBTask).where(
        DBTask.team_id == team_id,
        DBTask.status == TaskStatus.DONE,
        DBTask.updated_at >= start_date,
        DBTask.updated_at <= end_date
    ).order_by(DBTask.updated_at)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "velocity_trend": [],
            "quality_trend": [],
            "efficiency_trend": [],
            "dates": []
        }
    
    # Convert to pandas DataFrame for time series analysis
    df = pd.DataFrame([
        {
            "date": task.updated_at.date(),
            "story_points": task.story_points,
            "quality_score": await calculate_task_quality(task.id, db),
            "cycle_time": await calculate_cycle_time(task.id, db)
        }
        for task in tasks
    ])
    
    # Resample data based on interval
    if interval == "day":
        resampled = df.resample("D", on="date")
    else:
        resampled = df.resample("W", on="date")
    
    # Calculate trends
    velocity_trend = resampled["story_points"].sum().fillna(0).tolist()
    quality_trend = resampled["quality_score"].mean().fillna(0).tolist()
    efficiency_trend = (100 - resampled["cycle_time"].mean()).fillna(0).tolist()
    dates = [d.isoformat() for d in resampled.index.date]
    
    return {
        "velocity_trend": velocity_trend,
        "quality_trend": quality_trend,
        "efficiency_trend": efficiency_trend,
        "dates": dates
    }

async def calculate_team_completion_rate(
    team_id: str,
    start_date: date,
    end_date: date,
    db: AsyncSession = None
) -> float:
    """Calculate team's overall completion rate"""
    if db is None:
        db = next(get_db())

    query = select(DBSprint).where(
        DBSprint.team_id == team_id,
        DBSprint.start_date >= start_date,
        DBSprint.end_date <= end_date,
        DBSprint.status == SprintStatus.COMPLETED
    )
    
    result = await db.execute(query)
    sprints = result.scalars().all()
    
    if not sprints:
        return 0.0
    
    completion_rates = [
        sprint.completed_points / sprint.planned_points * 100
        if sprint.planned_points else 0
        for sprint in sprints
    ]
    
    return sum(completion_rates) / len(completion_rates)

async def calculate_task_distribution(
    team_id: str,
    start_date: date,
    end_date: date,
    db: AsyncSession = None
) -> Dict[str, Any]:
    """Calculate task distribution metrics"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(
        DBTask.team_id == team_id,
        DBTask.created_at >= start_date,
        DBTask.created_at <= end_date
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "by_type": {},
            "by_priority": {},
            "by_assignee": {}
        }
    
    # Distribution by type
    type_dist = {}
    for task in tasks:
        type_dist[task.type] = type_dist.get(task.type, 0) + 1
    
    # Distribution by priority
    priority_dist = {}
    for task in tasks:
        priority_dist[task.priority] = priority_dist.get(task.priority, 0) + 1
    
    # Distribution by assignee
    assignee_dist = {}
    for task in tasks:
        if task.assignee_id:
            assignee_dist[task.assignee_id] = assignee_dist.get(task.assignee_id, 0) + 1
    
    return {
        "by_type": type_dist,
        "by_priority": priority_dist,
        "by_assignee": assignee_dist
    }

async def identify_bottlenecks(
    team_id: str,
    start_date: date,
    end_date: date,
    db: AsyncSession = None
) -> List[Dict[str, Any]]:
    """Identify workflow bottlenecks"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(
        DBTask.team_id == team_id,
        DBTask.updated_at >= start_date,
        DBTask.updated_at <= end_date,
        DBTask.status == TaskStatus.DONE
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return []
    
    bottlenecks = []
    
    # Analyze time spent in each status
    status_times = {}
    for task in tasks:
        history = task.history or []
        status_changes = [
            h for h in history
            if h.get("field") == "status"
        ]
        
        for i in range(len(status_changes) - 1):
            status = status_changes[i]["new_value"]
            time_in_status = (
                datetime.fromisoformat(status_changes[i + 1]["timestamp"]) -
                datetime.fromisoformat(status_changes[i]["timestamp"])
            ).total_seconds() / 3600  # Convert to hours
            
            if status not in status_times:
                status_times[status] = []
            status_times[status].append(time_in_status)
    
    # Identify statuses with high average time
    for status, times in status_times.items():
        avg_time = sum(times) / len(times)
        if avg_time > 24:  # More than 24 hours in a status
            bottlenecks.append({
                "status": status,
                "average_time": avg_time,
                "affected_tasks": len(times),
                "severity": "high" if avg_time > 72 else "medium"
            })
    
    return sorted(bottlenecks, key=lambda x: x["average_time"], reverse=True)

async def identify_risk_factors(team_id: str, db: AsyncSession = None) -> List[Dict[str, Any]]:
    """Identify potential risk factors"""
    if db is None:
        db = next(get_db())

    risks = []
    
    # Check velocity stability
    velocity_metrics = await calculate_velocity_stability(team_id, db)
    if velocity_metrics["variability"] > 25:
        risks.append({
            "type": "velocity",
            "severity": "high",
            "description": "Unstable velocity indicates planning issues",
            "metrics": velocity_metrics
        })
    
    # Check task completion patterns
    completion_patterns = await analyze_completion_patterns(team_id, db)
    if completion_patterns["late_completion_rate"] > 30:
        risks.append({
            "type": "delivery",
            "severity": "high",
            "description": "High rate of late task completions",
            "metrics": completion_patterns
        })
    
    # Check team workload
    workload = await analyze_team_workload(team_id, db)
    if workload["overload_rate"] > 20:
        risks.append({
            "type": "workload",
            "severity": "medium",
            "description": "Team members showing signs of overload",
            "metrics": workload
        })
    
    return sorted(risks, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["severity"]], reverse=True)

async def calculate_velocity_stability(team_id: str, db: AsyncSession = None) -> Dict[str, float]:
    """Calculate velocity stability metrics"""
    if db is None:
        db = next(get_db())

    query = select(DBSprint).where(
        DBSprint.team_id == team_id,
        DBSprint.status == SprintStatus.COMPLETED
    ).order_by(DBSprint.end_date.desc()).limit(10)  # Last 10 sprints
    
    result = await db.execute(query)
    sprints = result.scalars().all()
    
    if not sprints:
        return {
            "average_velocity": 0.0,
            "variability": 0.0,
            "trend": 0.0
        }
    
    velocities = [sprint.completed_points for sprint in sprints]
    avg_velocity = sum(velocities) / len(velocities)
    
    # Calculate coefficient of variation (variability)
    if avg_velocity > 0:
        std_dev = np.std(velocities)
        variability = (std_dev / avg_velocity) * 100
    else:
        variability = 0.0
    
    # Calculate trend (positive means improving)
    if len(velocities) > 1:
        trend = (velocities[0] - velocities[-1]) / len(velocities)
    else:
        trend = 0.0
    
    return {
        "average_velocity": avg_velocity,
        "variability": variability,
        "trend": trend
    }

async def analyze_completion_patterns(team_id: str, db: AsyncSession = None) -> Dict[str, float]:
    """Analyze task completion patterns"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(
        DBTask.team_id == team_id,
        DBTask.status == TaskStatus.DONE
    ).order_by(DBTask.updated_at.desc()).limit(100)  # Last 100 tasks
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "late_completion_rate": 0.0,
            "average_delay": 0.0,
            "completion_predictability": 0.0
        }
    
    late_tasks = 0
    total_delay = timedelta()
    estimated_vs_actual = []
    
    for task in tasks:
        if task.due_date and task.updated_at.date() > task.due_date:
            late_tasks += 1
            total_delay += task.updated_at.date() - task.due_date
        
        if task.estimated_hours and task.actual_hours:
            estimated_vs_actual.append(task.actual_hours / task.estimated_hours)
    
    late_completion_rate = (late_tasks / len(tasks)) * 100
    average_delay = total_delay.days / late_tasks if late_tasks > 0 else 0
    
    # Calculate predictability (how close estimates are to actuals)
    if estimated_vs_actual:
        predictability = 100 - (abs(np.mean(estimated_vs_actual) - 1) * 100)
    else:
        predictability = 0.0
    
    return {
        "late_completion_rate": late_completion_rate,
        "average_delay": float(average_delay),
        "completion_predictability": predictability
    }

async def analyze_team_workload(team_id: str, db: AsyncSession = None) -> Dict[str, float]:
    """Analyze team workload distribution"""
    if db is None:
        db = next(get_db())

    query = select(DBTask).where(
        DBTask.team_id == team_id,
        DBTask.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.REVIEW])
    )
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    if not tasks:
        return {
            "average_load": 0.0,
            "overload_rate": 0.0,
            "load_distribution": 0.0
        }
    
    # Calculate workload per assignee
    assignee_loads = {}
    for task in tasks:
        if task.assignee_id:
            if task.assignee_id not in assignee_loads:
                assignee_loads[task.assignee_id] = 0
            assignee_loads[task.assignee_id] += task.story_points or 1
    
    if not assignee_loads:
        return {
            "average_load": 0.0,
            "overload_rate": 0.0,
            "load_distribution": 0.0
        }
    
    # Calculate metrics
    loads = list(assignee_loads.values())
    average_load = sum(loads) / len(loads)
    
    # Consider someone overloaded if they have more than 150% of average load
    overloaded = sum(1 for load in loads if load > average_load * 1.5)
    overload_rate = (overloaded / len(loads)) * 100
    
    # Calculate load distribution (coefficient of variation)
    if average_load > 0:
        std_dev = np.std(loads)
        load_distribution = (std_dev / average_load) * 100
    else:
        load_distribution = 0.0
    
    return {
        "average_load": average_load,
        "overload_rate": overload_rate,
        "load_distribution": load_distribution
    }