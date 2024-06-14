import json
import os
from functools import reduce

from devon_agent.retrieval.ast_extractor import extract_info_from_ast
from devon_agent.retrieval.ast_parser import parse_python_file
from devon_agent.retrieval.codebase_graph import CodeGraph
from devon_agent.retrieval.file_discovery import discover_python_files


class FunctionTable:
    def __init__(self, temp_dir=None):
        self.function_table = {}
        self.temp_dir = temp_dir if temp_dir is not None else ""

    def add_function(self, function_name, location):
        if function_name not in self.function_table:
            self.function_table[function_name] = [location]
        else:
            # print(f"Function {function_name} already exists in function table")
            self.function_table[function_name].append(location)

    def get_function(self, function_name, default):
        result = self.function_table.get(function_name, default)
        if len(result) == 1:
            return result[0]
        else:
            return result

    def get_function_with_location(self, function_name):
        # functions =  self.function_table.get(function_name, {})
        functions = reduce(
            lambda a, b: a + b,
            [
                self.function_table.get(k, {})
                for k in list(self.function_table.keys())
                if k.lower() == function_name.lower()
            ],
            [],
        )
        if len(functions) == 0:
            return {}

        results = []
        for function in functions:
            result = {}
            result["location"] = function.get("location", {})
            if result["location"].get("file_path", "").startswith(self.temp_dir):
                result["location"]["file_path"] = result["location"]["file_path"][
                    len(self.temp_dir) :
                ]
            result["code"] = function.get("code", "")
            if len(result["code"].split("/n")) > 20:
                result["code"] = "\n".join(result["code"].split("/n")[:20]) + "\n..."
            results.append(result)
        return results

    def save_to_file(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            json.dump(self.function_table, f)

    def load_from_file(self, file_path):
        with open(file_path, "r") as f:
            self.function_table = json.load(f)


class ClassTable:
    def __init__(self, temp_dir=None):
        self.class_table = {}
        self.temp_dir = temp_dir if temp_dir is not None else ""

    def add_class(self, class_name, location):
        if class_name not in self.class_table:
            self.class_table[class_name] = [location]
        else:
            self.class_table[class_name].append(location)

    def get_class(self, class_name, default):
        result = self.class_table.get(class_name, default)
        if len(result) == 1:
            return result[0]
        else:
            return result

    def get_class_with_location(self, class_name: str):
        # classes = self.class_table.get(class_name, {})
        classes = reduce(
            lambda a, b: a + b,
            [
                self.class_table.get(k, {})
                for k in list(self.class_table.keys())
                if k.lower() == class_name.lower()
            ],
            [],
        )

        if len(classes) == 0:
            return {}

        results = []
        for _class in classes:
            result = {}
            result["location"] = _class["location"]
            if result["location"].get("file_path", "").startswith(self.temp_dir):
                result["location"]["file_path"] = result["location"]["file_path"][
                    len(self.temp_dir) :
                ]
            result["code"] = _class["code"]
            results.append(result)
        return results

    def save_to_file(self, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(file_path, "w") as f:
            json.dump(self.class_table, f)

    def load_from_file(self, file_path):
        with open(file_path, "r") as f:
            self.class_table = json.load(f)


class CodeIndex:
    def __init__(self, codebase_path):
        self.code_graph = CodeGraph()
        self.function_table = FunctionTable(codebase_path)
        self.class_table = ClassTable(codebase_path)
        self.codebase_path = codebase_path

    def initialize_tables(self):
        for node in self.code_graph.graph.nodes(data=True):
            if node[1].get("type", "") == "function":
                node[1]["location"]["file_path"] = node[1]["location"]["file_path"][
                    len(self.codebase_path) :
                ]
                name, filepath = node[0].split(":")
                self.function_table.add_function(name, node[1])
            elif node[1].get("type", "") == "class":
                node[1]["location"]["file_path"] = node[1]["location"]["file_path"][
                    len(self.codebase_path) :
                ]
                name, filepath = node[0].split(":")
                self.class_table.add_class(name, node[1])

    def initialize(self):
        ignore_directories = [".git", "docs", "__pycache__"]

        python_files = discover_python_files(self.codebase_path, ignore_directories)

        for python_file in python_files:
            ast_tree = parse_python_file(python_file)
            if ast_tree is None:
                continue
            # print(file_path)

            # Extract information from the AST and build the graph
            extract_info_from_ast(self.code_graph.graph, ast_tree, python_file)
        print("intialized")
        self.initialize_tables()

    def save_as_json(self, file_path):
        index = {
            "codebase_path": self.codebase_path,
            "function_table": self.function_table.function_table,
            "class_table": self.class_table.class_table,
            "code_graph": self.code_graph.to_json(),
        }

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(index, f, default=list)

    @classmethod
    def load_from_json(cls, file_path):
        with open(file_path, "r") as f:
            index = json.load(f)
        code_index = cls(index["codebase_path"])
        code_index.function_table.function_table = index["function_table"]
        code_index.class_table.class_table = index["class_table"]
        code_index.code_graph.from_json_dict(index["code_graph"])
        return code_index

        # print(node[0])
