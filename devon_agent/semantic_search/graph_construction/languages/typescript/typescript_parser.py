import os

import tree_sitter_languages
from devon_agent.semantic_search.graph_construction.core.base_parser import BaseParser



class TypescriptParser(BaseParser):
    def __init__(self):
        super().__init__("typescript", "*")
        self.extensions = [".js", ".ts", ".tsx", ".jsx"]

    def _remove_extensions(self, file_path):
        no_extension_path = str(file_path)
        for extension in self.extensions:
            no_extension_path = no_extension_path.replace(extension, "")
        return no_extension_path

    def is_package(self, directory):
        return os.path.exists(os.path.join(directory, "__init__.py"))

    def find_module_path(self, module_name, start_dir, project_root):
        current_dir = start_dir
        components = module_name.split(".")

        # Make sure to find in the same directory as the root
        project_root = os.sep.join(project_root.split(os.sep)[:-1])
        # Try to find the module by traversing up towards the root until the module path is found or root is reached
        while current_dir.startswith(project_root) and (current_dir != "" or project_root != ""):
            possible_path = os.path.join(current_dir, *components)
            # Check for a direct module or package
            if os.path.exists(possible_path + ".py") or self.is_package(possible_path):
                return possible_path.replace("/", ".")
            # Move one directory up
            current_dir = os.path.dirname(current_dir)
        return None

    def resolve_relative_import_path(self, import_statement, current_file_path, project_root):
        if import_statement.startswith(".."):
            import_statement = import_statement[2:]
            current_file_path = os.sep.join(current_file_path.split(os.sep)[:-1])
        elif import_statement.startswith("."):
            import_statement = import_statement[1:]
        else:
            return self.find_module_path(import_statement, current_file_path, project_root)

        return self.resolve_relative_import_path(import_statement, current_file_path, project_root)

    def resolve_import_path(self, import_statement, current_file_directory, project_root):
        """
        Resolve the absolute path of an import statement.
        import_statement: The imported module as a string (e.g., 'os', 'my_package.my_module').
        current_file_directory: The directory of the file containing the import statement.
        project_root: The root directory of the project.
        """
        # Handling relative imports
        if import_statement.startswith("."):
            current_file_directory = os.sep.join(current_file_directory.split(os.sep)[:-1])
            return self.resolve_relative_import_path(import_statement, current_file_directory, project_root)
        else:
            # Handling absolute imports
            return self.find_module_path(import_statement, current_file_directory, project_root)

    def skip_directory(self, directory: str) -> bool:
        return directory == "__pycache__"

    def parse_file(
        self,
        file_path: str,
        root_path: str,
        visited_nodes: dict,
        global_imports: dict,
        level: int,
    ):
        if file_path.endswith("__init__.py"):
            return [], [], self.parse_init(file_path, root_path)
        return self.parse(file_path, root_path, visited_nodes, global_imports, level)

    def parse_init(self, file_path: str, root_path: str):
        parser = tree_sitter_languages.get_parser(self.language)
        with open(file_path, "r") as file:
            code = file.read()
        tree = parser.parse(bytes(code, "utf-8"))
        directory = ".".join(file_path.split(os.sep)[:-1])
        imports = {directory: []}
        temp_imports = {}
        for node in tree.root_node.children:
            if node.type == "import_from_statement":
                import_statements = node.named_children

                from_statement = import_statements[0]
                from_text = from_statement.text.decode()
                for import_statement in import_statements[1:]:
                    import_path = self.resolve_import_path(from_text, file_path, root_path)
                    if not import_path:
                        continue
                    new_import_path = import_path + "." + import_statement.text.decode()
                    import_alias = directory + "." + import_statement.text.decode()
                    imports[import_alias] = new_import_path
                    temp_imports[import_statement.text.decode()] = new_import_path
                    imports[directory].append(new_import_path)

            if node.type == "expression_statement":
                statement_children = node.children
                if statement_children[0].type == "assignment":
                    assignment = statement_children[0].named_children

                    variable_identifier = assignment[0]
                    assign_value = assignment[1]
                    if variable_identifier.text.decode() == "__all__":
                        imports[directory] = []
                        if assign_value.type == "list":
                            for child in assign_value.children:
                                if child.type == "string":
                                    for string_child in child.children:
                                        if string_child.type == "string_content":
                                            child_path = temp_imports.get(string_child.text.decode())
                                            if child_path:
                                                imports[directory].append(child_path)

        return imports
