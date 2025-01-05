import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.exceptions import WorkflowAlreadyStartedError
from app.core.config import get_settings

class TemporalWorker:
    def __init__(self, task_queue: str, workflows: list, activities: list):
        self.task_queue = task_queue
        self.workflows = workflows
        self.activities = activities
        self.worker = None
        self.client = None

    async def create_client(self):
        # Connect to the Temporal server
        self.client = await Client.connect(get_settings().TEMPORAL_URL)
        return self.client

    async def start_worker(self):
        if self.client is None:
            await self.create_client()
        self.worker = Worker(self.client, task_queue=self.task_queue, workflows=self.workflows, activities=self.activities)
        await self.worker.run()

    async def stop_worker(self):
        # Gracefully stop the worker
        if self.worker:
            try:
                await self.worker.shutdown() # Gracefully stop the worker
            except WorkflowAlreadyStartedError:
                print("Worker already stopped.")