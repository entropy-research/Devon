import asyncio
from collections import deque
from devon_agent.semantic_search.llm import get_completion, run_model_completion, code_explainer_and_summary_prompt, code_explainer_and_summary_prompt_groq, get_completion_groq, code_summary_prompt, directory_summary_prompt
import openai
import os
import yaml



async def process_code_node(graph, node, model_name):
    node_data = graph.nodes[node]
    code = node_data.get("text", "")
    retries = 8
    wait_time = 10  # seconds
    max_retries_no_status = 3  # max retries if exception does not have status_code attribute
    rate_limit_encountered = False
    doc = None
    summary = None

    # Gather child summaries and signatures
    child_nodes = [target for _, target in graph.out_edges(node)]
    children_summaries = []
    for child in child_nodes:
        child_data = graph.nodes[child]
        child_summary = child_data.get("summary", "")
        child_signature = child_data.get("signature", "")
        if child_summary and child_signature:
            children_summaries.append(f"{child_signature}\n{child_summary}")
    children_summaries_text = "\n".join(children_summaries)

    for attempt in range(retries):
        try:
            if model_name == "groq":
                doc = await run_model_completion(model_name, code_explainer_and_summary_prompt_groq(code, children_summaries_text))
                summary = await run_model_completion(model_name, code_summary_prompt(code))
            else:
                result = await run_model_completion(model_name, code_explainer_and_summary_prompt(code, children_summaries_text))
                doc_start = result.find("<description>") + len("<description>")
                doc_end = result.find("</description>")
                summary_start = result.find("<summary>") + len("<summary>")
                summary_end = result.find("</summary>")
                
                doc = result[doc_start:doc_end].strip()
                summary = result[summary_start:summary_end].strip()

            break  # If the call succeeds, exit the loop
        except Exception as e:
            if isinstance(e, openai.OpenAIError):
                if hasattr(e, 'status_code'):
                    code = e.status_code
                    if code == 429:
                        if attempt < retries - 1:
                            rate_limit_encountered=True
                            print(f"Rate limit exceeded. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{retries})")
                            await asyncio.sleep(wait_time)
                        else:
                            raise e  # Raise the exception after the last attempt
                    else:
                        raise e
                else:
                    if attempt < max_retries_no_status - 1:
                        print(f"Exception without status_code. Retrying in {wait_time} seconds... (Attempt {attempt + 1}/{max_retries_no_status})")
                        await asyncio.sleep(wait_time)
                    else:
                        raise e  # Raise the exception after the max retries
            else:
                raise e
            
    # print("==========")
    # print(f"Codeblock name: {node_data.get('signature')}, {node_data.get('type')}")
    # print("Level:", node_data.get("level"))
    # print("Path:", node_data.get("path"))
    # print(code)
    # # print(doc)
    # print()

    doc += "\n\n" + summary
    graph.nodes[node]["doc"] = doc
    if summary is not None:
        graph.nodes[node]["summary"] = summary
        # print("summary", summary)

    return rate_limit_encountered, doc

async def process_level_async(graph, nodes, level, batch_size, model_name):
    rate_limits = 0
    successful_completions = 0

    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i + batch_size]
        tasks = []
        for node in batch:
            node_type = graph.nodes[node].get("type", "")
            if node_type == "directory":
                tasks.append(process_directory_node(graph, node, model_name))
                pass
            else:
                tasks.append(process_code_node(graph, node, model_name))
        results = await asyncio.gather(*tasks)
        
        for node, result in zip(batch, results):
            if isinstance(result, tuple) and result[0]:  # Check if rate_limit_encountered is True
                rate_limits += 1
            else:
                successful_completions += 1

    return rate_limits, successful_completions



def generate_doc_level_wise(graph, actions, model_name="groq", edge_types=["FUNCTION_DEFINITION", "CLASS_DEFINITION", "CONTAINS"], batch_size=30, minimum_batch = 4):
    files_to_process = actions["add"] + actions["update"]
    file_file_paths = list(map(lambda x: x[0], files_to_process))

    root_node = graph.graph["root_id"]

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

    max_level = max(node_levels.values())

    current_batch_size = batch_size
    for level in range(max_level, -1, -1):
        nodes_to_process = [
            node for node, node_level in node_levels.items()
            if node_level == level and (graph.nodes[node].get("file_path") in file_file_paths or graph.nodes[node].get("type") == "directory")
        ]

        if nodes_to_process:
            current_batch_size = max(current_batch_size, minimum_batch)
            rate_limits, successful_completions = asyncio.run(process_level_async(graph, nodes_to_process, level, batch_size=current_batch_size, model_name=model_name))
            if rate_limits > len(nodes_to_process) * 0.2:  # More than 20% rate limits
                current_batch_size = max(1, current_batch_size // 2)
            elif rate_limits == 0:
                current_batch_size = min(current_batch_size + (current_batch_size // 10), 100)  # Increase batch size by 10% up to a max of 100

            print(f"Processed level {level} with batch size {current_batch_size}: {successful_completions} successful, {rate_limits} rate limits")



async def process_directory_node(graph, node, model_name, threshold=10, root_dir=None):
    # Use traverse_directory to get the full structure with correct file count
    directory_structure = traverse_directory(graph, node)
    file_count = directory_structure["file_count"]

    if file_count > threshold:
        # For larger directories, generate a summary using LLM
        yaml_structure = json_to_yaml(directory_structure)
        llm_summary = await run_model_completion(model_name, directory_summary_prompt(yaml_structure))
        print(yaml_structure)
        print("llm_summary", llm_summary)
        summary_json = {
            "name": directory_structure["name"],
            "path": directory_structure["path"],
            "type": "directory",
            "file_count": 0,  # Set to 0 for LLM-summarized directories
            "summary": llm_summary,
            "is_llm_summary": True  # Flag to indicate this is an LLM-generated summary
        }
    else:
        # For smaller directories, use the structure as is
        summary_json = directory_structure

    # Update the node's summary_json
    graph.nodes[node]["summary_json"] = summary_json

    # if True:
    #     print(file_count)
    #     print(generate_summary_from_json(summary_json, root_dir))

    return summary_json


def traverse_directory(graph, node):
    node_data = graph.nodes[node]
    
    # If this node has a pre-computed summary_json, use it
    if "summary_json" in node_data:
        return node_data["summary_json"]
    
    result = {
        "name": os.path.basename(node_data.get("file_path", "")),
        "path": node_data.get("file_path", ""),
        "type": node_data.get("type", ""),
    }
    
    # For files or directories with summaries
    if "summary" in node_data:
        result["summary"] = node_data["summary"]
    
    # Calculate file count
    if result["type"] == "file":
        result["file_count"] = 1
    else:  # For directories
        result["children"] = []
        file_count = 1  # Count the directory itself
        for _, child in graph.out_edges(node):
            child_result = traverse_directory(graph, child)
            if child_result:
                result["children"].append(child_result)
                file_count += child_result["file_count"]
        result["file_count"] = file_count
    
    # Save the computed result in the graph node
    graph.nodes[node]["summary_json"] = result
    
    return result


def json_to_yaml(json_data):
    try:
        def convert_node(node):
            if node['type'] == 'file':
                return {node['name']: node.get('summary', '')}
            elif node['type'] == 'directory':
                dir_content = {}
                if node.get('file_count', 0) == 0 and 'summary' in node:
                    dir_content['summary'] = node['summary']

                for child in node.get('children', []):
                    child_content = convert_node(child)
                    if isinstance(child_content, dict):
                        dir_content.update(child_content)
                    else:
                        dir_content[child] = ''

                # If directory is empty, return it as an empty dict
                return {node['name']: dir_content or {}}
        
        # Convert JSON data to nested dictionary
        yaml_data = convert_node(json_data)

        # Convert nested dictionary to YAML string
        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
    except Exception as e:
        return f"Error converting JSON to YAML: {str(e)}"
    

def generate_summary_from_json(json_data, root_dir):
    # Check if it's an LLM-generated summary
    if json_data.get("is_llm_summary", False) and "summary" in json_data:
        return json_data["summary"]


    # Convert JSON to YAML
    yaml_structure = json_to_yaml(json_data)
    yaml_string = f"relative directory path from project root: {os.path.relpath(json_data['path'], start=root_dir)}\n"
    return (yaml_string + yaml_structure)
