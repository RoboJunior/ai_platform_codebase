from temporalio import workflow
from datetime import timedelta

@workflow.defn
class UserEmailWorkflow:
    @workflow.run
    async def run(self, email_addresses_str: str, subject: str, html_content: str):
        try:
            # convert email addresses back to a list
            email_addresses = email_addresses_str.split(',')

            results = []
            for email_address in email_addresses:
                result = await workflow.execute_activity(
                    "handle_email_workflow",
                    args=[email_address, subject, html_content],
                    start_to_close_timeout=timedelta(seconds=30)
                )
                if result:
                    results.append(result)

            return results if results else ["No emails sent"]
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {e}")
            raise
