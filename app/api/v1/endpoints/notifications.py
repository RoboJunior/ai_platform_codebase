from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.services.notification_service import get_token_from_websocket, redis_client
from app.services.auth_service import get_current_user
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session
from app.db import models
from sqlalchemy import or_

notification_router = APIRouter()

@notification_router.websocket('/ws/{topic}/{topic_id}')
async def send_notification_to_user(
    websocket: WebSocket, 
    topic: str, 
    topic_id: str,
    db: Session = Depends(get_database_session)
):
    try:
        # Get token and verify user before accepting connection
        token = await get_token_from_websocket(websocket)
        current_user = get_current_user(token=token, db=db)

        if topic == "teams":
            # Check if the user is a member of the team
            is_member = db.query(models.Membership).filter(
                models.Membership.user_id == current_user.id,
                models.Membership.team_id == topic_id
            ).first()

            # Raising forbidden if the user is not part the team
            if not is_member:
                raise HTTPException(status_code=403, detail="User is not part of the team")
            
        if topic == "users":
            # Check if the user exist in the database
            user = db.query(models.User).filter(models.User.id == topic_id).first()

            # Rasing forbidden if the user is not found
            if not user:
                raise HTTPException(status_code=403, detail="User not found")
        
        await websocket.accept()
        # Subscribe to redis pub/sub service
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(topic_id)

        # Listen for messages from Redis and send them to the WebSocket
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])
        except WebSocketDisconnect:
            print(f"WebSocket disconnected for {topic_id}")
        finally:
            await pubsub.unsubscribe(topic_id)
            await pubsub.close()
            await websocket.close()

    except HTTPException as he:
        await websocket.close(code=4001, reason=str(he.detail))
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close(code=4000)
        raise HTTPException(status_code=403, detail="Credentials not found or invalid")
    
@notification_router.get('/get_all_notifications/{team_id}')
def get_all_notifications(team_id: int, db: Session = Depends(get_database_session), current_user: int = Depends(get_current_user)):
    # Check wheather the team exist or not
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="team does not exist")
    
    # Check if the user is a member of the team
    is_member = db.query(models.Membership).filter(
        models.Membership.user_id == current_user.id,
        models.Membership.team_id == team_id
    ).first()

    if not is_member:
        raise HTTPException(status_code=403, detail="User doesnt have access to view team notifications")
    
    return db.query(models.Notifications).filter(
        or_(
            models.Notifications.user_id == current_user.id,
            models.Notifications.team_id == team_id
        )
    ).all()
