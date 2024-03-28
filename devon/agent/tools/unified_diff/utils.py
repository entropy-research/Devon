from devon.agent.tools.unified_diff.create_diff import FileDiff, MultiFileDiff

# def apply_diff_to_file(original_code: str, diff: FileDiff) -> str:
#     result_lines = original_code.splitlines()

#     hunks = reversed(diff.hunks)
#     for hunk in hunks:
#         src_start = hunk.src_start - 1
#         src_end = src_start + hunk.src_lines
#         tgt_start = hunk.tgt_start - 1
#         tgt_end = tgt_start + hunk.tgt_lines

#         # Replace the original lines with the modified lines from the hunk

#         print(result_lines[src_start:src_end])
#         print([line.content for line in hunk.lines if line.type != "removed"])
#         result_lines[src_start:src_end] = [line.content for line in hunk.lines if line.type != "removed"]
#         # result_lines[tgt_start:tgt_end] = [line.content for line in hunk.lines if line.type != "removed"]

#     return "\n".join(result_lines)
def apply_diff_to_file(original_code: str, diff: FileDiff) -> str:
    result_lines = original_code.splitlines()
    hunks = reversed(diff.hunks)
    
    for hunk in hunks:
        src_start = hunk.src_start - 1
        src_end = src_start + hunk.src_lines
        
        # Create a new list to store the modified lines
        modified_lines = []
        
        # Iterate over the lines in the hunk
        for line in hunk.lines:
            if line.type == "added" or line.type == "unchanged":
                # Add the line to the modified lines list
                modified_lines.append(line.content)
        
        # Replace the original lines with the modified lines
                
        # print(src_start, src_end)
        # print(result_lines[src_start:src_end])
        # print(modified_lines)
        result_lines[src_start:src_end] = modified_lines
    
    return "\n".join(result_lines)

def apply_diff_to_file_map(file_code_mapping: dict, diff: MultiFileDiff) -> (dict, list):
    updated_files = {}
    touched_files = []

    for file_diff in diff.files:
        file_path = file_diff.tgt_file
        if file_path in file_code_mapping:
            original_code = file_code_mapping[file_path]
            result_lines = apply_diff_to_file(original_code, file_diff)
            updated_files[file_path] = result_lines
            touched_files.append(file_path)
        else:
            file_code_mapping[file_path] = apply_diff_to_file("", file_diff)
            # print(f"Warning: File '{file_path}' not found in the file code mapping.")

    # Add untouched files to the updated_files dictionary
    for file_path, original_code in file_code_mapping.items():
        if file_path not in touched_files:
            updated_files[file_path] = original_code

    return updated_files, touched_files
