from .registry import ability

@ability(
    name="finish",
    description="Use this to shut down once you have accomplished all of your goals,"
    " or when there are insurmountable problems that make it impossible"
    " for you to finish your task.",
    parameters=[
        {
            "name": "reason",
            "description": "A summary to the user of how the goals were accomplished",
            "type": "string",
            "required": True,
        }
    ],
    output_type="None",
)
async def finish(
    agent,
    task_id: str,
    reason: str,
) -> str:

    print("shutting down")
    return reason
