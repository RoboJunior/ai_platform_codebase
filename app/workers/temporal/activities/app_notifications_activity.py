from temporalio import activity
from app.services.notification_service import notification_manager

@activity.defn
async def send_app_notifications_to_user(topic: str , message: str):
    await notification_manager.notify(topic, message)