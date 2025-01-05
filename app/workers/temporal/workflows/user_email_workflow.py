from temporalio import workflow
from datetime import timedelta

@workflow.defn
class UserEmailWorkflow:
    @workflow.run
    async def run(self, user_email: str):
        try:
            result = await workflow.execute_activity(
                "send_mail_to_user",
                user_email,
                start_to_close_timeout=timedelta(seconds=30)
            )
            return result
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")
            raise