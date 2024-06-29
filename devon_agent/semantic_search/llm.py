from dotenv import load_dotenv
import os
from litellm import acompletion
import asyncio


# Load environment variables from .env file
load_dotenv()

    
def code_explainer_and_summary_prompt(function_code, children_summaries):
    user_prompt = function_code + "\n" + "Here are the summaries for all the definitions:" + "\n" + children_summaries

    message = [{"content": f"""You are a code explainer, given a piece of code and summaries of its child functions or classes, you need to explain what the code is doing and is trying to achieve. Use code symbols, like variable names, function names, etc whenever you can while explaining. We purposely omitted some code If the code has the comment '# Code replaced for brevity. See node_id ..... ', so give us your best guess on what the whole code is trying to do using the summaries given of the definitions. Don't repeat the summaries.

Also give a summary. Mention what the code contains and what is the purpose. Use the summary of definitions if given. Have maximum of 3 lines

wrap the description in <description> tag and summary in <summary> tag
""", "role": "system"},
                {"content": f"{user_prompt}", "role": "user"}]
    
    return message

def code_explainer_and_summary_prompt_groq(function_code, children_summaries):
    user_prompt = function_code + "\n" + "Here are the summaries for all the definitions:" + "\n" + children_summaries

    message = [{"content": f"""You are a code explainer, given a piece of code and summaries of its child functions or classes, you need to explain what the code is doing and is trying to achieve. Use code symbols, like variable names, function names, etc whenever you can while explaining. We purposely omitted some code If the code has the comment '# Code replaced for brevity. See node_id ..... ', so give us your best guess on what the whole code is trying to do using the summaries given of the definitions. Don't repeat the summaries.""", "role": "system"},
                {"content": f"{user_prompt}", "role": "user"}]
    
    return message
# def file_summary_prompt(function_code):
#     message = [{"content": f"Mention the main class or functions and say what their purpose is. Dont mention about commented code. Have maximum of 3  Be as concise as possible", "role": "system"},
#                {"content": f"{function_code}", "role": "user"}]
    
#     return message    

def code_summary_prompt(function_code):
    message = [{"content": f"summarize what does the code trying to do. Dont mention about commented code. Do not have a summary more than 3 lines, but try to keep is less than 3. Be as concise as posible", "role": "system"},
               {"content": f"{function_code}", "role": "user"}]
    
    return message 

def directory_summary_prompt(directory_content):
    message = [{"content": f"In a really concise way, describe the role of the directory. ONLY 3 SENTENCES maximum. Don't have points", "role": "system"},
               {"content": f"{directory_content}", "role": "user"}]
    
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
    
async def get_completion_groq(messages, size = "small", model="llama-3-8b"):
    try:

        # if size == "small":
        try:
            response = await acompletion(
                model="groq/llama3-8b-8192",
                messages=messages,
                temperature=0.5,
                )
        except Exception as e:
            # print(e)
            raise e
        # else:
        #     response = await acompletion(
        #         model="claude-3-opus-20240229",
        #         messages=messages,
        #         temperature=0.5,
        #         max_tokens=4096
        #     )
 
        # Return the API response
        return response.choices[0].message['content']

    except Exception as e:
        # Handle errors that occur during the API request or processing
        # return {"error": str(e)}
        raise e


async def run_model_completion(model_name, prompt):
    if model_name == "groq":
        return await get_completion_groq(prompt, model="anthropic")
    else:
        return await get_completion(prompt)


async def main():
    # print(await get_completion_groq(code_explainer_prompt("""def _relate_constructor_calls(self, node_view, imports):
    #     for node_id, node_attrs in node_view:
    #         function_calls = node_attrs.get("function_calls")
    #         inherits = node_attrs.get("inheritances")
    #         if function_calls:
    #             function_calls_relations = self.__relate_function_calls(node_attrs, function_calls, imports)
    #             for relation in function_calls_relations:
    #                 self.graph.add_edge(relation["sourceId"], relation["targetId"], type=relation["type"])
    #         if inherits:
    #             inheritances_relations = self.__relate_inheritances(node_attrs, inherits, imports)
    #             for relation in inheritances_relations:
    #                 self.graph.add_edge(relation["sourceId"], relation["targetId"], type=relation["type"])""")))
    # print(await get_completion(code_summary_prompt(""""""), size="small"))
#     print(await run_model_completion("haiku", directory_summary_prompt("""test:
#   test1.py: The code contains a set of functions that perform various code analysis
#     tasks, including removing non-ASCII characters, traversing a syntax tree, extracting
#     function names, decomposing function calls, and identifying function calls and
#     class inheritances. The purpose of this code is to provide a set of utilities
#     for analyzing and processing code.
#   new.py: The code defines a `hello()` function that adds two variables and prints
#     the result. The actual implementation of the function has been omitted for brevity.
#   idk.py: The code defines a function `idk` that removes non-ASCII characters from
#     the input text using a regular expression. The purpose i)s to clean up the text
#     by removing any non-standard characters.""")))
    print(await run_model_completion("haiku", directory_summary_prompt("""test:
  test1.py: The code contains a set of functions that perform various code analysis
    tasks, including removing non-ASCII characters, traversing a syntax tree, extracting
    function names, decomposing function calls, and identifying function calls and
    class inheritances. The purpose of this code is to provide a set of utilities
    for analyzing and processing code.
  new.py: The code defines a `hello()` function that adds two variables and prints
    the result. The actual implementation of the function has been omitted for brevity.
  idk.py: The code defines a function `idk` that removes non-ASCII characters from
    the input text using a regular expression. The purpose i)s to clean up the text
    by removing any non-standard characters.""")))

if __name__ == "__main__":
    asyncio.run(main())


# message = [{'content': "You are a code explainer, given a piece of code, you need to explain what the code is doing and is trying to achieve. Use code symbols, like variable names, function names, etc whenever you can while explaining. We purposely omitted some code If the code has the comment '# Code replaced for brevity. See node_id ..... '.", 'role': 'system'}, {'content': 'import os\nimport uuid\n\nimport networkx as nx\nfrom blar_graph.graph_construction.languages.python.python_parser import PythonParser\nfrom blar_graph.graph_construction.utils import format_nodes\n\n\nclass GraphConstructor:\n    # Code replaced for brevity. See node_id 63e540a1-91b3-4f17-b687-f0b263eeebc2', 'role': 'user'}]
# async def main():
#     doc = await get_completion(message, model = "anthropic")
#     print(doc)

# asyncio.run(main())
