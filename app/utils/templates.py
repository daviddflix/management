SPRINT_REPORT_TEMPLATE = """
# Sprint Report: {sprint_name}
## Overview
- Sprint Goal: {goal}
- Status: {status}
- Completion Rate: {completion_rate}%

## Metrics
- Velocity: {velocity} points
- Tasks Completed: {completed_tasks}/{total_tasks}
- Quality Score: {quality_score}

## Key Achievements
{achievements}

## Challenges & Risks
{challenges}

## Next Steps
{next_steps}

## Team Performance
{team_performance}
"""

KPI_REPORT_TEMPLATE = """
# Next Week KPIs
## Team Objectives
{objectives}

## Target Metrics
- Expected Velocity: {target_velocity}
- Quality Targets: {quality_targets}
- Delivery Goals: {delivery_goals}

## Focus Areas
{focus_areas}
"""

PROGRESS_REPORT_TEMPLATE = """
# Mid-Sprint Progress Report
## Current Status
- Sprint Progress: {progress}%
- Burndown Status: {burndown_status}

## Task Status
- Completed: {completed_tasks}
- In Progress: {in_progress_tasks}
- Blocked: {blocked_tasks}

## Risks & Mitigation
{risks_and_mitigation}

## Recommendations
{recommendations}
""" 