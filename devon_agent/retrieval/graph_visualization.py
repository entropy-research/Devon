# graph_visualization.py


def print_nodes_with_children(graph):
    """
    Prints all the nodes in the graph along with their child nodes.
    Args:
        graph (nx.DiGraph): The graph representing the codebase.
    """
    print("Nodes with Child Nodes:")
    print("----------------------")

    for node in graph.nodes:
        child_nodes = list(graph.successors(node))
        if child_nodes:
            print(f"Node: {node}")
            print("Child Nodes:")
            for child in child_nodes:
                print(f"  - {child}")
            print()


def print_node_details(graph):
    """
    Prints all the nodes in the graph along with their details.
    Args:
        graph (nx.DiGraph): The graph representing the codebase.
    """
    print("Node Details:")
    print("-------------")

    for node in graph.nodes:
        node_attrs = graph.nodes[node]

        print(f"Node Name: {node}")
        print(f"Node Type: {node_attrs.get('type', 'Unknown')}")

        child_nodes = list(graph.successors(node))
        if child_nodes:
            print("Child Nodes:")
            for child in child_nodes:
                print(f"  - {child}")
        else:
            print("No Child Nodes")

        parent_nodes = list(graph.predecessors(node))
        if parent_nodes:
            print("Parent Nodes:")
            for parent in parent_nodes:
                print(f"  - {parent}")
        else:
            print("No Parent Nodes")

        called_functions = []
        for _, dest_node, edge_attrs in graph.out_edges(node, data=True):
            if edge_attrs.get("type") == "calls":
                called_functions.append(dest_node)

        if called_functions:
            print("Called Functions:")
            for func in called_functions:
                print(f"  - {func}")
        else:
            print("No Called Functions")

        # print("Node Attributes:")
        # for attr, value in node_attrs.items():
        #     print(f"  - {attr}: {value}")

        print()


def print_node_attributes(graph, node):
    """
    Prints the attributes of a specific node in the graph.
    Args:
        graph (nx.DiGraph): The graph representing the codebase.
        node (str): The name of the node.
    """
    if node in graph.nodes:
        attributes = graph.nodes[node]
        print(f"Node: {node}")
        print("Attributes:")
        for attr, value in attributes.items():
            print(f"  - {attr}: {value}")
    else:
        print(f"Node '{node}' not found in the graph.")


def print_file_functions(graph, file_path):
    """
    Prints all the functions defined in a specific file.
    Args:
        graph (nx.DiGraph): The graph representing the codebase.
        file_path (str): The path of the file.
    """
    print(f"Functions in file: {file_path}")
    print("----------------------------")

    for node in graph.nodes:
        if (
            graph.nodes[node].get("type") == "function"
            and graph.nodes[node].get("location", {}).get("file_path") == file_path
        ):
            print(node)


def print_function_calls(graph, function_name):
    """
    Prints all the functions called by a specific function.
    Args:
        graph (nx.DiGraph): The graph representing the codebase.
        function_name (str): The name of the function.
    """
    print(f"Functions called by: {function_name}")
    print("----------------------------")

    if function_name in graph.nodes:
        for successor in graph.successors(function_name):
            if graph.nodes[successor].get("type") == "function":
                print(successor)
    else:
        print(f"Function '{function_name}' not found in the graph.")
