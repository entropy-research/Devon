from devon_agent.agents.default.agent import TaskAgent
from devon_agent.semantic_search.code_graph_manager import CodeGraphManager
from devon_agent.tool import Tool, ToolContext
from devon_agent.agents.model import AnthropicModel, ModelArguments, OpenAiModel
import chromadb.utils.embedding_functions as embedding_functions
import os

from devon_agent.utils import encode_path

class SemanticSearch(Tool):
    def __init__(self):
        self.temp_file_path = None
        self.messages = []  # Class variable to keep track of old messages

    @property
    def name(self):
        return "semantic_search"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        self.db_path = ctx["session"].db_path
        # self.vectorDB = chromadb.PersistentClient(path=os.path.join(self.base_path, "vectorDB"))
        self.vectorDB_path = os.path.join(self.db_path, "vectorDB")
        self.graph_path = os.path.join(self.db_path, "graph/graph.pickle")
        self.collection_name = ctx["session"].base_path
        self.manager = CodeGraphManager(self.graph_path, self.vectorDB_path, encode_path(ctx["session"].base_path) , os.environ.get("OPENAI_API_KEY"), ctx["session"].base_path)
        # self.manager.create_graph()
        
        
    def cleanup(self, ctx):
        try:
            self.manager.delete_collection(self.collection_name)
        except:
            pass
        pass

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """
    SEMANTIC_SEARCH(1)               General Commands Manual               SEMANTIC_SEARCH(1)

    NAME
            semantic_search - Ask a qustion regarding the codebase and get an answer. Use this especially when you want to understand how the codebase works.

    SYNOPSIS
            semantic_search QUERY_TEXT

    DESCRIPTION
            The semantic_search command performs a semantic search for the specified query within the code base.
            It uses a vector database to find and return relevant code snippets that match the query contextually.
            The relavent snippets are sent to a llm, while will then formulate an answer for you.
            Use this tool to get a better understanding of the codebase before executing a task.

    OPTIONS
            QUERY_TEXT
                    The query text to search within the code base.

    RETURN VALUE
            A string containing the final answer from the llm along with the paths to the code snippets

    EXAMPLES
            To search for how to create a new tool for the agent:

                    semantic_search "How do I create a new tool for the agent"
    """
            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, query_text: str) -> str:
        """
        command_name: semantic_search
        description: Performs a semantic search for the specified query within the code base.
        signature: semantic_search [QUERY_TEXT]
        example: `semantic_search "How do I create a new tool for the agent"`
        """

        # def format_response_for_llm(response):
        #     formatted_string = ""
        #     ids = response["ids"]
        #     documents = response["documents"]
        #     metadatas = response["metadatas"]
        #     for i in range(len(ids[0])):
        #         metadata = metadatas[0][i]
        #         document = documents[0][i]
        #         code = document.split("--code-- - \n")[1]
        #         formatted_string += f"path: {metadata.get('file_path')}\n"
        #         formatted_string += f"signature: {metadata.get('signature')}\n"
        #         formatted_string += f"start line: {metadata.get('start_line')}\n"
        #         formatted_string += f"end line: {metadata.get('end_line')}\n"
        #         formatted_string += f"code: \n{code}\n\n"
        #     return formatted_string

        try:
            agent : TaskAgent = ctx["session"].agent
            # model_args = ModelArguments(
            #     model_name=agent.args.model,
            #     temperature=0.5,
            #     api_key=agent.args.api_key
            # )
            opus = agent.current_model

            # Run the semantic search function
            # openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            #     api_key=os.environ.get("OPENAI_API_KEY"),
            #     model_name="text-embedding-ada-002"
            # )

            
            # collection_name = "devon-5"

            response = self.manager.query(query_text)
            # print(response)
            # print(asyncio.run(get_completion(agent_prompt(query_text, (response)), size="large")))


            # collection = self.vectorDB.get_collection("devon-5", openai_ef)
            # result = collection.query(query_texts=[query_text], n_results=10)

            # print(result)

            # formated_response = format_response_for_llm(result)

            # Add the new query and response to the messages
            self.messages.append({"content": f"The user's question: {query_text}\n\nOur tool's response: {response} \n\n Remember, be sure to give me relavent code snippets along with absolute file path while formulating an answer", "role": "user"})

            # Use all the messages in the LLM call
            response = opus.query(
                messages=self.messages,
                system_message="You are a senior software engineer who is expert in understanding large codebases. You are serving a user who asked a question about a codebase they have no idea about. We did semantic search with their question on the codebase through our tool and we are giving you the output of the tool. The tool's response will not be fully accurate. Only choose the code that looks right to you while formulating the answer. Your job is to frame the answer properly by looking at all the different code blocks and give a final answer. Your job is to make the user understand the new codebase, so whenever you are talking about an important part of the codebase mention the full file path and codesnippet, like the whole code of a small function or the relavent section of a large function, which will be given along with the code in the tool output"
            )

            # Append the assistant's response to the messages
            self.messages.append({"content": response, "role": "assistant"})
            
            return response
        
        except Exception as e:
            return str(e)
