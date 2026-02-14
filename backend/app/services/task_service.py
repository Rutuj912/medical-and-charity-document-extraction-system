from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json

from app.config import get_logger, settings
from app.utils.exceptions import TaskException, TaskNotFoundError, TaskCreationError

logger = get_logger(__name__)


class TaskService:
    def __init__(self):
        self.logger = logger
        self.tasks_dir = settings.get_absolute_path(settings.JSON_TASKS_DIR)

    async def create_task(
        self,
        task_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        self.logger.info(
            "Task creation requested",
            task_id=task_id
        )

        raise NotImplementedError("Task creation will be implemented in Steps 6-7")

    async def save_task_output(
        self,
        task_id: str,
        output_data: Dict[str, Any],
        filename: str = "output.json"
    ) -> Path:
        self.logger.info(
            "Task output save requested",
            task_id=task_id,
            filename=filename
        )

        raise NotImplementedError("Task output saving will be implemented in Steps 6-7")

    async def get_task_status(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        self.logger.info(
            "Task status query",
            task_id=task_id
        )

        raise NotImplementedError("Task status will be implemented in Steps 6-7")

    async def list_tasks(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        self.logger.info(
            "Task listing requested",
            limit=limit,
            offset=offset
        )

        raise NotImplementedError("Task listing will be implemented in Steps 6-7")

    async def delete_task(
        self,
        task_id: str
    ) -> bool:
        self.logger.info(
            "Task deletion requested",
            task_id=task_id
        )

        raise NotImplementedError("Task deletion will be implemented in Steps 6-7")

    async def cleanup_old_tasks(
        self,
        days: int = 30
    ) -> int:
        self.logger.info(
            "Task cleanup requested",
            days=days
        )

        raise NotImplementedError("Task cleanup will be implemented in Step 7")
