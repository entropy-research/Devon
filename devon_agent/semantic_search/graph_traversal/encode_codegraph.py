import asyncio
from collections import deque
from devon_agent.semantic_search.llm import (get_completion, code_explainer_prompt)
import anyio

async def process_node(graph, node):
    node_data = graph.nodes[node]
    code = node_data.get("text", "")
    
    doc = await get_completion(code_explainer_prompt(code), model="anthropic")

    print("here4")
    
    print("==========")
    print(f"Codeblock name: {node_data.get('signature')}, {node_data.get('type')}")
    print("Level:", node_data.get("level"))
    print("Path:", node_data.get("path"))
    # print(code)
    # print(doc)
    print()
    graph.nodes[node]["doc"] = doc
    return code

async def process_node_async(graph, node, retries=1):
    for attempt in range(retries):
        try:
            result = await process_node(graph, node)
            return result
        except Exception as e:
            print(f"Max retries reached for node {node}")
    return None

async def process_level_async(graph, nodes, level, retries=2, batch_size=70):
    print("here3")
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i + batch_size]
        tasks = [process_node_async(graph, node, retries=retries) for node in batch]
        results = await asyncio.gather(*tasks)
        for node, result in zip(batch, results):
            # print("Code:\n" + result)
            pass

async def generate_doc_level_wise(graph, edge_types=["FUNCTION_DEFINITION", "CLASS_DEFINITION", "CONTAINS"], batch_size=30):
    root_node = graph.graph["root_node_id"]

    print("here2")

    # Perform a breadth-first search (BFS) starting from the root node
    queue = deque([(root_node, 0)])
    visited = set()
    node_levels = {}

    while queue:
        node, level = queue.popleft()
        if node not in visited:
            visited.add(node)
            node_levels[node] = level
            child_nodes = [target for _, target, data in graph.out_edges(node, data=True) if data['type'] in edge_types]
            for child_node in child_nodes:
                queue.append((child_node, level + 1))

    # Find the maximum level among the descendants of the root node
    max_level = max(node_levels.values())

    # Process nodes level by level, starting from the maximum level
    for level in range(max_level, -1, -1):
        nodes_to_process = [
            node for node, node_level in node_levels.items() 
            if node_level == level and graph.nodes[node].get("type", "directory") != "directory"
        ]
        if nodes_to_process:
            await process_level_async(graph, nodes_to_process, level, batch_size=batch_size)
