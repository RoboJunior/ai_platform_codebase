from temporalio import workflow
from datetime import timedelta
from typing import List, Union

@workflow.defn
class AppNotificationsWorkflow:
    @workflow.run
    async def run(self, topics_str: str, message: str) -> List[str]:
        try:
            # Split topics back into a list
            topics = [t.strip() for t in topics_str.split(",")]
            
            results = []
            for topic in topics:
                if topic:  # Skip empty topics
                    result = await workflow.execute_activity(
                        "send_app_notifications_to_user",
                        args=[topic, message],  # Pass as list instead of tuple
                        start_to_close_timeout=timedelta(seconds=30)
                    )
                    if result:
                        results.append(result)
            
            return results if results else ["No notifications sent"]
            
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {str(e)}")
            return [f"Error: {str(e)}"]
