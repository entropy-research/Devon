from abc import ABC, abstractmethod
from devon_agent.semantic_search.graph_construction.utils import format_nodes, tree_parser
from pathlib import Path

import tree_sitter_languages
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import BaseNode, Document, NodeRelationship
from llama_index.core.text_splitter import CodeSplitter
from llama_index.packs.code_hierarchy import CodeHierarchyNodeParser



class BaseParser(ABC):
    RELATIONS_TYPES_MAP = {
        "function_definition": "FUNCTION_DEFINITION",
        "class_definition": "CLASS_DEFINITION",
    }

    def __init__(
        self,
        language: str,
        wildcard: str,
    ):
        self.language = language
        self.wildcard = wildcard

    def parse(
        self,
        file_path: str,
        root_path: str,
        visited_nodes: dict,
        global_imports: dict,
        level: int,
    ):
        path = Path(file_path)
        if not path.exists():
            print(f"File {file_path} does not exist.")
            raise FileNotFoundError

        documents = SimpleDirectoryReader(
            input_files=[path],
            file_metadata=lambda x: {"filepath": x},
        ).load_data()

        # Bug related to llama-index it's safer to remove non-ascii characters. Could be removed in the future
        documents[0].text = tree_parser.remove_non_ascii(documents[0].text)

        code = CodeHierarchyNodeParser(
            language=self.language,
            chunk_min_characters=3,
            code_splitter=CodeSplitter(language=self.language, max_chars=10000, chunk_lines=10),
        )
        try:
            split_nodes = code.get_nodes_from_documents(documents)
        except TimeoutError:
            print(f"Timeout error: {file_path}")
            return [], [], {}

        node_list = []
        edges_list = []
        assignment_dict = {}

        file_node, file_relations = self.__process_node__(
            split_nodes.pop(0), file_path, "", visited_nodes, global_imports, assignment_dict, documents[0], level
        )
        node_list.append(file_node)
        edges_list.extend(file_relations)

        for node in split_nodes:
            processed_node, relationships = self.__process_node__(
                node,
                file_path,
                file_node["attributes"]["node_id"],
                visited_nodes,
                global_imports,
                assignment_dict,
                documents[0],
                level,
            )

            node_list.append(processed_node)
            edges_list.extend(relationships)

        imports = self._get_imports(str(path), node_list[0]["attributes"]["node_id"], root_path)

        return node_list, edges_list, imports

    def get_start_and_end_line_from_byte(self, file_contents, start_byte, end_byte):
        start_line = file_contents.count("\n", 0, start_byte) + 1
        end_line = file_contents.count("\n", 0, end_byte) + 1

        return start_line, end_line

    def __process_node__(
        self,
        node: BaseNode,
        file_path: str,
        file_node_id: str,
        visited_nodes: dict,
        global_imports: dict,
        assignment_dict: dict,
        document: Document,
        level: int,
    ):
        no_extension_path = self._remove_extensions(file_path)
        relationships = []
        scope = node.metadata["inclusive_scopes"][-1] if node.metadata["inclusive_scopes"] else None
        type_node = scope["type"] if scope else "file"
        parent_level = level
        leaf = False

        if type_node == "function_definition":
            function_calls = tree_parser.get_function_calls(node, assignment_dict, self.language)
            processed_node = format_nodes.format_function_node(node, scope, function_calls, file_node_id)
        elif type_node == "class_definition":
            inheritances = tree_parser.get_inheritances(node, self.language)
            processed_node = format_nodes.format_class_node(node, scope, file_node_id, inheritances)
        else:
            function_calls = tree_parser.get_function_calls(node, assignment_dict, self.language)
            processed_node = format_nodes.format_file_node(node, file_path, function_calls)
        for relation in node.relationships.items():
            if relation[0] == NodeRelationship.CHILD:
                if len(relation[1]) == 0:
                    leaf = True
                for child in relation[1]:
                    relation_type = (
                        child.metadata["inclusive_scopes"][-1]["type"] if child.metadata["inclusive_scopes"] else ""
                    )
                    relationships.append(
                        {
                            "sourceId": node.node_id,
                            "targetId": child.node_id,
                            "type": self.RELATIONS_TYPES_MAP.get(relation_type, "UNKNOWN"),
                        }
                    )
            elif relation[0] == NodeRelationship.PARENT:
                if relation[1]:
                    parent_path = (
                        visited_nodes.get(relation[1].node_id, {}).get("path", no_extension_path).replace("/", ".")
                    )
                    parent_level = visited_nodes.get(relation[1].node_id, {}).get("level", level)

                    node_path = f"{parent_path}.{processed_node['attributes']['name']}"
                else:
                    node_path = no_extension_path.replace("/", ".")
        start_line, end_line = self.get_start_and_end_line_from_byte(
            document.text, node.metadata["start_byte"], node.metadata["end_byte"]
        )
        processed_node["attributes"]["start_line"] = start_line
        processed_node["attributes"]["end_line"] = end_line
        processed_node["attributes"]["path"] = node_path
        processed_node["attributes"]["file_path"] = file_path
        processed_node["attributes"]["level"] = parent_level + 1
        processed_node["attributes"]["leaf"] = leaf


        processed_node["type"] = type_node

        global_imports[node_path] = {
            "id": processed_node["attributes"]["node_id"],
            "type": processed_node["type"],
        }
        visited_nodes[node.node_id] = {"path": node_path, "level": parent_level + 1}
        return processed_node, relationships

    def _get_imports(self, path: str, file_node_id: str, root_path: str) -> dict:
        parser = tree_sitter_languages.get_parser(self.language)
        with open(path, "r") as file:
            code = file.read()
        tree = parser.parse(bytes(code, "utf-8"))

        imports = {"_*wildcard*_": {"path": [], "alias": "", "type": "wildcard"}}
        for node in tree.root_node.children:
            # From Statement Case
            if node.type == "import_from_statement":
                import_statements = node.named_children

                from_statement = import_statements[0]
                from_text = from_statement.text.decode()
                for import_statement in import_statements[1:]:
                    if import_statement.text.decode() == self.wildcard:
                        imports["_*wildcard*_"]["path"].append(self.resolve_import_path(from_text, path, root_path))
                    imports[import_statement.text.decode()] = {
                        "path": self.resolve_import_path(from_text, path, root_path),
                        "alias": "",
                        "type": "import_from_statement",
                    }
            # Direct Import Case
            elif node.type == "import_statement":
                import_statement = node.named_children[0]
                from_text = import_statement.text.decode()

                if import_statement.type == "aliased_import":
                    # If the import statement is aliased
                    from_statement, _, alias = import_statement.children
                    from_text = from_statement.text.decode()
                    imports[alias.text.decode()] = {
                        "path": self.resolve_import_path(from_text, path, root_path),
                        "alias": alias.text.decode(),
                        "type": "aliased_import",
                    }
                else:
                    # If it's a simple import statement
                    imports[import_statement.text.decode()] = {
                        "path": self.resolve_import_path(from_text, path, root_path),
                        "alias": "",
                        "type": "import_statement",
                    }
        return {file_node_id: imports}

    @abstractmethod
    def resolve_import_path(self, from_text: str, path: str, root_path: str):
        pass

    @abstractmethod
    def _remove_extensions(self, path: str) -> str:
        pass

    @abstractmethod
    def is_package(self, directory: str) -> bool:
        pass

    @abstractmethod
    def skip_directory(self, directory: str) -> bool:
        pass
