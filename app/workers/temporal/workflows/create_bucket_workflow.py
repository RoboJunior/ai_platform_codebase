from temporalio import workflow
from datetime import timedelta
from sqlalchemy.orm import Session

@workflow.defn()
class BucketCreationWorkFlow:
    @workflow.signal
    async def admin_approval(self, approved: bool):
        self.approval = approved

    @workflow.run
    async def create_new_bucket(self, bucket_name: str, team_name: str, team_id: int):
        self.approval = None

        # Wait for admin approval/rejection
        while self.approval is None:
            await workflow.wait_condition(lambda: self.approval is not None, timeout=timedelta(hours=24))

        # if the request is approved by the admin then create a bucket 
        if self.approval:
            # Added passthrough as its a external https to the minio client
            with workflow.unsafe.imports_passed_through():
                from ..activities.create_bucket_activity import create_bucket
                from app.db.session import get_db
                db = get_db()
                return await workflow.execute_activity(
                    create_bucket,
                    args=[team_name, bucket_name, team_id, db],
                    start_to_close_timeout=timedelta(seconds=30)
                )
        else:
            return "Bucket creation request was rejected"
