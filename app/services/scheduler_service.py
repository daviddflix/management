from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
from typing import Optional, Dict, Any, Callable, Union, List
from datetime import datetime, timedelta
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class ScheduleType(str, Enum):
    CRON = "cron"
    INTERVAL = "interval"
    DATE = "date"

class JobStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    ERROR = "error"

class SchedulerConfig:
    """Configuration for the scheduler instance."""
    def __init__(
        self,
        timezone: str = "UTC",
        job_defaults: Optional[Dict[str, Any]] = None,
        max_instances: int = 3,
        executor_workers: int = 10
    ):
        self.timezone = timezone
        self.job_defaults = job_defaults or {
            'coalesce': True,
            'max_instances': max_instances,
            'misfire_grace_time': 30
        }
        self.executor_workers = executor_workers

class Pipeline:
    """Represents a scheduled pipeline with its configuration and status."""
    def __init__(
        self,
        func: Callable,
        schedule_type: ScheduleType,
        name: str,
        schedule_config: Dict[str, Any],
        description: Optional[str] = None,
        enabled: bool = True
    ):
        self.func = func
        self.schedule_type = schedule_type
        self.name = name
        self.schedule_config = schedule_config
        self.description = description
        self.enabled = enabled
        self.status = JobStatus.STOPPED
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.error_count: int = 0
        self.job: Optional[Job] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline to dictionary for API responses."""
        return {
            "name": self.name,
            "description": self.description,
            "schedule_type": self.schedule_type,
            "schedule_config": self.schedule_config,
            "enabled": self.enabled,
            "status": self.status,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "error_count": self.error_count
        }

class AsyncSchedulerService:
    """Async scheduler service for managing different types of pipelines."""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or SchedulerConfig()
        self.scheduler = AsyncIOScheduler(
            timezone=self.config.timezone,
            job_defaults=self.config.job_defaults
        )
        self.pipelines: Dict[str, Pipeline] = {}
        
    async def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started successfully")

    async def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler shut down successfully")

    def add_pipeline(self, pipeline: Pipeline) -> bool:
        """Add a new pipeline to the scheduler."""
        try:
            if pipeline.name in self.pipelines:
                logger.warning(f"Pipeline {pipeline.name} already exists")
                return False

            trigger = self._create_trigger(pipeline.schedule_type, pipeline.schedule_config)
            
            async def wrapped_func():
                try:
                    pipeline.status = JobStatus.RUNNING
                    pipeline.last_run = datetime.now()
                    await pipeline.func()
                    pipeline.error_count = 0
                except Exception as e:
                    pipeline.error_count += 1
                    pipeline.status = JobStatus.ERROR
                    logger.error(f"Error in pipeline {pipeline.name}: {str(e)}")
                    raise
                finally:
                    pipeline.status = JobStatus.RUNNING if pipeline.enabled else JobStatus.STOPPED
                    if pipeline.job:
                        pipeline.next_run = pipeline.job.next_run_time

            pipeline.job = self.scheduler.add_job(
                wrapped_func,
                trigger=trigger,
                id=pipeline.name,
                name=pipeline.name
            )
            
            self.pipelines[pipeline.name] = pipeline
            logger.info(f"Pipeline {pipeline.name} added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error adding pipeline {pipeline.name}: {str(e)}")
            return False

    def remove_pipeline(self, pipeline_name: str) -> bool:
        """Remove a pipeline from the scheduler."""
        try:
            if pipeline_name not in self.pipelines:
                return False
                
            pipeline = self.pipelines[pipeline_name]
            if pipeline.job:
                pipeline.job.remove()
            del self.pipelines[pipeline_name]
            logger.info(f"Pipeline {pipeline_name} removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error removing pipeline {pipeline_name}: {str(e)}")
            return False

    def pause_pipeline(self, pipeline_name: str) -> bool:
        """Pause a pipeline."""
        try:
            pipeline = self.pipelines.get(pipeline_name)
            if not pipeline or not pipeline.job:
                return False
                
            pipeline.job.pause()
            pipeline.status = JobStatus.PAUSED
            logger.info(f"Pipeline {pipeline_name} paused successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing pipeline {pipeline_name}: {str(e)}")
            return False

    def resume_pipeline(self, pipeline_name: str) -> bool:
        """Resume a paused pipeline."""
        try:
            pipeline = self.pipelines.get(pipeline_name)
            if not pipeline or not pipeline.job:
                return False
                
            pipeline.job.resume()
            pipeline.status = JobStatus.RUNNING
            logger.info(f"Pipeline {pipeline_name} resumed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming pipeline {pipeline_name}: {str(e)}")
            return False

    def get_pipeline_status(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a pipeline."""
        pipeline = self.pipelines.get(pipeline_name)
        return pipeline.to_dict() if pipeline else None

    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all registered pipelines and their status."""
        return [pipeline.to_dict() for pipeline in self.pipelines.values()]

    def _create_trigger(
        self,
        schedule_type: ScheduleType,
        config: Dict[str, Any]
    ) -> Union[CronTrigger, IntervalTrigger]:
        """Create a trigger based on schedule type and configuration."""
        if schedule_type == ScheduleType.CRON:
            return CronTrigger(**config)
        elif schedule_type == ScheduleType.INTERVAL:
            return IntervalTrigger(**config)
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")

# Create global instance
scheduler_service = AsyncSchedulerService()

# Example usage:
"""
# Create a pipeline for Monday.com task progress checking
async def check_monday_tasks():
    # Implementation here
    pass

pipeline = Pipeline(
    func=check_monday_tasks,
    schedule_type=ScheduleType.CRON,
    name="monday_task_progress",
    schedule_config={
        "hour": "*/4",  # Every 4 hours
        "minute": "0"
    },
    description="Check Monday.com task progress and send reports"
)

# Add pipeline to scheduler
await scheduler_service.add_pipeline(pipeline)

# Start the scheduler
await scheduler_service.start()
""" 