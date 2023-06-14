from asyncio.coroutines import _is_coroutine
from datetime import datetime, timedelta
from random import randint
from typing import Callable

from aiogram.methods import TelegramMethod
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from cherino.crud.jobstore import SqliteJobStore


SchedulerFunc = Callable | TelegramMethod


class TelegramMethodWrapper:
    _is_coroutine = _is_coroutine

    def __init__(self, method: TelegramMethod):
        self.method = method

    async def call(self):
        return await self.method


class Scheduler:
    jobstores = {
        "sqlite": SqliteJobStore(),
        "default": MemoryJobStore(),
    }
    job_defaults = {
        "misfire_grace_time": 15 * 60,
    }

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            jobstores=self.jobstores, job_defaults=self.job_defaults
        )
        self.scheduler.start()
        self.run_after(logger.info, 1, "test-scheduler", args=("APScheduler 工作中",))

    @staticmethod
    def _wrap_func(func: SchedulerFunc):
        """
        TelegramMethod 是 awaitable 的，但是 apscheduler 只会根据 iscoroutinefunction 的结果来判断是否是异步函数
        """
        if isinstance(func, TelegramMethod):
            return TelegramMethodWrapper(func)
        else:
            return func

    def run_single(
        self, func: SchedulerFunc, seconds: int, job_id: str, *args, **kwargs
    ):
        """
        若干秒后执行命令，如果已经存在相同 job_id 的任务，则立即运行前一个任务
        """
        for job in self.scheduler.get_jobs():
            if job.id.startswith(f"{job_id}:_CNT_:"):
                job.reschedule(None)
                break
        self.run_after(
            func, seconds, f"{job_id}:_CNT_:{randint(0, 2**32)}", *args, **kwargs
        )

    def run_after(
        self, func: SchedulerFunc, seconds: int, job_id: str, *args, **kwargs
    ):
        """
        若干秒后执行命令，如果已经存在相同 job_id 的任务，前一个任务会被取消
        """
        if isinstance(func, TelegramMethod):
            kwargs["jobstore"] = "sqlite"
            func = TelegramMethodWrapper(func).call
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
        try:
            self.scheduler.remove_job(job_id)
        except JobLookupError:
            pass

    def trigger(self, job_id: str):
        """
        立即触发任务
        """
        if job := self.scheduler.get_job(job_id):
            job.reschedule(None)
        else:
            for job in self.scheduler.get_jobs():
                if job.id.startswith(f"{job_id}:_CNT_:"):
                    job.reschedule(None)
                    return
