from fastapi import FastAPI
from app.api.v1.api import api_router_v1
import asyncio
from fastapi.middleware.cors import CORSMiddleware

# TODO write the cleanup logic for cleaning up otp's using temporlio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def server_health():
    return {"message": "Server successfully running in port 8000"}

app.include_router(api_router_v1, prefix="/v1")