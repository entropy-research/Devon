# main.py

import json
import os
import tarfile
import tempfile
from devon.retrieval.file_discovery import discover_python_files
from devon.retrieval.ast_parser import parse_python_file
from devon.retrieval.ast_extractor import extract_info_from_ast
from devon.retrieval.codebase_graph import create_graph
from devon.retrieval.graph_visualization import print_nodes_with_children, print_node_attributes, print_file_functions, print_node_details, print_function_calls


class FunctionTable:
    
    def __init__(self,temp_dir=None):
        self.function_table = {}
        self.temp_dir = temp_dir if temp_dir is not None else ""

    def add_function(self, function_name, location):
        self.function_table[function_name] = location

    def get_function(self, function_name, default):
        return self.function_table.get(function_name, default)
    
    def get_function_with_location(self, function_name):
        location =  self.function_table.get(function_name, {}).get("location", {})
        # get rid of the temp_dir from the location
        if location["file_path"].startswith(self.temp_dir):
            location["file_path"] = location["file_path"][len(self.temp_dir):]
        return location
    
    def save_to_file(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            json.dump(self.function_table, f)

    def load_from_file(self, file_path):
        with open(file_path, "r") as f:
            self.function_table = json.load(f)

class ClassTable:

    def __init__(self,temp_dir=None):
        self.class_table = {}
        self.temp_dir = temp_dir if temp_dir is not None else ""


    def add_class(self, class_name, location):
        self.class_table[class_name] = location
    
    def get_class(self, class_name, default):
        return self.class_table.get(class_name, default)
    
    def get_class_with_location(self, class_name):
        location =  self.class_table.get(class_name, {}).get("location", {})
        # get rid of the temp_dir from the location
        if location["file_path"].startswith(self.temp_dir):
            location["file_path"] = location["file_path"][len(self.temp_dir):]
        return location

    def save_to_file(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            json.dump(self.class_table, f)

    def load_from_file(self, file_path):
        with open(file_path, "r") as f:
            self.class_table = json.load(f)
    
def analyze_codebase(root_dir, ignore_dirs=None):
    """
    Analyzes the Python codebase and builds a graph representation.
    Args:
        root_dir (str): The root directory of the codebase.
        ignore_dirs (list): A list of directory names to ignore (default: None).
    Returns:
        nx.DiGraph: The graph representation of the codebase.
    """
    # Create a new graph
    graph = create_graph()

    # Discover Python files in the codebase, excluding ignored directories
    python_files = discover_python_files(root_dir, ignore_dirs)

    # Process each Python file
    for file_path in python_files:
        # Parse the Python file and generate the AST
        ast_tree = parse_python_file(file_path)

        # Extract information from the AST and build the graph
        extract_info_from_ast(graph, ast_tree, file_path)

    return graph

# # Specify the root directory of your Python codebase
# codebase_root = "."

# # Specify the directories to ignore
# ignore_directories = ["tests", "myenv", "docs", "__pycache__"]

# # Analyze the codebase and build the graph, excluding the ignored directories
# codebase_graph = analyze_codebase(codebase_root, ignore_dirs=ignore_directories)

# # Print the graph information
# # print("Number of nodes:", codebase_graph.number_of_nodes())
# # print("Number of edges:", codebase_graph.number_of_edges())
# # print("Disconnected components:", codebase_graph.graph["disconnected_components"])

# #  add all function nodes to function table with their name as key



# # print(codebase_graph.nodes(data=True))
# for node in codebase_graph.nodes(data=True):
#     if node[1].get("type","") == "function":
#         function_table[node[0]] = node[1]


# for node in codebase_graph.nodes(data=True):
#     if node[1].get("type","") == "class":
#         class_table[node[0]] = node[1]
    


# print_node_details(codebase_graph)
# print_node_attributes(codebase_graph, "extract_info_from_ast")
# print_function_calls(codebase_graph, "extract_info_from_ast")

def get_function_defn(function_name, function_table : FunctionTable):
    return function_table.get_function_with_location(function_name)

def get_class_defn(class_name, class_table : ClassTable):
    # print(class_table.class_table.keys())

    return class_table.get_class_with_location(class_name)
    # return class_table[class_name].get("location", {})



# function_table = {}

# class_table = {}


def initialize_archive(archive_path, class_table, function_table):

    # open archive into temporary directory
    archive = tarfile.open(archive_path)
    temp_dir = tempfile.mkdtemp()
    archive.extractall(temp_dir)
    archive.close()

    # initialize repository
    codebase_root = temp_dir
    ignore_directories = [".git", "docs", "__pycache__"]
    codebase_graph = analyze_codebase(codebase_root, ignore_dirs=ignore_directories)

    for node in codebase_graph.nodes(data=True):
        if node[1].get("type","") == "function":
            function_table.add_function(node[0], node[1])
        elif node[1].get("type","") == "class":
            class_table.add_class(node[0], node[1])
    return codebase_graph




def initialize_repository(repo_path, class_table, function_table):

    codebase_root = repo_path

    # print(codebase_root)
    #  list all files in the directory
    # for root, dirs, files in os.walk(codebase_root):
    #     for file in files:
    #         print(os.path.join(root, file))

    ignore_directories = [".git", "docs", "__pycache__"]

    # Analyze the codebase and build the graph, excluding the ignored directories
    codebase_graph = analyze_codebase(codebase_root, ignore_dirs=ignore_directories)

    for node in codebase_graph.nodes(data=True):
        if node[1].get("type","") == "function":
            function_table.add_function(node[0], node[1])
        elif node[1].get("type","") == "class":
            class_table.add_class(node[0], node[1])

    print(function_table)
    # print(class_table)
    
    return codebase_graph



        
