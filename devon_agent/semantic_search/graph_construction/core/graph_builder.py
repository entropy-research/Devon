import os
import hashlib
import json
import pickle
import networkx as nx
import pytest
import tempfile
from devon_agent.semantic_search.graph_construction.languages.python.python_parser import (
    PythonParser)
from devon_agent.semantic_search.graph_construction.utils import format_nodes


# Import other parsers as needed, e.g., JavaScriptParser, etc.

class GraphConstructor:
    def __init__(self, language, root_path, graph_storage_path, update, ignore_dirs=None):
        self.language = language
        self.root_path = root_path
        self.graph_storage_path = graph_storage_path
        self.graph_path = os.path.join(self.graph_storage_path, f"{language}_graph.pickle")
        self.hash_path = os.path.join(self.graph_storage_path, f"{language}_hashes.json")
        self.ignore_dirs = ignore_dirs if ignore_dirs else []

        # Choose the appropriate parser based on the language
        if language == "python":
            self.parser = PythonParser()
        # Add more language parsers as needed
        else:
            raise ValueError(f"Language {language} is not supported.")

        if not os.path.exists(graph_storage_path):
            os.makedirs(graph_storage_path)

        if not (update and os.path.exists(self.graph_path) and os.path.exists(self.hash_path)):
            print("creating new graphs and hashes")
            self.graph = nx.DiGraph()
            self.hashes = {}

        else:
            print("loading existing graphs and hashes")
            self.load_graph(self.graph_path)
            self.hashes = self.load_hashes(self.hash_path)
            print(len(self.graph.nodes))


    def load_graph(self, graph_path):
        with open(graph_path, 'rb') as f:
            self.graph = pickle.load(f)

    def load_hashes(self, hash_path):
        if os.path.exists(hash_path):
            with open(hash_path, 'r') as f:
                return json.load(f)
        return {}

    def save_graph(self, graph_path):
        with open(graph_path, 'wb') as f:
            pickle.dump(self.graph, f)

    def save_hashes(self, hash_path, hashes):
        self.hashes = hashes
        with open(hash_path, 'w') as f:
            json.dump(hashes, f)


    def compute_file_hash(self, file_path):
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    
    def detect_changes(self):
        current_hashes = {}
        actions = {"add": [], "update": [], "delete": []}
        stored_hashes = self.hashes
        ignored_paths = set()
        visited_nodes = set()

        def read_gitignore(path):
            gitignore_path = os.path.join(path, ".gitignore")
            if os.path.exists(gitignore_path):
                with open(gitignore_path, "r") as gitignore_file:
                    for line in gitignore_file:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            if line.startswith("/"):
                                normalized_path = os.path.normpath(line[1:])
                                absolute_path = os.path.abspath(os.path.join(path, normalized_path))
                            else:
                                normalized_path = os.path.normpath(line)
                                absolute_path = os.path.abspath(os.path.join(path, normalized_path))
                            ignored_paths.add(absolute_path)

        def traverse_directory(dir_path, parent_node_id):
            read_gitignore(dir_path)
            
            # Get the children of the current directory node in the graph
            children_in_graph = {
                os.path.normpath(self.graph.nodes[child]['path']): child
                for child in list(self.graph.successors(parent_node_id))
                if 'path' in self.graph.nodes[child]
            }

            # print(children_in_graph)


            # print("dir path", dir_path)

            dirs, files = [], []
            
            for entry in os.scandir(dir_path):
                abs_path = os.path.abspath(entry.path)
                if abs_path in ignored_paths or entry.name.startswith("."):
                    continue
                
                if entry.is_dir() and entry.name not in self.ignore_dirs:
                    dirs.append(entry.path)
                elif entry.is_file():
                    # Check file extension before processing
                    file_extension = os.path.splitext(entry.name)[1]
                    if file_extension in self.parser.extensions:
                        files.append(entry.path)
            
            # Process directories
            # print(children_in_graph.keys())
            for sub_dir in dirs:
                # print(sub_dir)
                # print("sub_dir", sub_dir)

                if sub_dir not in children_in_graph.keys():
                    # Create the directory node if it doesn't exist in the graph
                    sub_dir_node_id = self.create_dir(sub_dir, parent_node_id)
                    visited_nodes.add(sub_dir_node_id)
                    traverse_directory(sub_dir, sub_dir_node_id)
                else:
                    # Traverse the existing directory node
                    sub_dir_node_id = children_in_graph[sub_dir]
                    visited_nodes.add(sub_dir_node_id)
                    traverse_directory(sub_dir, sub_dir_node_id)
            
            # Process files
            for file_path in files:
                if file_path in ignored_paths:
                    continue

                current_hashes[file_path] = self.compute_file_hash(file_path)

                if file_path not in stored_hashes:
                    actions["add"].append((file_path, parent_node_id))
                elif stored_hashes[file_path] != current_hashes[file_path]:
                    actions["update"].append((file_path, parent_node_id))
                
                if file_path in children_in_graph:
                    visited_nodes.add(children_in_graph[file_path])
            
            # Handle deletions
            for child_path, node_id in children_in_graph.items():
                if child_path not in current_hashes and node_id not in visited_nodes:
                    if not os.path.isdir(child_path):
                        self.delete_file_or_dir(node_id, actions)
                    else:
                        actions["delete"].append((child_path, parent_node_id))
                    

        root_node_id = self.graph.graph.get('root_id')
        # print("rood_id", root_node_id)
        # children_in_graph = {
        #     self.graph.nodes[child]['path']: child
        #     for child in list(self.graph.successors(root_node_id))
        #     if 'path' in self.graph.nodes[child]
        # }
        # print("sss", children_in_graph)
        # Find or create the root directory node
        if root_node_id is None:
            for node_id, data in self.graph.nodes(data=True):
                if data.get("path") == self.root_path and data.get("type") == "directory":
                    root_node_id = node_id
                    break
        if root_node_id is None:
            root_node_id = self.create_dir(self.root_path, None)

        self.graph.graph['root_id'] = root_node_id
        
        traverse_directory(self.root_path, root_node_id)
        return actions, current_hashes

    def delete_file_or_dir(self, node_id, actions = None):
        if (self.graph.nodes[node_id]["type"] == "file"):
            if actions is not None:
                actions["delete"].append((self.graph.nodes[node_id]["path"], node_id))
            # print("deleting file", self.graph.nodes[node_id]["path"])
        elif (self.graph.nodes[node_id]["type"] == "directory"):
            # print("deleting dir", self.graph.nodes[node_id]["path"])
            pass
        children = list(self.graph.successors(node_id))
        for child in children:
            self.delete_file_or_dir(child, actions)
        self.graph.remove_node(node_id)

    def create_dir(self, path, parent_node_id):
        print("creating dir", path)
        
        directory_node = format_nodes.format_directory_node(path, False, 0)  # Adjust level as needed
        directory_node_id = directory_node["attributes"]["node_id"]
        self.graph.add_node(directory_node_id, **directory_node["attributes"])

        # print(self.graph.nodes[directory_node_id])

        if parent_node_id is not None:
            self.graph.add_edge(parent_node_id, directory_node_id, type="CONTAINS")

        # if parent_node_id == self.graph.graph.get('root_id'):
        #     print("here")

        #     children_in_graph = {
        #         self.graph.nodes[child]['path']: child
        #         for child in list(self.graph.successors(parent_node_id))
        #         if 'path' in self.graph.nodes[child]
        #     }
        #     print("sucessors", children_in_graph)

        return directory_node_id

    def build_or_update_graph(self):
        actions, current_hashes = self.detect_changes()
        
        for file in actions["add"]:
            self.process_file(file, action="add")
        for file in actions["update"]:
            self.process_file(file, action="update")
        for file in actions["delete"]:
            self.process_file(file, action="delete")
        
        # self.save_graph(self.graph_path)
        # self.hashes = current_hashes  # Update self.hashes with the current hashes
        # self.save_hashes(self.hash_path, self.hashes)

        return actions, current_hashes  # Return the actions list

    def process_file(self, parent_id_and_file_path, action):
        if action == "update":
            self.remove_file_from_graph(parent_id_and_file_path)
            success = self.parse_file_and_update_graph(parent_id_and_file_path)
            # if success:
                  # Ensure old nodes are removed before adding new ones
            # self.delete_file_or_dir()
            
        elif action == "add":
            self.parse_file_and_update_graph(parent_id_and_file_path)
        elif action == "delete":
            # self.remove_file_from_graph(file_path)
            pass

    def parse_file_and_update_graph(self, parent_id_and_file_path):
        parent_id = parent_id_and_file_path[1]
        file_path = parent_id_and_file_path[0]
        # print(file_path)
        try:
            nodes, relationships, imports = self.parser.parse_file(file_path, self.root_path, {}, {}, level=0)
        except Exception as e:
            print(e, file_path)
            return False

        if len(nodes) == 0:
            return
        
        for node in nodes:
            
            node["attributes"]['path'] = file_path
            node["attributes"]['type'] = node["type"]
            # print("creating node")
            self.graph.add_node(node["attributes"]["node_id"], **node["attributes"])
        
        for relationship in relationships:
            # print("creating relationship")
            self.graph.add_edge(relationship["sourceId"], relationship["targetId"], type=relationship["type"])
        
        self.graph.add_edge(parent_id, nodes[0]["attributes"]["node_id"], type="CONTAINS")
        return True

    def remove_file_from_graph(self, parent_id_and_file_path):
        parent_node_id = parent_id_and_file_path[1]
        file_path = parent_id_and_file_path[0]
        
        # Get the file node using the parent_node_id
        node_id_to_remove = None
        for child in self.graph.successors(parent_node_id):
            if self.graph.nodes[child].get("path") == file_path:
                node_id_to_remove = child
                break
        
        if node_id_to_remove is not None:
            # print("removing node", file_path, node_id_to_remove)
            self.delete_file_or_dir(node_id_to_remove, None)
        else:
            print("Node to remove not found for path:", file_path)