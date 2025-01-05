from fastapi import APIRouter
from .endpoints import users
from .endpoints import auth
from .endpoints import teams
from .endpoints import notifications

api_router_v1 = APIRouter()

api_router_v1.include_router(users.user_router, prefix="/users", tags=["Users"])
api_router_v1.include_router(auth.auth_router, prefix='/auth', tags=["Authentication"])
api_router_v1.include_router(teams.team_router, prefix='/teams', tags=['Teams'])
api_router_v1.include_router(notifications.notification_router, prefix="/notifications", tags=['Notifications'])