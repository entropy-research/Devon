import anyio
import uuid
import networkx as nx
# import chromadb
import asyncio
import tiktoken
from devon_agent.semantic_search.graph_construction.core.graph_builder import GraphConstructor
from devon_agent.semantic_search.graph_traversal.encode_codegraph import (generate_doc_level_wise)
from devon_agent.semantic_search.graph_traversal.value_extractor import (extract_chromadb_values)
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv
import os

class CodeGraphManager:
    def __init__(self, graph_storage_path, db_path, root_path, openai_api_key, api_key, model_name, collection_name):
        if not openai_api_key:
            raise ValueError("OpenAI API key is missing.")
        if not api_key:
            raise ValueError("API key is missing.")
        if model_name not in ["haiku", "groq"]:
            raise ValueError("Unsupported model. Only 'haiku' and 'groq' are supported.")
        
        self.graph_storage_path = graph_storage_path
        self.db_path = db_path
        self.root_path = root_path
        self.openai_api_key = openai_api_key
        self.api_key = api_key
        self.model_name = model_name
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_api_key,
            model_name="text-embedding-ada-002"
        )
        self.collection_name = collection_name
        self.languages = []
        self.ignore_dirs = []
        self.db_client = None
        

    def detect_languages(self):
        try:
            extensions = set()
            ignored_paths = set()

            def traverse_directory(path, ignored_paths):
                if not os.path.exists(path):
                    return
                gitignore_path = os.path.join(path, ".gitignore")
                if os.path.exists(gitignore_path):
                    with open(gitignore_path, "r") as gitignore_file:
                        for line in gitignore_file:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                normalized_path = os.path.normpath(line)
                                absolute_path = os.path.abspath(os.path.join(path, normalized_path))
                                ignored_paths.add(absolute_path)

                for entry in os.scandir(path):
                    if entry.name.startswith(".") or os.path.abspath(entry.path) in ignored_paths:
                        continue
                    if entry.is_file():
                        ext = os.path.splitext(entry.name)[1]
                        if ext:
                            extensions.add(ext)
                    elif entry.is_dir():
                        traverse_directory(entry.path, ignored_paths)

            traverse_directory(self.root_path, ignored_paths)
            self.languages = list({extension_to_language.get(ext) for ext in extensions if extension_to_language.get(ext)})
            print("Detected languages:", self.languages)
        
        except Exception as e:
            print(f"An error occurred while detecting languages: {e}")
            raise

    def create_graph(self):
        if not self.root_path:
            raise ValueError("Root path is not provided")

        # Ensure the database path exists
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
            print(f"Created database directory at {self.db_path}")

        # Initialize the database client
        if self.db_client is None:
            self.db_client = chromadb.PersistentClient(path=self.db_path)

        self.detect_languages()

        for language in self.languages:
            print(f"Building graph for {language}")
            try:
                graph_path = os.path.join(self.graph_storage_path, f"{language}_graph.pickle")
                hash_path = os.path.join(self.graph_storage_path, f"{language}_hashes.json")

                # Check if collection exists
                try:
                    collection = self.db_client.get_collection(name=self.collection_name, embedding_function=self.openai_ef)
                    collection_exists = True
                except ValueError:
                    print("Vector Collection not found")
                    # collection = self.db_client.create_collection(name=self.collection_name, embedding_function=self.openai_ef)
                    collection_exists = False
                    # print("Collection created.")

                # Determine if we need to create a new graph or update the existing one
                graph_exists = os.path.exists(graph_path)
                hash_exists = os.path.exists(hash_path)
                create_new_graph = not collection_exists or not graph_exists or not hash_exists

                # If the collection exists but the graph or hash does not, clear the collection
                if collection_exists and create_new_graph:
                    print(f"Graph or hash does not exist. Clearing all the entries for {language} in the collection.")
                    collection.delete(where={"lang" : language})
                   

                # Initialize the graph constructor
                self.graph_constructor = GraphConstructor(
                    language,
                    self.root_path,
                    self.graph_storage_path,
                    not create_new_graph,  # Pass False to create new graph if needed
                    ignore_dirs=["__pycache__"]
                )

                # Build or update the graph and get the actions list
                actions, current_hashes = self.graph_constructor.build_or_update_graph()

                print(actions)

                # Generate documentation for the updated graph
                generate_doc_level_wise(self.graph_constructor.graph, actions, model_name=self.model_name)

                # Update the collection
                self.update_collection(actions, language)

                # Save the updated graph and hashes
                self.graph_constructor.save_graph(graph_path)
                self.graph_constructor.save_hashes(hash_path, current_hashes)

            except ValueError as e:
                print(f"Error: {e}. Language {language} is not supported.")
            except Exception as e:
                print(f"An unexpected error occurred while building the graph for {language}: {e}")



    def update_collection(self, actions, language):
        try:
            collection_name = self.collection_name

            # Get or create the collection
            try:
                collection = self.db_client.get_collection(name=collection_name, embedding_function=self.openai_ef)
            except ValueError:
                print("Collection not found, creating a new one.")
                collection = self.db_client.create_collection(name=collection_name, embedding_function=self.openai_ef)
                print("Collection created.")

            # Helper function to count tokens
            def count_tokens(text: str) -> int:
                encoding = tiktoken.get_encoding("cl100k_base")
                num_tokens = len(encoding.encode(text))
                return num_tokens

            # Helper function to split nodes by token count
            def split_nodes(node_id, doc, code, node_data):
                combined_text = f"documentation - \n{doc} \n--code-- - \n{code}"
                if count_tokens(combined_text) > 8000:
                    doc_metadata = {"split_type": "documentation", **node_data}
                    code_metadata = {"split_type": "code", **node_data}

                    doc_id = f"{node_id}-doc"
                    code_id = f"{node_id}-code"

                    docs = [doc, code]
                    ids = [doc_id, code_id]
                    metadatas = [doc_metadata, code_metadata]
                else:
                    docs = [combined_text]
                    ids = [node_id]
                    metadatas = [node_data]

                return ids, docs, metadatas

            # Helper function to find node_id by file_path using parent_node_id
            def find_node_id_by_file_path(parent_node_id, file_path):
                for child in self.graph_constructor.graph.successors(parent_node_id):
                    if self.graph_constructor.graph.nodes[child].get("file_path") == file_path:
                        return child
                return None

            # Helper function to process node and its children
            def process_node_recursively(node_id):
                print("node getting added", node_id)
                node_data = self.graph_constructor.graph.nodes[node_id]
                code = node_data.get("text", "")
                doc = node_data.get("doc", "")
                metadata = {
                    "type": node_data.get("type", ""),
                    "name": node_data.get("name", ""),
                    "file_path": node_data.get("file_path", ""),
                    "start_line": node_data.get("start_line", ""),
                    "end_line": node_data.get("end_line", ""),
                    "node_id": node_data.get("node_id", ""),
                    "file_node_id": node_data.get("file_node_id", ""),
                    "signature": node_data.get("signature", ""),
                    "leaf": node_data.get("leaf", ""),
                    "lang": language
                }

                if metadata is None:
                    metadata = {}

                ids, docs, metadatas = split_nodes(node_id, doc, code, metadata)
                all_ids.extend(ids)
                all_docs.extend(docs)
                all_metadatas.extend(metadatas)

                for child in self.graph_constructor.graph.successors(node_id):
                    process_node_recursively(child)

            # Process delete actions
            for file_path, parent_node_id in actions["delete"]:
                print("deleting nodes from", file_path)
                collection.delete(where={"file_path": file_path})

            # Delete nodes that are going to be updated
            for file_path, parent_node_id in actions["update"]:
                print("deleting nodes from", file_path)
                collection.delete(where={"file_path": file_path})

            # Collect all nodes to be added or updated
            all_ids = []
            all_docs = []
            all_metadatas = []

            for file_path, parent_node_id in actions["add"] + actions["update"]:
                node_id = find_node_id_by_file_path(parent_node_id, file_path)
                if not node_id:
                    print(f"No node found for file path: {file_path}")
                    continue

                process_node_recursively(node_id)

            # Generate embeddings for all documents at once
            if all_docs:
                embeddings = self.openai_ef(all_docs)
                # Add all nodes to the collection
                # print(all_metadatas)
                collection.add(ids=all_ids, documents=all_docs, embeddings=embeddings, metadatas=all_metadatas)

        except Exception as e:
            print(f"An error occurred while updating the collection: {e}")
            raise


    def query_collection(self, query_text):
        def combine_split_nodes(collection, documents, metadatas):
            combined_results = []

            for doc, metadata in zip(documents, metadatas):
                node_id = metadata.get("node_id")

                # Check if the document is already combined or split
                if metadata.get("split_type") is None:
                    # Document is already combined
                    combined_results.append({
                        "doc": doc,
                        "code": "",
                        "metadata": metadata,
                        "combined_text": doc
                    })
                else:
                    # Fetch all parts of the split node
                    print("here")
                    node_parts = collection.get(where={"node_id": node_id})
                    doc_part = ""
                    code_part = ""

                    for part_doc, part_metadata in zip(node_parts["documents"][0], node_parts["metadatas"][0]):
                        if part_metadata.get("split_type") == "documentation":
                            doc_part = part_doc
                        elif part_metadata.get("split_type") == "code":
                            code_part = part_doc

                    combined_text = f"documentation - \n{doc_part} \n--code-- - \n{code_part}"
                    combined_results.append({
                        "doc": doc_part,
                        "code": code_part,
                        "metadata": metadata,
                        "combined_text": combined_text
                    })

            return combined_results

        try:
            collection_name = self.collection_name

            collection = self.db_client.get_collection(name=collection_name, embedding_function=self.openai_ef)
            
            print("starting fetch")
            result = collection.query(query_texts=[query_text], n_results=10)
            print("finished fetch")

            documents = result["documents"][0]
            metadatas = result["metadatas"][0]

            combined_results = combine_split_nodes(collection, documents, metadatas)

            return combined_results

        except Exception as e:
            print(f"An error occurred while querying the collection: {e}")
            raise

    def query_and_run_agent(self, query_text):
        try:
            # Ensure the database path exists
            if not os.path.exists(self.db_path):
                raise ValueError(f"Database path '{self.db_path}' does not exist.")

            # Initialize the database client if it's not already initialized
            if self.db_client is None:
                self.db_client = chromadb.PersistentClient(path=self.db_path)

            # Check if the collection exists
            try:
                self.db_client.get_collection(name=self.collection_name, embedding_function=self.openai_ef)
            except ValueError:
                raise ValueError(f"Collection '{self.collection_name}' does not exist.")
                # print("collection not found, creating a collection")
                # self.db_client.create_collection(name=self.collection_name, embedding_function=self.openai_ef)

            # Step 1: Run the query method
            combined_results = self.query_collection(query_text)

            # for result in combined_results:
            #     result["metadata"]["code"]=""
            #     result["metadata"]["summary"]=""
            #     result["metadata"]["doc"]=""
            #     print(result["metadata"])

            # Step 2: Format the response
            formatted_response = self.format_response_for_llm(combined_results)

            # Step 3: Run the agent with the formatted response
            agent_response = asyncio.run(
                get_completion(agent_prompt(query_text, formatted_response), model="anthropic", size="large")
            )

            return agent_response

        except Exception as e:
            print(f"An error occurred while running the query and agent: {e}")
            raise


    def generate_embeddings(self, docs):
        try:
            return self.openai_ef(docs)
        except Exception as e:
            print(f"An error occurred while generating embeddings: {e}")
            raise

    def load_graph(self):
        try:
            self.graph_constructor.load_graph(self.graph_storage_path)
        except FileNotFoundError as e:
            print(f"Graph file not found: {e}")
            raise
        except Exception as e:
            print(f"An error occurred while loading the graph: {e}")
            raise

    def load_graph_and_perform_operations(self, query_text, collection_name):
        def count_tokens(text: str) -> int:
            encoding = tiktoken.get_encoding("cl100k_base")
            num_tokens = len(encoding.encode(text))
            return num_tokens
        try:
            self.load_graph()
        except Exception as e:
            print(f"Failed to load the graph: {e}")
            return

        try:
            client = chromadb.PersistentClient(path=self.db_path)
            try:
                test_collection = client.get_collection(name=collection_name, embedding_function=self.openai_ef)
            except Exception:
                print("Collection not found, creating a new one.")
                test_collection = client.create_collection(name=collection_name, embedding_function=self.openai_ef)
                print("Collection created")
                node_ids, docs, metadatas, codes = extract_chromadb_values(self.graph_constructor.graph)

                docs_and_code = []
                combined_ids = []
                combined_metadatas = []

                for i in range(len(docs)):
                    doc = docs[i]
                    code = codes[i]
                    combined_text = f"documentation - \n{doc} \n--code-- - \n{code}"
                    
                    if count_tokens(combined_text) > 8000:
                        doc_metadata = metadatas[i].copy()
                        code_metadata = metadatas[i].copy()
                        doc_metadata["split_type"] = "documentation"
                        code_metadata["split_type"] = "code"

                        doc_id = f"{node_ids[i]}-doc"
                        code_id = f"{node_ids[i]}-code"
                        
                        docs_and_code.append(f"documentation - \n{doc}")
                        docs_and_code.append(f"--code-- - \n{code}")
                        combined_ids.extend([doc_id, code_id])
                        combined_metadatas.extend([doc_metadata, code_metadata])
                        
                    else:
                        docs_and_code.append(combined_text)
                        combined_ids.append(node_ids[i])
                        combined_metadatas.append(metadatas[i])

                print("embedding")
                embeddings = self.generate_embeddings(docs_and_code)
                print("embedding done")

                test_collection.add(ids=combined_ids, documents=docs_and_code, embeddings=embeddings, metadatas=combined_metadatas)

            processed_node_ids = set()
            complete_responses = {"ids": [], "documents": [], "metadatas": []}

            result = test_collection.query(query_texts=[query_text], n_results=10)

            for i in range(len(result["ids"][0])):
                metadata = result["metadatas"][0][i]
                split_type = metadata.get("split_type")
                vector_id = result["ids"][0][i]
                doc = result["documents"][0][i]
                node_id = metadata.get("node_id")
                if node_id not in processed_node_ids:
                    if split_type is None:
                        complete_responses["ids"].append(vector_id)
                        complete_responses["documents"].append(doc)
                        complete_responses["metadatas"].append(metadata)
                    else:
                        node_parts = test_collection.get(where={"node_id": node_id})
                        code = ""
                        documentation = ""
                        
                        for j in range(len(node_parts["ids"][0])):
                            part_metadata = node_parts["metadatas"][0][j]
                            part_document = node_parts["documents"][0][j]
                            if part_metadata.get("split_type") == "documentation":
                                documentation = part_document
                            if part_metadata.get("split_type") == "code":
                                code = part_document

                        complete_responses["ids"].append(vector_id)
                        complete_responses["documents"].append(f"documentation - \n{documentation} \n--code-- - \n{code}")
                        complete_responses["metadatas"].append(metadata)
                                
                    processed_node_ids.add(node_id)

            return self.format_response_for_llm(complete_responses)

        except Exception as e:
            print(f"An error occurred during graph operations: {e}")
            raise

    def format_response_for_llm(self, response):
        try:
            formatted_string = ""
            for item in response:
                metadata = item["metadata"]
                document = item["combined_text"]
                code = document.split("--code-- - \n")[1]
                formatted_string += f"path: {metadata.get('file_path')}\n"
                formatted_string += f"signature: {metadata.get('signature')}\n"
                formatted_string += f"start line: {metadata.get('start_line')}\n"
                formatted_string += f"end line: {metadata.get('end_line')}\n"
                formatted_string += f"code: \n{code}\n\n"
            return formatted_string
        except Exception as e:
            print(f"An error occurred while formatting the response: {e}")
        raise
