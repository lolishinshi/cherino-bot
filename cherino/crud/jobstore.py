import pickle

from peewee import IntegrityError
from apscheduler.jobstores.base import BaseJobStore, ConflictingIdError, JobLookupError
from apscheduler.job import Job
from apscheduler.util import datetime_to_utc_timestamp, utc_timestamp_to_datetime
from loguru import logger

from cherino.database.models.jobstore import JobStore


class SqliteJobStore(BaseJobStore):
    def _reconstitute_job(self, job_state):
        job_state = pickle.loads(job_state)
        job_state["jobstore"] = self
        job = Job.__new__(Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job

    def _get_jobs(self, *conditions):
        jobs = []
        job_stores = (
            JobStore.select().where(*conditions).order_by(JobStore.next_run_time)
        )
        failed_job_ids = set()

        for row in job_stores:
            try:
                jobs.append(self._reconstitute_job(row.job_state))
            except BaseException:
                logger.exception('Unable to restore job "%s" -- removing it', row.id)
                failed_job_ids.add(row.id)

        # Remove all the jobs we failed to restore
        if failed_job_ids:
            JobStore.delete().where(JobStore.id.in_(failed_job_ids))

        return jobs

    def lookup_job(self, job_id):
        if job_store := JobStore.get_or_none(JobStore.id == job_id).execute():
            return self._reconstitute_job(job_store)

    def get_due_jobs(self, now):
        timestamp = datetime_to_utc_timestamp(now)
        return self._get_jobs(JobStore.next_run_time <= timestamp)

    def get_next_run_time(self):
        jobstore = (
            JobStore.select(JobStore.next_run_time)
            .where(JobStore.next_run_time.is_null(False))
            .order_by(JobStore.next_run_time)
            .limit(1)
            .get_or_none()
        )
        if jobstore:
            return utc_timestamp_to_datetime(jobstore.next_run_time)

    def get_all_jobs(self):
        jobs = self._get_jobs()
        self._fix_paused_jobs_sorting(jobs)
        return jobs

    def add_job(self, job):
        insert = JobStore.insert(
            id=job.id,
            next_run_time=datetime_to_utc_timestamp(job.next_run_time),
            job_state=pickle.dumps(job.__getstate__(), pickle.HIGHEST_PROTOCOL),
        )
        try:
            insert.execute()
        except IntegrityError:
            raise ConflictingIdError(job.id)

    def update_job(self, job):
        rowcount = (
            JobStore.update(
                {
                    "next_run_time": datetime_to_utc_timestamp(job.next_run_time),
                    "job_state": pickle.dumps(
                        job.__getstate__(), pickle.HIGHEST_PROTOCOL
                    ),
                }
            )
            .where(JobStore.id == job.id)
            .execute()
        )

        if rowcount == 0:
            raise JobLookupError(job.id)

    def remove_job(self, job_id):
        rowcount = JobStore.delete().where(JobStore.id == job_id).execute()
        if rowcount == 0:
            raise JobLookupError(job_id)

    def remove_all_jobs(self):
        JobStore.delete().execute()
