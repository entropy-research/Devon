from devon.agent.tools.unified_diff.create_diff import FileDiff, MultiFileDiff
import os

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

def apply_diff(multi_file_diff: MultiFileDiff):
    for file_diff in multi_file_diff.files:
        src_file = file_diff.src_file
        tgt_file = file_diff.tgt_file

        if src_file == "/dev/null":
            # Creating a new file
            with open(tgt_file, "w") as f:
                for hunk in file_diff.hunks:
                    for line in hunk.lines:
                        if line.type != "removed":
                            f.write(line.content)
        elif tgt_file == "/dev/null":
            # Deleting a file
            os.remove(src_file)
        else:
            # Modifying an existing file
            with open(src_file, "r") as src, open(tgt_file, "w") as tgt:
                src_lines = src.readlines()
                tgt_lines = []

                for hunk in file_diff.hunks:
                    src_idx = hunk.src_start - 1
                    tgt_idx = hunk.tgt_start - 1

                    # Copy unchanged lines until the hunk start
                    while src_idx < hunk.src_start - 1:
                        tgt_lines.append(src_lines[src_idx])
                        src_idx += 1
                        tgt_idx += 1

                    # Process hunk lines
                    for line in hunk.lines:
                        if line.type == "added":
                            tgt_lines.append(line.content)
                            tgt_idx += 1
                        elif line.type == "removed":
                            src_idx += 1
                        else:
                            tgt_lines.append(line.content)
                            src_idx += 1
                            tgt_idx += 1

                # Copy remaining unchanged lines after the last hunk
                while src_idx < len(src_lines):
                    tgt_lines.append(src_lines[src_idx])
                    src_idx += 1

                tgt.writelines(tgt_lines)