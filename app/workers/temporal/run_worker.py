import asyncio
from .worker_manager import email_worker, notification_worker

async def run_worker():
    print("Starting Workers .....")
    await asyncio.gather(email_worker())
    await asyncio.gather(notification_worker())

if __name__ == "__main__":
    asyncio.run(run_worker())