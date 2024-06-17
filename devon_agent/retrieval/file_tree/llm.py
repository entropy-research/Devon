from dotenv import load_dotenv
import os
from litellm import acompletion

# Load environment variables from .env file
load_dotenv()

async def get_completion(messages, model="openai"):
    try:
        # Retrieve API keys from environment variables
        openai_api_key = os.getenv("OPENAI_API_KEY")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # Determine the model to use based on available API keys
        if model == "openai" and not openai_api_key:
            model = "anthropic" if anthropic_api_key else None
        elif model == "anthropic" and not anthropic_api_key:
            model = "openai" if openai_api_key else None

        if model == "openai":
            os.environ["OPENAI_API_KEY"] = openai_api_key
            response = await acompletion(
                model="gpt-4o",
                messages=messages
            )
        elif model == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
            response = await acompletion(
                model="claude-3-sonnet-20240229",
                messages=messages
            )
        else:
            raise ValueError("Invalid model specified and no valid API keys found.")

        # Return the API response
        return response.choices[0].message['content']

    except Exception as e:
        # Handle errors that occur during the API request or processing
        return {"error": str(e)}
    
# Example usage of the function with message objects (requires an async context)
example_messages = [
    {"role": "user", "content": "Hello, how are you?"}
]

# async def main():
#     response = await get_completion(example_messages)
#     print(response)

# asyncio.run(main())
