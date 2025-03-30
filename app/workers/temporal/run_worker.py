import asyncio
from .worker_manager import email_worker, notification_worker, create_bucket_worker

async def run_worker():
    print("Starting Workers .....")
    await asyncio.gather(notification_worker(), email_worker(), create_bucket_worker())

if __name__ == "__main__":
    asyncio.run(run_worker())