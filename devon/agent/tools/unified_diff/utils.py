<<<<<<< HEAD
from devon.agent.tools.unified_diff.create_diff import FileDiff, MultiFileDiff
import os

=======
import difflib
from devon.agent.tools.unified_diff.create_diff import FileDiff, MultiFileDiff, construct_versions_from_diff_hunk
import os

from devon.agent.tools.unified_diff.diff_types import MultiFileDiff2

>>>>>>> 0f6851b (new coding)
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

def first_and_last_content_lines(lines):
    start = 0
    for i, line in enumerate(lines):
        if line != '':
            start = i
            break
    
    end = 0
    for i, line in enumerate(reversed(lines)):
        if line != '':
            end = i
            break
    
    return start, end


def match_stripped_lines(file_lines, old_block):

    stripped_file_lines = [line.strip() for line in file_lines]
    old_lines = [line.strip() for line in old_block.splitlines()]

    start, end  = first_and_last_content_lines(old_lines)

    print(old_block)
    print(old_lines)
    
    i = 0
    while i < len(stripped_file_lines):
        if len(old_lines) > 0 and stripped_file_lines[i] == old_lines[start]:
            print("matched")
            j = 1
            while i + j < len(stripped_file_lines) and stripped_file_lines[i + j] == old_lines[-end]:
                j += 1

            if len(old_lines) <= i + j:
                start_line = i  # Add 1 to convert from 0-based index to 1-based line number
                end_line = i + j
                return start_line, end_line
            else:
                i += 1
        else:
            i += 1
    
    return None, None


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
<<<<<<< HEAD
                    for line in hunk.lines:
                        if line.type != "removed":
                            f.write(line.content)
=======
                    to_write = [line.content for line in hunk.lines if line.type != "removed"]
                    f.write("\n".join(to_write))
>>>>>>> 0f6851b (new coding)
        elif tgt_file == "/dev/null":
            # Deleting a file
            os.remove(src_file)
        else:
            # Modifying an existing file
            with open(src_file, "r") as src, open(tgt_file, "w") as tgt:
                src_lines = src.readlines()
                tgt_lines = []
<<<<<<< HEAD

                for hunk in file_diff.hunks:
                    src_idx = hunk.src_start - 1
                    tgt_idx = hunk.tgt_start - 1

                    # Copy unchanged lines until the hunk start
                    while src_idx < hunk.src_start - 1:
                        tgt_lines.append(src_lines[src_idx])
                        src_idx += 1
                        tgt_idx += 1
=======
                src_idx = 0

                for hunk in file_diff.hunks:
                    # Copy unchanged lines until the hunk start

                    while src_idx < hunk.src_start - 1 and src_idx < len(src_lines):
                        print(src_idx)
                        print(len(src_lines))
                        print(hunk.src_start)
                        tgt_lines.append(src_lines[src_idx])
                        src_idx += 1
>>>>>>> 0f6851b (new coding)

                    # Process hunk lines
                    for line in hunk.lines:
                        if line.type == "added":
                            tgt_lines.append(line.content)
<<<<<<< HEAD
                            tgt_idx += 1
=======
>>>>>>> 0f6851b (new coding)
                        elif line.type == "removed":
                            src_idx += 1
                        else:
                            tgt_lines.append(line.content)
                            src_idx += 1
<<<<<<< HEAD
                            tgt_idx += 1
=======
>>>>>>> 0f6851b (new coding)

                # Copy remaining unchanged lines after the last hunk
                while src_idx < len(src_lines):
                    tgt_lines.append(src_lines[src_idx])
                    src_idx += 1

<<<<<<< HEAD
                tgt.writelines(tgt_lines)
=======
                tgt.write("\n".join(tgt_lines))

def apply_diff2(multi_file_diff: MultiFileDiff2):
    for file_diff in multi_file_diff.files:
        src_file = file_diff.src_file
        tgt_file = file_diff.tgt_file

        print(src_file, tgt_file)

        if src_file == "/dev/null":
            # Creating a new file
            with open(tgt_file, "w") as f:
                for hunk in file_diff.hunks:
                    to_write = [line.content for line in hunk.lines if line.type != "removed"]
                    # f.write("\n".join(to_write))
        elif tgt_file == "/dev/null":
            # Deleting a file
            # os.remove(src_file)
            pass
        else:
            # Modifying an existing file
            with open(src_file, "r") as src:
                src_lines = src.readlines()
                tgt_lines = src_lines
                src_idx = 0

                for hunk in file_diff.hunks:
                    # Copy unchanged lines until the hunk start


                    old, new  = construct_versions_from_diff_hunk(hunk)

                    start, end = match_stripped_lines(src_lines, old)
                    
                    print(start, end)
                    if start and end:
                        tgt_lines[start:end] = new.splitlines()

                    # while src_idx < hunk.src_start - 1 and src_idx < len(src_lines):
                    #     print(src_idx)
                    #     print(len(src_lines))
                    #     print(hunk.src_start)
                    #     tgt_lines.append(src_lines[src_idx])
                    #     src_idx += 1

                    # # Process hunk lines
                    # for line in hunk.lines:
                    #     if line.type == "added":
                    #         tgt_lines.append(line.content)
                    #     elif line.type == "removed":
                    #         src_idx += 1
                    #     else:
                    #         tgt_lines.append(line.content)
                    #         src_idx += 1

                # Copy remaining unchanged lines after the last hunk
                # while src_idx < len(src_lines):
                #     tgt_lines.append(src_lines[src_idx])
                #     src_idx += 1
                

                # print("\n".join(tgt_lines))
                # with open(tgt_file, "w") as tgt:
                    # tgt.write("\n".join(tgt_lines))
>>>>>>> 0f6851b (new coding)
