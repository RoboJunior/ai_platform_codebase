from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.services.notification_service import notification_manager, get_token_from_websocket
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
        
        await websocket.accept()
        await notification_manager.subscribe(topic_id, websocket)
        
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        notification_manager.unsubscribe(topic, websocket)
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
