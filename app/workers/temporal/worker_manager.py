from .activities.app_notifications_activity import send_app_notifications_to_user
from .activities.user_email_activity import handle_email_workflow
from .activities.create_bucket_activity import create_bucket
from .workflows.app_notifications_workflow import AppNotificationsWorkflow
from .workflows.user_email_workflow import UserEmailWorkflow
from .workflows.create_bucket_workflow import BucketCreationWorkFlow
from temporalio.client import Client
from temporalio.worker import Worker
from app.core.config import get_settings

async def notification_worker():
    client = await Client.connect(get_settings().TEMPORAL_URL)
    worker = Worker(
        client, task_queue="app-notification-task-queue",
        workflows=[AppNotificationsWorkflow],
        activities=[send_app_notifications_to_user]
    )
    await worker.run()

async def email_worker():
    client = await Client.connect(get_settings().TEMPORAL_URL)
    worker = Worker(
        client, task_queue="user-email-task-queue",
        workflows=[UserEmailWorkflow],
        activities=[handle_email_workflow]
    )
    await worker.run()

async def create_bucket_worker():
    client = await Client.connect(get_settings().TEMPORAL_URL)
    worker = Worker(
        client, task_queue="bucket-creation-task-queue",
        workflows=[BucketCreationWorkFlow],
        activities=[create_bucket]
    )
    await worker.run()