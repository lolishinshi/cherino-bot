from datetime import datetime, timedelta
from random import randint
from typing import Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.methods import TelegramMethod
from loguru import logger


class Scheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.run_after(logger.info, 1, "test-scheduler", args=("APScheduler 工作中",))

    @staticmethod
    def wrap_func(func: Callable | TelegramMethod):
        """
        TelegramMethod 是 awaitable 的，但是 apscheduler 只会根据 iscoroutinefunction 的结果来判断是否是异步函数
        """
        if isinstance(func, TelegramMethod):
            async def wrapper(*args, **kwargs):
                return await func
            return wrapper
        else:
            return func

    def run_single(self, func: Callable | TelegramMethod, seconds: int, job_id: str, *args, **kwargs):
        """
        若干秒后执行命令，如果已经存在相同 job_id 的任务，则立即运行前一个任务
        """
        func = self.wrap_func(func)
        for job in self.scheduler.get_jobs():
            if job.id.startswith(f"{job_id}:_CNT_:"):
                job.reschedule(None)
                self.scheduler.wakeup()
                break
        self.run_after(
            func, seconds, f"{job_id}:_CNT_:{randint(0, 2**32)}", *args, **kwargs
        )

    def run_after(self, func: Callable | TelegramMethod, seconds: int, job_id: str, *args, **kwargs):
        """
        若干秒后执行命令
        """
        func = self.wrap_func(func)
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