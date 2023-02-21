from random import randint
from typing import Callable
from datetime import datetime, timedelta
from loguru import logger

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.run_after(logger.info, 1, "test-scheduler", args=("APScheduler 工作中",))

    def run_single(self, func: Callable, seconds: int, job_id: str, *args, **kwargs):
        """
        若干秒后执行命令，如果已经存在相同 job_id 的任务，则立即运行前一个任务
        """
        for job in self.scheduler.get_jobs():
            if job.id.startswith(f"{job_id}:_CNT_:"):
                job.reschedule(None)
                self.scheduler.wakeup()
                break
        self.run_after(
            func, seconds, f"{job_id}:_CNT_:{randint(0, 2**32)}", *args, **kwargs
        )

    def run_after(self, func: Callable, seconds: int, job_id: str, *args, **kwargs):
        """
        若干秒后执行命令
        """
        self.scheduler.add_job(
            func,
            "date",
            run_date=datetime.now() + timedelta(seconds=seconds),
            id=job_id,
            replace_existing=True,
            *args,
            **kwargs,
        )

    def cancel(self, job_id: str):
        """
        取消任务
        """
        self.scheduler.remove_job(job_id)
