import json

import networkx as nx


def create_graph():
    """
    Creates a new directed graph for representing the Python codebase.
    Returns:
        nx.DiGraph: The created graph.
    """
    graph = nx.DiGraph(name="Python Codebase Graph")
    graph.graph["node_attrs"] = {
        "type": None,
        "code": None,
        "doc": None,
        "location": {
            "file_path": None,
            "start_line": None,
            "end_line": None,
        },
        "dependencies": {
            "imports": [],
            "exported": [],
        },
    }
    graph.graph["edge_types"] = {
        "calls": {
            "ref_location": {
                "file_path": None,
                "line_number": None,
            }
        },
        "imports": {
            "ref_location": {
                "file_path": None,
                "line_number": None,
            }
        },
    }
    graph.graph["total_nodes"] = 0
    graph.graph["total_edges"] = 0
    graph.graph["disconnected_components"] = []
    return graph


def add_node(graph, node_id, node_attrs):
    """
    Adds a new node to the graph with the specified attributes.
    Args:
        graph (nx.DiGraph): The graph to add the node to.
        node_id (str): The unique identifier for the node.
        node_attrs (dict): The attributes of the node.
    """
    graph.add_node(node_id, **node_attrs)
    graph.graph["total_nodes"] += 1


def add_edge(graph, source, target, edge_type, ref_location):
    """
    Adds a new edge to the graph with the specified attributes.
    Args:
        graph (nx.DiGraph): The graph to add the edge to.
        source (str): The source node of the edge.
        target (str): The target node of the edge.
        edge_type (str): The type of the edge.
        ref_location (dict): The reference location of the edge.
    """
    graph.add_edge(source, target, type=edge_type, ref_location=ref_location)
    graph.graph["total_edges"] += 1


def get_node_attrs(graph, node_id):
    """
    Retrieves the attributes of a node in the graph.
    Args:
        graph (nx.DiGraph): The graph containing the node.
        node_id (str): The unique identifier of the node.
    Returns:
        dict: The attributes of the node.
    """
    return graph.nodes[node_id]


def get_edge_attrs(graph, source, target):
    """
    Retrieves the attributes of an edge in the graph.
    Args:
        graph (nx.DiGraph): The graph containing the edge.
        source (str): The source node of the edge.
        target (str): The target node of the edge.
    Returns:
        dict: The attributes of the edge.
    """
    return graph.edges[source, target]


def get_neighbors(graph, node_id):
    """
    Retrieves the neighbors of a node in the graph.
    Args:
        graph (nx.DiGraph): The graph containing the node.
        node_id (str): The unique identifier of the node.
    Returns:
        list: The neighbors of the node.
    """
    return list(graph.neighbors(node_id))


def get_successors(graph, node_id):
    """
    Retrieves the successors (outgoing neighbors) of a node in the graph.
    Args:
        graph (nx.DiGraph): The graph containing the node.
        node_id (str): The unique identifier of the node.
    Returns:
        list: The successors of the node.
    """
    return list(graph.successors(node_id))


def get_predecessors(graph, node_id):
    """
    Retrieves the predecessors (incoming neighbors) of a node in the graph.
    Args:
        graph (nx.DiGraph): The graph containing the node.
        node_id (str): The unique identifier of the node.
    Returns:
        list: The predecessors of the node.
    """
    return list(graph.predecessors(node_id))


def get_connected_components(graph):
    """
    Retrieves the connected components of the graph.
    Args:
        graph (nx.DiGraph): The graph to analyze.
    Returns:
        list: The connected components of the graph.
    """
    return list(nx.weakly_connected_components(graph))


def get_cycles(graph):
    """
    Retrieves the cycles in the graph.
    Args:
        graph (nx.DiGraph): The graph to analyze.
    Returns:
        list: The cycles in the graph.
    """
    return list(nx.simple_cycles(graph))


def get_topological_sort(graph):
    """
    Performs a topological sort on the graph.
    Args:
        graph (nx.DiGraph): The graph to sort.
    Returns:
        list: The nodes in topological order.
    """
    return list(nx.topological_sort(graph))


def get_shortest_path(graph, source, target):
    """
    Finds the shortest path between two nodes in the graph.
    Args:
        graph (nx.DiGraph): The graph to search.
        source (str): The source node.
        target (str): The target node.
    Returns:
        list: The nodes in the shortest path from source to target.
    """
    return nx.shortest_path(graph, source, target)


def get_all_paths(graph, source, target):
    """
    Finds all paths between two nodes in the graph.
    Args:
        graph (nx.DiGraph): The graph to search.
        source (str): The source node.
        target (str): The target node.
    Returns:
        list: All paths from source to target.
    """
    return list(nx.all_simple_paths(graph, source, target))


class CodeGraph:
    def __init__(self, graph=None):
        """
        Creates a new directed graph for representing the Python codebase.
        Returns:
            nx.DiGraph: The created graph.
        """
        if graph is not None:
            self.graph = graph
        else:
            graph = nx.DiGraph(name="Python Codebase Graph")
            graph.graph["node_attrs"] = {
                "type": None,
                "code": None,
                "doc": None,
                "location": {
                    "file_path": None,
                    "start_line": None,
                    "end_line": None,
                },
                "dependencies": {
                    "imports": [],
                    "exported": [],
                },
            }
            graph.graph["edge_types"] = {
                "calls": {
                    "ref_location": {
                        "file_path": None,
                        "line_number": None,
                    }
                },
                "imports": {
                    "ref_location": {
                        "file_path": None,
                        "line_number": None,
                    }
                },
            }
            graph.graph["total_nodes"] = 0
            graph.graph["total_edges"] = 0
            graph.graph["disconnected_components"] = []

            self.graph: nx.DiGraph = graph

    def to_json(self):
        from networkx.readwrite import json_graph

        jg = json_graph.adjacency_data(self.graph)
        return jg

    @classmethod
    def from_json_dict(cls, json_dict):
        from networkx.readwrite import json_graph

        graph = json_graph.adjacency_graph(json_dict)
        return cls(graph)

    @classmethod
    def from_json(cls, json_str):
        from networkx.readwrite import json_graph

        jg = json.loads(json_str)
        graph = json_graph.adjacency_graph(jg)
        return cls(graph)
