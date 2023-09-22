from asyncio.coroutines import _is_coroutine
from datetime import datetime, timedelta
from typing import Callable, Optional

from aiogram import Bot
from aiogram.methods import TelegramMethod
from apscheduler.job import Job
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from cherino.crud.jobstore import SqliteJobStore


SchedulerFunc = Callable | TelegramMethod


class TelegramMethodJob:
    """
    此类型的作用：
      1. 使 TelegramMethod 可以被 apscheduler 识别为异步函数
      2. 使 TelegramMethod 可以被序列化
    """
    _is_coroutine = _is_coroutine
    _bot = None

    def __init__(self, method: TelegramMethod):
        self.method = method
        # Bot 实例无法别序列化，这里需要删掉
        self.method._bot = None

    async def call(self):
        self.method._bot = TelegramMethodJob._bot
        return await self.method

    @classmethod
    def set_bot(cls, bot: Optional[Bot]):
        cls._bot = bot


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

    def run_single(
        self, func: SchedulerFunc, seconds: int, job_id: str, *args, **kwargs
    ):
        """
        若干秒后执行命令，如果已经存在相同 job_id 的任务，则立即运行前一个任务
        """
        self.trigger(job_id)
        self.run_after(func, seconds, job_id, *args, **kwargs)

    def run_after(
        self, func: SchedulerFunc, seconds: int, job_id: str, *args, **kwargs
    ):
        """
        若干秒后执行命令，如果已经存在相同 job_id 的任务，前一个任务会被取消
        """
        if isinstance(func, TelegramMethod):
            kwargs["jobstore"] = "sqlite"
            func = TelegramMethodJob(func).call
        if not kwargs.get("name"):
            kwargs["name"] = job_id
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
        if job := self.find(job_id):
            job.remove()

    def find(self, job_id: str) -> Optional[Job]:
        """
        查找任务
        """
        if job := self.scheduler.get_job(job_id):
            return job
        if job := self.scheduler.get_job(job_id, "sqlite"):
            return job

    def trigger(self, job_id: str):
        """
        立即触发任务
        """
        if job := self.find(job_id):
            job.reschedule(None)
