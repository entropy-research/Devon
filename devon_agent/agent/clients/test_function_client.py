from devon_agent.agent.clients.client import GPT4, Message
from devon_agent.agent.clients.tool_utils.tools import Tool, Toolbox

from pydantic import Field
from openai import OpenAI
import json

def get_n_day_weather_forecast(
    location: str = Field(..., description="The city and state, e.g. San Francisco, CA"),
    format: str = Field("celsius", description="The temperature unit to use. Infer this from the user's location."),
    num_days: int = Field(..., description="The number of days to forecast")
) -> str:
    """Get an N-day weather forecast"""
    # Placeholder implementation
    return json.dumps({"location": location, "format": format, "num_days": num_days, "forecast": "Sunny"})

if __name__ == "__main__":
    client = OpenAI()

    model = GPT4(client, system_message="You are a helpful assistant", max_tokens=1000, tools_enabled=True)

    tool_bank = Toolbox()
    tool_bank.add_tool(
        Tool.from_function(
            function=get_n_day_weather_forecast,
            name="get_n_day_weather_forecast",
            description="Get an N-day weather forecast",
        )
    )

    message, tool_calls = model.chat(messages=[
            Message(role="user", content="What's the weather like in San Francisco, Tokyo, and Paris?")
        ],
        tools=tool_bank
    )

    tool_results = tool_bank.execute_tool_calls(tool_calls)

    print(tool_results)