import re

import tree_sitter_languages
from tree_sitter import Language, Node


def remove_non_ascii(text):
    # Define the regular expression pattern to match ascii characters
    pattern = re.compile(r"[^\x00-\x7F]+")
    # Replace ascii characters with an empty string
    cleaned_text = pattern.sub("", text)
    return cleaned_text


def traverse_tree(tree):
    cursor = tree.walk()
    visited_children = False
    while True:
        if not visited_children:
            yield cursor.node
            if not cursor.goto_first_child():
                visited_children = True
        elif cursor.goto_next_sibling():
            visited_children = False
        elif not cursor.goto_parent():
            break


def get_function_name(call_str):
    match = re.match(r"([a-zA-Z_][\w\.]*)\s*\(", call_str)
    if match:
        return match.group(1)  # Return the captured function name
    else:
        return None  # No function name found


def decompose_function_call(call_node: Node, language: Language, decomposed_calls=[]):
    calls_query = language.query(
        """
        (attribute
            object: [
                (identifier) @object
                ((attribute) @nested_object
                attribute: _ @nested_method)
            ]
            attribute: _ @method)
        """
    )

    decompose_call = calls_query.captures(call_node)

    if len(decompose_call) == 0:
        decomposed_calls.append(call_node.text.decode())
        return decomposed_calls

    nested_object = False
    for decompose_node, type in decompose_call:
        if type == "nested_object":
            nested_object = True
            decomposed_calls = decompose_function_call(decompose_node, language, decomposed_calls)
        elif (type == "object" or type == "method") and nested_object:
            continue
        else:
            decomposed_calls.append(decompose_node.text.decode())

    return decomposed_calls


def get_function_calls(node: Node, assignments_dict: dict, language: str) -> list[str]:
    code_text = node.text
    function_calls = []

    parser = tree_sitter_languages.get_parser(language)
    tree = parser.parse(bytes(code_text, "utf-8"))
    language = tree_sitter_languages.get_language(language)

    assignment_query = language.query("""(assignment left: _ @variable right: _ @expression)""")

    assignments = assignment_query.captures(tree.root_node)

    for assignment_node, assignment_type in assignments:
        if assignment_type == "variable":
            variable_identifier_node = assignment_node
            variable_identifier = variable_identifier_node.text.decode()
            if "self." in variable_identifier:
                for scope in node.metadata["inclusive_scopes"]:
                    if scope["type"] == "class_definition":
                        variable_identifier = scope["name"] + "." + variable_identifier.split("self.")[1]
                        break
            continue

        if assignment_type == "expression":
            assign_value = assignment_node

            if assign_value.type == "call":
                expression = assign_value
                expression_identifier = expression.named_children[0].text.decode()
                assignments_dict[variable_identifier] = expression_identifier
                continue

            assignments_dict[variable_identifier] = assign_value.text.decode()

    calls_query = language.query("""(call function: _ @function_call)""")

    function_calls_nodes = calls_query.captures(tree.root_node)

    for call_node, _ in function_calls_nodes:
        decomposed_call = decompose_function_call(call_node, language, [])
        called_from_assignment = False

        join_call = decomposed_call[0]
        for index, call in enumerate(decomposed_call):
            if index != 0:
                join_call += "." + call

            if "self." in join_call:
                for scope in node.metadata["inclusive_scopes"]:
                    if scope["type"] == "class_definition":
                        join_call = scope["name"] + "." + join_call.split("self.")[1]
                        break

            if assignments_dict.get(join_call):
                function_calls.append(assignments_dict[join_call] + "." + ".".join(decomposed_call[index + 1 :]))
                called_from_assignment = True
                break

        if not called_from_assignment:
            node_text = call_node.text.decode()
            if "self." in node_text:
                for scope in node.metadata["inclusive_scopes"]:
                    if scope["type"] == "class_definition":
                        node_text = scope["name"] + "." + node_text.split("self.")[1]
                        break
            function_calls.append(node_text)

    return function_calls


def get_inheritances(node: Node, language: str) -> list[str]:
    code_text = node.text

    parser = tree_sitter_languages.get_parser(language)
    tree = parser.parse(bytes(code_text, "utf-8"))
    node_names = map(lambda node: node, traverse_tree(tree))

    inheritances = []

    for tree_node in node_names:
        if tree_node.type == "class_definition":
            statement_children = tree_node.children
            for child in statement_children:
                if child.type == "argument_list":
                    for argument in child.named_children:
                        if argument.type == "identifier":
                            inheritances.append(argument.text.decode("utf-8"))

    return inheritances
