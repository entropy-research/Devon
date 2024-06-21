import anyio
import uuid
import networkx as nx
import chromadb
import asyncio
import tiktoken
from devon_agent.semantic_search.graph_construction.core.graph_builder import GraphConstructor
from devon_agent.semantic_search.graph_traversal.encode_codegraph import (generate_doc_level_wise)
from devon_agent.semantic_search.graph_traversal.value_extractor import (extract_chromadb_values)
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv
import os


# Load environment variables from .env file
load_dotenv()

class CodeGraphManager:
    def __init__(self, graph_path, db_path, collection_name, OPENAI_API_KEY, root_path=None):
        self.graph_path = graph_path
        self.db_path = db_path
        self.root_path = root_path
        self.graph_constructor = GraphConstructor("python")
        self.openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name="text-embedding-ada-002"
            )
        self.collection_name = collection_name
    
    def create_graph(self):

        def count_tokens(text: str) -> int:
            encoding = tiktoken.get_encoding("cl100k_base")
            num_tokens = len(encoding.encode(text))
            return num_tokens


        if not self.root_path:
            raise ValueError("Root path is not provided")
        
        # repo_id = str(uuid.uuid4())
        self.graph_constructor.build_graph(self.root_path)
        asyncio.run(generate_doc_level_wise(self.graph_constructor.graph))
        # self.graph_constructor.save_graph(self.graph_path)

        client = chromadb.PersistentClient(path=self.db_path)

        collection = client.create_collection(name=self.collection_name, embedding_function=self.openai_ef)
        print("collection created")
        node_ids, docs, metadatas, codes = extract_chromadb_values(self.graph_constructor.graph)

        docs_and_code = []
        combined_ids = []
        combined_metadatas = []

        for i in range(len(docs)):
            doc = docs[i]
            code = codes[i]
            combined_text = f"documentation - \n{doc} \n--code-- - \n{code}"
            
            if count_tokens(combined_text) > 8000:
                # Split into separate entries
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
        if len(embeddings) > 0:
            collection.add(ids=combined_ids, documents=docs_and_code, embeddings=embeddings, metadatas=combined_metadatas)

    def generate_embeddings(self, docs):
        if docs:
            return self.openai_ef(docs)
        else:
            return []

    def load_graph(self):
        self.graph_constructor.load_graph(self.graph_path)

    def query(self, query_text):

        client = chromadb.PersistentClient(path=self.db_path)

        collection = client.get_collection(name=self.collection_name, embedding_function=self.openai_ef)
        

        # Use a set to keep track of already processed node_ids
        processed_node_ids = set()
        complete_responses = {"ids": [], "documents": [], "metadatas": []}

        # Query the collection
        result = collection.query(query_texts=[query_text], n_results=10)

        
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
                    node_parts = collection.get(where={"node_id": node_id})
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
    
    def delete_collection(self, collection_name):
        client = chromadb.PersistentClient(path=self.db_path)
        client.delete_collection(collection_name)

    def format_response_for_llm(self, response):
        formatted_string = ""
        ids = response["ids"]
        metadatas = response["metadatas"]
        documents = response["documents"]
        
        for i in range(len(ids)):
            metadata = metadatas[i]
            document = documents[i]
            code = document.split("--code-- - \n")[1]
            formatted_string += f"path: {metadata.get('file_path')}\n"
            formatted_string += f"signature: {metadata.get('signature')}\n"
            formatted_string += f"start line: {metadata.get('start_line')}\n"
            formatted_string += f"end line: {metadata.get('end_line')}\n"
            formatted_string += f"code: \n{code}\n\n"

        return formatted_string
