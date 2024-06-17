from collections import deque

def process_node(graph, node):
    node_data = graph.nodes[node]
    code = node_data.get("text", "")
    if code == "":
        print("code is empty", node_data.get("signature"), node_data.get("type"), node_data.get("file_path"))
    doc = node_data.get("doc", "")
    if doc == "":
        print("doc is empty", node_data.get("signature"), node_data.get("type"))
    metadata = {
        "type": node_data.get("type", ""),
        "name": node_data.get("name", ""),
        "file_path": node_data.get("file_path", ""),
        "start_line": node_data.get("start_line", ""),
        "end_line": node_data.get("end_line", ""),
        "node_id": node_data.get("node_id", ""),
        "file_node_id": node_data.get("file_node_id", ""),
        "signature": node_data.get("signature", ""),
        "leaf": node_data.get("leaf", ""),
    }

    if metadata == None:
        metadata = {}

    return node, doc, metadata, code

def extract_chromadb_values(graph, edge_types=["FUNCTION_DEFINITION", "CLASS_DEFINITION", "CONTAINS"]):
    root_node = graph.graph["root_node_id"]

    queue = deque([root_node])
    visited = set()

    node_ids = []
    docs = []
    metadatas = []
    codes = []

    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            try:
                if graph.nodes[node].get("type") != "directory":
                    node_id, doc, metadata, code = process_node(graph, node)
                    node_ids.append(node_id)
                    docs.append(doc)
                    metadatas.append(metadata)
                    codes.append(code)
            except ValueError as e:
                print(f"Error processing node {node}: {str(e)}")
            child_nodes = [target for _, target, data in graph.out_edges(node, data=True) if data['type'] in edge_types]
            queue.extend(child_nodes)

    return node_ids, docs, metadatas, codes