

import json

def transform_json_to_jsonl(input_file_path, output_file_path):
    """
    Transforms a JSON file to a JSON Lines file.

    Parameters:
    - input_file_path: str, the path to the input JSON file.
    - output_file_path: str, the path to the output JSON Lines file.
    """
    try:
        # Open the input JSON file and load the data
        with open(input_file_path, 'r') as json_file:
            data = json.load(json_file)
        
        # Open the output JSON Lines file in write mode
        with open(output_file_path, 'w') as jsonl_file:
            # Iterate over each item in the data (assuming it's a list)
            for item in data:
                # Convert each item to a JSON string and write it to the file with a newline
                jsonl_file.write(json.dumps(item) + '\n')
                
        print(f"Successfully transformed JSON to JSONL. Output file: {output_file_path}")
    except Exception as e:
        print(f"Error during transformation: {e}")

# Example usage
transform_json_to_jsonl('predictions_for_swebench.json', 'predictions_for_swebench.jsonl')
