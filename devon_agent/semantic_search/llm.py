from dotenv import load_dotenv
import os
from litellm import acompletion
import asyncio


# Load environment variables from .env file
load_dotenv()

def code_explainer_prompt(function_code):
    message = [{"content": f"You are a code explainer, given a piece of code, you need to explain what the code is doing and is trying to achieve. Use code symbols, like variable names, function names, etc whenever you can while explaining. We purposely omitted some code If the code has the comment '# Code replaced for brevity. See node_id ..... '.", "role": "system"},
                {"content": f"{function_code}", "role": "user"}]
    
    return message

def agent_prompt(question, tool_response):
    message = [{"content": f"You are a senior software engineer who is expert in understanding large codebases. You are serving a user who asked a question about a codebase they have no idea about. We did semantic search with their question on the codebase through our tool and we are giving you the output of the tool. The tool's response will not be fully accurate. Only choose the code that looks right to you while formulating the answer. Your job is to frame the answer properly by looking at all the different code blocks and give a final answer. Your job is to make the user understand the new codebase, so whenever you are talking about an important part of the codebase mention the full file path and codesnippet, like the whole code of a small function or the relavent section of a large function, which will be given along with the code in the tool output", "role": "system"},
                {"content": f"The user's question: {question}\n\nOur tool's response: {tool_response} \n\n Remember, be sure to give us relavent code snippets along with file path while formulating an answer", "role": "user"}]
    
    return message

async def get_completion(messages, size = "small", model="anthropic"):
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
            if size == "small":
                response = await acompletion(
                    model="claude-3-haiku-20240307",
                    messages=messages,
                    temperature=0.5,
                )
            else:
                response = await acompletion(
                    model="claude-3-opus-20240229",
                    messages=messages,
                    temperature=0.5,
                    max_tokens=4096
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



async def main():
    print(await get_completion(agent_prompt("How do I create a new tool for the agent", """"""), size="large"))

if __name__ == "__main__":
    asyncio.run(main())


# message = [{'content': "You are a code explainer, given a piece of code, you need to explain what the code is doing and is trying to achieve. Use code symbols, like variable names, function names, etc whenever you can while explaining. We purposely omitted some code If the code has the comment '# Code replaced for brevity. See node_id ..... '.", 'role': 'system'}, {'content': 'import os\nimport uuid\n\nimport networkx as nx\nfrom blar_graph.graph_construction.languages.python.python_parser import PythonParser\nfrom blar_graph.graph_construction.utils import format_nodes\n\n\nclass GraphConstructor:\n    # Code replaced for brevity. See node_id 63e540a1-91b3-4f17-b687-f0b263eeebc2', 'role': 'user'}]
# async def main():
#     doc = await get_completion(message, model = "anthropic")
#     print(doc)

# asyncio.run(main())