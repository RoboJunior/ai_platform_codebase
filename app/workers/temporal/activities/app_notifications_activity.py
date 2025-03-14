from temporalio import activity
from app.services.notification_service import redis_client

@activity.defn
async def send_app_notifications_to_user(topic: str , message: str):
    await redis_client.publish(topic, message)
    return message