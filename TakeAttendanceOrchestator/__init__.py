import azure.durable_functions as df
from datetime import timedelta

async def main(context: df.DurableOrchestrationContext):
    event_uid = context.get_input()

    retry_options = df.RetryOptions(5000, 3)

    while True:
        should_continue = await context.call_activity_with_retry(
            'CallLaravelApi', retry_options, event_uid
        )
        if not should_continue:
            break

        await context.create_timer(
            context.current_utc_datetime + timedelta(seconds=10)
        )

    return "Attendance task completed."