from typing import Dict, List
from fastapi import WebSocket, HTTPException
from app.core.config import get_settings
from temporalio.client import Client
import uuid
from sqlalchemy.orm import Session
from app.workers.temporal.workflows.app_notifications_workflow import AppNotificationsWorkflow
from app.db import models
import redis.asyncio as redis

# Create a redis client
redis_client = redis.Redis(host=get_settings().REDIS_HOST, port=get_settings().REDIS_PORT, decode_responses=True)

async def create_temporal_client():
    return await Client.connect(get_settings().TEMPORAL_URL)

async def start_app_notifications_workflow(topics: List[dict], message: str, db: Session):
    # get the user id and team id to insert into database
    user_id = next((d["user_id"] for d in topics if "user_id" in d), None)
    team_id = next((d["team_id"] for d in topics if "team_id" in d), None)
    
    # Convert topics to comma-separated string if it's a dict
    topics_str = ",".join(str(list(topic.values())[0]) for topic in topics)
    
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
    # Create a model to insert into notifications table
    notifications = models.Notifications(user_id=user_id, team_id=team_id, message=message)
    db.add(notifications)
    db.commit()
    
    return app_notification_workflow

async def get_token_from_websocket(websocket: WebSocket) -> str:
    auth_header = websocket.headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")
