from typing import Callable
from random import randint
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    def run_after(self, func: Callable, seconds: int, job_id: str, *args, **kwargs):
        """
        若干秒后执行命令，如果已经存在相同 job_id 的任务，则立即运行前一个任务
        """
        if old_job := self.scheduler.get_job(job_id):
            old_job.reschedule(None)

        self.scheduler.add_job(
            func,
            "date",
            run_date=datetime.now() + timedelta(seconds=seconds),
            id=job_id,
            *args,
            **kwargs,
        )

    def cancel(self, job_id: str):
        """
        取消任务
        """
        self.scheduler.remove_job(job_id)
