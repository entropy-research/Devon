# ast_extractor.py

import ast
import os

import networkx as nx

from devon_agent.retrieval.codebase_graph import add_edge, add_node


def extract_info_from_ast(graph, ast_tree, file_path):
    # Add file node to the graph

    def nestedTestFunction():
        pass

    file_attrs = {
        "type": "file",
        "file_path": file_path,
    }
    add_node(graph, file_path, file_attrs)

    # Add directory node to the graph
    directory_path = os.path.dirname(file_path)
    directory_attrs = {
        "type": "directory",
        "directory_path": directory_path,
    }
    add_node(graph, directory_path, directory_attrs)

    # Add edge from directory to file
    add_edge(graph, directory_path, file_path, "contains", {})

    # Define a visitor class to traverse the AST
    # Define a visitor class to traverse the AST
    class ASTVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_scope = []

        def visit_ClassDef(self, node):
            class_name = node.name
            class_lineno = node.lineno
            class_attrs = {
                "type": "class",
                "code": ast.unparse(node),
                "doc": ast.get_docstring(node),
                "location": {
                    "file_path": file_path,
                    "start_line": class_lineno,
                    "end_line": class_lineno + len(node.body) - 1,
                },
                "dependencies": {
                    "imports": [],
                    "exported": [],
                },
            }

            # Add the class node to the graph
            add_node(graph, class_name + ":" + file_path, class_attrs)

            # Add edge from file to class
            add_edge(graph, file_path, class_name, "defines", {})

            # Update the current scope
            self.current_scope.append(class_name)

            # Visit the body of the class
            self.generic_visit(node)

            # Remove the class from the current scope
            self.current_scope.pop()

        def visit_FunctionDef(self, node):
            function_name = node.name
            function_lineno = node.lineno
            function_attrs = {
                "type": "function",
                "code": ast.unparse(node),
                "doc": ast.get_docstring(node),
                "location": {
                    "file_path": file_path,
                    "start_line": function_lineno,
                    "end_line": function_lineno + len(node.body) - 1,
                },
                "dependencies": {
                    "imports": [],
                    "exported": [],
                },
            }

            # Add the function node to the graph
            add_node(graph, function_name + ":" + file_path, function_attrs)

            # Add edge from the current scope to the function
            if self.current_scope:
                parent = self.current_scope[-1]
                add_node(
                    graph,
                    parent + "." + function_name + ":" + file_path,
                    function_attrs,
                )
                add_edge(graph, parent, function_name, "defines", {})
            else:
                # If not inside a class, add edge from file to function
                add_edge(graph, file_path, function_name, "defines", {})

            # Update the current scope
            self.current_scope.append(function_name)

            # Visit the body of the function
            self.generic_visit(node)

            # Remove the function from the current scope
            self.current_scope.pop()

        def visit_Import(self, node):
            for alias in node.names:
                imported_module = alias.name
                # import_lineno = node.lineno

                # Add the imported module to the dependencies of the current scope
                if self.current_scope:
                    current_node = self.current_scope[-1]
                    try:
                        graph.nodes[current_node]["dependencies"]["imports"].append(
                            imported_module
                        )
                    except:
                        pass
                    # graph.nodes[current_node]["dependencies"]["imports"].append(imported_module)
                # else:
                #     # If not inside a function or class, add the import to the file dependencies
                #     file_node = file_path
                #     graph.nodes[file_node]["dependencies"]["imports"].append(imported_module)

        def visit_ImportFrom(self, node):
            imported_module = node.module
            # import_lineno = node.lineno

            # Add the imported module to the dependencies of the current scope
            if self.current_scope:
                current_node = self.current_scope[-1]
                try:
                    graph.nodes[current_node]["dependencies"]["imports"].append(
                        imported_module
                    )
                except Exception:
                    pass
            # else:
            #     # If not inside a function or class, add the import to the file dependencies
            #     file_node = file_path
            #     graph.nodes[file_node]["dependencies"]["imports"].append(imported_module)

        def visit_Call(self, node):
            called_function = None
            if isinstance(node.func, ast.Name):
                called_function = node.func.id
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    called_function = f"{node.func.value.id}.{node.func.attr}"
            elif isinstance(node.func, ast.Call):
                # Handle nested function calls
                self.visit(node.func)

            if called_function:
                call_lineno = node.lineno
                if self.current_scope:
                    caller = self.current_scope[-1]
                    add_edge(
                        graph,
                        caller,
                        called_function,
                        "calls",
                        {"file_path": file_path, "line_number": call_lineno},
                    )

    # Create an instance of the ASTVisitor
    visitor = ASTVisitor()

    # Traverse the AST using the visitor
    visitor.visit(ast_tree)

    # Update the graph metadata
    graph.graph["total_nodes"] = len(graph.nodes)
    graph.graph["total_edges"] = len(graph.edges)
    graph.graph["disconnected_components"] = list(nx.weakly_connected_components(graph))
