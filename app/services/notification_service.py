from typing import Dict, List, Union
from fastapi import WebSocket
from app.core.config import get_settings
from temporalio.client import Client
import uuid
from app.workers.temporal.workflows.app_notifications_workflow import AppNotificationsWorkflow


class NotificationManager:
    def __init__(self):
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def subscribe(self, topic: str, websocket: WebSocket):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(websocket)

    def unsubscribe(self, topic: str, websocket: WebSocket):
        if topic in self.subscriptions:
            self.subscriptions[topic].remove(websocket)

    async def notify(self, topic: str, message: str):
        if topic in self.subscriptions:
            for websocket in self.subscriptions[topic]:
                try:
                    await websocket.send_text(message)
                except Exception:
                    self.unsubscribe(topic, websocket)

async def create_temporal_client():
    return await Client.connect(get_settings().TEMPORAL_URL)

async def start_app_notifications_workflow(topics: Union[str, List[str]], message: str):
    # Convert topics to comma-separated string if it's a list
    topics_str = topics if isinstance(topics, str) else ",".join(topics)
    
    # Basic validation
    if not topics_str or not message:
        raise ValueError("Both topics and message are required")
    
    task_id = uuid.uuid4().hex
    client = await create_temporal_client()
    
    app_notification_workflow = await client.execute_workflow(
        AppNotificationsWorkflow.run,
        id=task_id,
        task_queue="app-notification-task-queue",
        args=[topics_str, message]  # Pass as simple strings
    )
    return app_notification_workflow

notification_manager = NotificationManager()