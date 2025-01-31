from fastapi import FastAPI
from app.api.v1.api import api_router_v1
from app.workers.temporal.client import TemporalWorker
from app.workers.temporal.workflows.user_email_workflow import UserEmailWorkflow
from app.workers.temporal.activities.user_email_activity import handle_email_workflow
from app.workers.temporal.workflows.invitation_mail_workflow import InvitationEmailWorkflow
from app.workers.temporal.activities.invitation_mail_activity import send_invitation_mail_to_user
from app.workers.temporal.workflows.app_notifications_workflow import AppNotificationsWorkflow
from app.workers.temporal.activities.app_notifications_activity import send_app_notifications_to_user
import asyncio
from fastapi.middleware.cors import CORSMiddleware

# TODO do code cleanup in routes layer move all the bussiness logic to service file

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defining email workflow to send user email after logging in
user_email_worker = TemporalWorker(
    task_queue="user-email-task-queue", 
    workflows=[UserEmailWorkflow],
    activities=[handle_email_workflow]
)

# Defining invitation mail workflow to send user invitation email
invitation_mail_worker = TemporalWorker(
    task_queue="invitation-email-task-queue",
    workflows=[InvitationEmailWorkflow],
    activities=[send_invitation_mail_to_user]
)

# Defining notification service workflow to send user app notifications
app_notification_worker = TemporalWorker(
    task_queue="app-notification-task-queue",
    workflows=[AppNotificationsWorkflow],
    activities=[send_app_notifications_to_user]
)

@app.on_event("startup")
async def startup_event():
    # Start the email worker
    asyncio.create_task(user_email_worker.start_worker())
    asyncio.create_task(invitation_mail_worker.start_worker())
    asyncio.create_task(app_notification_worker.start_worker())

@app.on_event("shutdown")
async def shutdown_event():
    # Gracefully stop the workers on shutdown
    await user_email_worker.stop_worker()
    await invitation_mail_worker.stop_worker()
    await app_notification_worker.stop_worker()

@app.get("/")
def server_health():
    return {"message": "Server successfully running in port 8000"}

app.include_router(api_router_v1, prefix="/v1")