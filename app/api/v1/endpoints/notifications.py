from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from app.services.notification_service import notification_manager
from app.services.auth_service import get_current_user
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_database_session

notification_router = APIRouter()

async def get_token_from_websocket(websocket: WebSocket) -> str:
    auth_header = websocket.headers.get('authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@notification_router.websocket('/ws/{topic}')
async def send_notification_to_user(
    websocket: WebSocket, 
    topic: str, 
    db: Session = Depends(get_database_session)
):
    try:
        # Get token and verify user before accepting connection
        token = await get_token_from_websocket(websocket)
        current_user = get_current_user(token=token, db=db)
        
        await websocket.accept()
        await notification_manager.subscribe(topic, websocket)
        
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