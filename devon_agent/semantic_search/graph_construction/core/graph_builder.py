
import os
import uuid
import pickle

import networkx as nx
from devon_agent.semantic_search.graph_construction.utils import format_nodes
from devon_agent.semantic_search.graph_construction.languages.python.python_parser import (
    PythonParser)


class GraphConstructor:
    def __init__(self, language = "python"):
        self.graph = nx.DiGraph()  # Create a directed graph
        self.directories_map = {}
        self.visited_nodes = {}
        self.global_imports = {}
        self.import_aliases = {}
        self.root = None
        self.skip_tests = True
        if language == "python":
            self.parser = PythonParser()
        # elif language == "javascript":
        #     self.parser = JavascriptParser()
        else:
            raise ValueError(f"Language {language} not supported")
        # TODO: Add more languages

    def save_graph(self, file_path):
        """Saves the graph to the specified file path using pickle."""
        # Ensure the directory exists
        print(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Save the graph using pickle
        with open(file_path, "wb") as f:
            pickle.dump(self.graph, f)

    def load_graph(self, file_path):
        """Loads the graph from the specified file path using pickle."""
        # Load the graph using pickle
        with open(file_path, "rb") as f:
            self.graph = pickle.load(f)
        # Retrieve the root node ID from the loaded graph's graph attributes
        self.root_node_id = self.graph.graph.get("root_node_id")

    
    def set_root_node(self, root_node_id):
        self.root_node_id = root_node_id
        self.graph.graph["root_node_id"] = root_node_id

    def _scan_directory(
        self,
        path: str,
        nodes: list = None,
        relationships: list = None,
        imports: dict = None,
        parent_id: str = None,
        level: int = 0,
        ignored_paths: set = None,
    ):
        if nodes is None:
            nodes = []
        if relationships is None:
            relationships = []
        if imports is None:
            imports = {}
        if ignored_paths is None:
            ignored_paths = set()

        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory {path} not found")
        if self.root is None:
            self.root = path
        if path.endswith("tests") or path.endswith("test"):
            return nodes, relationships, imports

        # package = self.parser.is_package(path)

        directory_node = format_nodes.format_directory_node(path, False, level)
        directory_path = directory_node["attributes"]["path"]
        directory_node_id = directory_node["attributes"]["node_id"]

        if self.root_node_id is None:
            self.set_root_node(directory_node_id)

        if parent_id is not None:
            relationships.append(
                {
                    "sourceId": parent_id,
                    "targetId": directory_node_id,
                    "type": "CONTAINS",
                }
            )

        nodes.append(directory_node)

        # Read .gitignore file if present and update ignored_paths set
        gitignore_path = os.path.join(path, ".gitignore")
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as gitignore_file:
                for line in gitignore_file:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        normalized_path = os.path.normpath(line)
                        absolute_path = os.path.abspath(os.path.join(path, normalized_path))
                        ignored_paths.add(absolute_path)
                        print(absolute_path)

        for entry in os.scandir(path):
            if (entry.name in ["legacy", "test"] and self.skip_tests) or entry.name.startswith("."):
                continue

            # Check if the entry path matches any ignored path
            if os.path.abspath(entry.path) in ignored_paths:
                continue

            if entry.is_file():
                if entry.name.endswith(".py") or entry.name.endswith(".js"):
                    entry_name = entry.name.split(".")[0]
                    try:
                        processed_nodes, relations, file_imports = self.parser.parse_file(
                            entry.path,
                            self.root,
                            visited_nodes=self.visited_nodes,
                            global_imports=self.global_imports,
                            level=level,
                        )
                    except Exception as e:
                        print(f"Error {entry.path}")
                        print(e)
                        continue
                    print(f"Processed {entry.path}")
                    if not processed_nodes:
                        self.import_aliases.update(file_imports)
                        continue
                    file_root_node_id = processed_nodes[0]["attributes"]["node_id"]

                    nodes.extend(processed_nodes)
                    relationships.extend(relations)
                    relationships.append(
                        {
                            "sourceId": directory_node_id,
                            "targetId": file_root_node_id,
                            "type": "CONTAINS",
                        }
                    )
                    imports.update(file_imports)

                    global_import_key = (directory_path + entry_name).replace("/", ".")
                    self.global_imports[global_import_key] = {
                        "id": file_root_node_id,
                        "type": "FILE",
                    }
                else:
                    pass
                    # file_node = {
                    #     "type": "FILE",
                    #     "attributes": {
                    #         "path": entry.path,
                    #         "name": entry.name,
                    #         "node_id": str(uuid.uuid4()),
                    #     },
                    # }
                    # nodes.append(file_node)
                    # relationships.append(
                    #     {
                    #         "sourceId": directory_node_id,
                    #         "targetId": file_node["attributes"]["node_id"],
                    #         "type": "CONTAINS",
                    #     }
                    # )
            if entry.is_dir():
                if self.parser.skip_directory(entry.name):
                    continue
                nodes, relationships, imports = self._scan_directory(
                    entry.path, nodes, relationships, imports, directory_node_id, level + 1, ignored_paths
                )
        return nodes, relationships, imports 

    def build_graph(self, path):
        self.clear_graph()
        
        nodes, relationships, imports = self._scan_directory(path)
        
        for node in nodes:
            node["attributes"]["type"] = node["type"]
            self.graph.add_node(node["attributes"]["node_id"], **node["attributes"])
        for relationship in relationships:
            self.graph.add_edge(relationship["sourceId"], relationship["targetId"], type=relationship["type"])

    def clear_graph(self):
        self.graph.clear()
        self.root_node_id = None
        self.directories_map = {}
        self.visited_nodes = {}
        self.global_imports = {}
        self.import_aliases = {}
        self.graph.graph["root_node_id"] = None




    # def _relate_wildcard_imports(self, file_node_id: str, imports_list: list):
    #     import_edges = []
    #     for import_path in imports_list:
    #         all_dir_imports = self.import_aliases.get(import_path)
    #         if all_dir_imports is None:
    #             all_dir_imports = [import_path]
    #         for dir_import in all_dir_imports:
    #             targetId = self.global_imports.get(dir_import)
    #             if targetId:
    #                 import_edges.append(
    #                     {
    #                         "sourceId": file_node_id,
    #                         "targetId": targetId["id"],
    #                         "type": "IMPORTS",
    #                     }
    #                 )
    #     return import_edges

    # # Recursive functions to relate imports
    # def _relate_imports_and_directory_imports(self, file_node_id: str, path: str, visited_paths=set()):
    #     import_edges = []
    #     import_alias = self.import_aliases.get(path)
    #     targetId = self.global_imports.get(path)
    #     if not targetId and import_alias:
    #         if isinstance(import_alias, list):
    #             for alias in import_alias:
    #                 if alias not in visited_paths:
    #                     visited_paths.add(alias)
    #                     import_edges.extend(
    #                         self._relate_imports_and_directory_imports(file_node_id, alias, visited_paths)
    #                     )
    #         else:
    #             targetId = self.global_imports.get(import_alias)
    #     if targetId:
    #         import_edges.append(
    #             {
    #                 "sourceId": file_node_id,
    #                 "targetId": targetId["id"],
    #                 "type": "IMPORTS",
    #             }
    #         )
    #     return import_edges

    # def _relate_imports(self, imports: dict):
    #     import_edges = []
    #     for file_node_id in imports.keys():
    #         for imp, import_object in imports[file_node_id].items():
    #             path = import_object["path"]
    #             if imp == "_*wildcard*_" and path:
    #                 related_imports = self._relate_wildcard_imports(file_node_id, path)
    #                 import_edges.extend(related_imports)
    #                 continue
    #             import_edges.extend(self._relate_imports_and_directory_imports(file_node_id, f"{path}.{imp}"))
    #     return import_edges

    # def __get_directory(self, node_attrs, function_call, imports):
    #     if "type" in node_attrs and node_attrs["type"] == "FILE":
    #         file_imports = imports.get(node_attrs["node_id"], {})
    #     else:
    #         file_imports = imports.get(node_attrs.get("file_node_id"), {})

    #     import_object = file_imports.get(function_call.split(".")[0], {})
    #     root_directory = node_attrs["path"].replace("." + node_attrs["name"], "")
    #     alias = import_object.get("alias", "")
    #     function_import = import_object.get("path", "")
    #     directory = root_directory
    #     if function_import:
    #         # Change the directory to complete path if it's an alias else it's assumed to be a regular import
    #         import_alias = function_import + "." + function_call.split(".")[0]
    #         directory = self.import_aliases.get(import_alias, function_import)
    #     elif file_imports.get("_*wildcard*_"):
    #         # See if the import is present as wildcard import (*)
    #         for wildcard_path in file_imports["_*wildcard*_"]:
    #             import_alias = wildcard_path + "." + function_call.split(".")[0]
    #             if import_alias in self.import_aliases:
    #                 directory = self.import_aliases[wildcard_path + "." + function_call.split(".")[0]]
    #                 break

    #     if isinstance(directory, list):
    #         candidates = [s for s in directory if s.endswith(function_call.split(".")[-1])]
    #         if len(candidates) == 1:
    #             directory = candidates[0]
    #         else:
    #             directory = ""

    #     for module in function_call.split("."):
    #         if module == alias:
    #             continue
    #         final_module = "." + module
    #         intermediate_module = "." + module + "."
    #         if not (final_module in directory or intermediate_module in directory):
    #             directory += f".{module}"

    #     return directory

    # def __relate_function_calls(self, node_attrs, function_calls, imports):
    #     relations = []
    #     for function_call in function_calls:
    #         # Get the directory of the function using the import logic of the language
    #         directory = self.__get_directory(node_attrs, function_call, imports)
    #         target_object = self.global_imports.get(directory)


    #         if target_object:
    #             target_object_type = target_object["type"]
    #             if target_object_type == "FUNCTION" or target_object_type == "FILE":
    #                 relations.append(
    #                     {
    #                         "sourceId": node_attrs["node_id"],
    #                         "targetId": target_object["id"],
    #                         "type": "CALLS",
    #                     }
    #                 )
    #             elif target_object_type == "CLASS":
    #                 relations.append(
    #                     {
    #                         "sourceId": node_attrs["node_id"],
    #                         "targetId": target_object["id"],
    #                         "type": "INSTANTIATES",
    #                     }
    #                 )

    #                 init_directory = directory + ".__init__"
    #                 if init_directory in self.global_imports:
    #                     init_node = self.global_imports[init_directory]
    #                     relations.append(
    #                         {
    #                             "sourceId": node_attrs["node_id"],
    #                             "targetId": init_node["id"],
    #                             "type": "CALLS",
    #                         }
    #                     )
    #     return relations

    # def __relate_inheritances(self, node_attrs, inherits, imports):
    #     relations = []

    #     for inherit in inherits:
    #         # Get the directory of the function using the import logic of the language
    #         directory = self.__get_directory(node_attrs, inherit, imports)
    #         # Look for the node with the definition of the class
    #         target_class = self.global_imports.get(directory)

    #         if target_class:
    #             relations.append(
    #                 {
    #                     "sourceId": node_attrs["node_id"],
    #                     "targetId": target_class["id"],
    #                     "type": "INHERITS",
    #                 }
    #             )

    #     return relations

    # def _relate_constructor_calls(self, node_view, imports):
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
    #                 self.graph.add_edge(relation["sourceId"], relation["targetId"], type=relation["type"])   