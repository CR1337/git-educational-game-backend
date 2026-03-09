import os
import time
import psutil
import subprocess
from uuid import uuid4
from celery import Celery
from controllers.redis_controller import RedisController
from typing import Any, Callable, Dict, List, Optional


class _CeleryController:

    _NAME: str = "tasks"
    _SLEEP_DELAY: float = 0.1  # s
    _app: Celery
    _task_wrapper: Any
    _worker_processes: Dict[str, subprocess.Popen]

    def __init__(self):
        self._app = Celery(
            self._NAME,
            broker=f"redis://{RedisController.HOST}:{RedisController.PORT}/0",
            backend=f"redis://{RedisController.HOST}:{RedisController.PORT}/1",
        )
        
        @self._app.task
        def task_wrapper(*args, **kwargs) -> Dict[str, Any]:
            func: Callable = args[0]
            args = args[1:]
            return {
                "return_value": func(*args, **kwargs),
                "worker_pid": os.getpid()
            }
        
        self._task_wrapper = task_wrapper
        self._worker_processes = {}

    def _worker_is_ready(self, worker_name: str) -> bool:
        ping_result = self._app.control.ping()
        return any(
            key.startswith(worker_name) for key in ping_result
        )

    def run_task(self, func: Callable, *args, **kwargs) -> str:
        worker_name = str(uuid4())
        full_worker_name = f"worker_{worker_name}"
        queue_name = f"worker_{worker_name}_queue"
        worker_process = subprocess.Popen([
                "celery",
                "-A", self._NAME,
                "worker",
                "-n", f"worker_{worker_name}.%h",
                "-Q", f"worker_{worker_name}_queue",
                "--concurrency=1",
                "--prefetch-multiplier=1",
                "--loglevel=info"
        ])
        while not self._worker_is_ready(full_worker_name):
            time.sleep(self._SLEEP_DELAY)

        task = self._task_wrapper.apply_async(
            args=tuple([func] + list(args)), kwargs=kwargs,
            queue=queue_name
        )
        task_id = task.id
        self._worker_processes[task_id] = worker_process

        return task_id

    def task_is_ready(self, task_id: str) -> bool:
        return self._app.AsyncResult(task_id).ready()

    def get_task_result(self, task_id: str) -> Any:
        while not self.task_is_ready(task_id):
            time.sleep(self._SLEEP_DELAY)

        return self._app.AsyncResult(task_id).result
    
    def get_task_pid(self, task_id: str) -> Optional[int]:
        worker_process = self._worker_processes.get(task_id)
        if not worker_process:
            return None
        
        worker_pid = None
        result = self._app.AsyncResult(str(task_id))
        if result.ready():
            worker_pid = result.result.get("worker_pid")

        if not worker_pid:
            worker_pid = worker_process.pid
        
        return worker_pid

    def get_opened_files(self, task_id: str) -> List[str]:
        worker_process = self._worker_processes.get(task_id)
        if not worker_process:
            return []

        try:
            worker_pid = self.get_task_pid(task_id)

            process = psutil.Process(worker_pid)
    
            open_files = process.open_files()
            return [file.path for file in open_files if file.path]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return []

    
CeleryController = _CeleryController()
