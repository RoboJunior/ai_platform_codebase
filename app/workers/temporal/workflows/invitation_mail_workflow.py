from temporalio import workflow
from datetime import timedelta

@workflow.defn
class InvitationEmailWorkflow:
    @workflow.run
    async def run(self, user_email: str, team_name: str, team_code: str):
        try:
            result = await workflow.execute_activity(
                "send_invitation_mail_to_user",
                args=(user_email, team_name, team_code),
                start_to_close_timeout=timedelta(seconds=30),
            )
            return result
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")
            raise
