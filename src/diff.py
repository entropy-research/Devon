from pydantic import BaseModel
from typing import List
import xmltodict


class Hunk(BaseModel):
    src_start: int
    src_lines: int
    tgt_start: int
    tgt_lines: int
    lines: str

class UnifiedDiff(BaseModel):
    src_file: str
    tgt_file: str
    hunks: List[Hunk]

def apply_diff(file_code_mapping: dict, diff: UnifiedDiff) -> (dict, list):
    updated_files = {}
    touched_files = []
    for file_path, original_code in file_code_mapping.items():
        if file_path == diff.src_file or file_path == diff.tgt_file:
            result_lines = original_code.splitlines()[:]
            for hunk in diff.hunks:
                src_start = hunk.src_start - 1
                src_end = src_start + hunk.src_lines
                tgt_start = hunk.tgt_start - 1
                tgt_end = tgt_start + hunk.tgt_lines

                # Replace the original lines with the modified lines from the hunk
                result_lines[src_start:src_end] = hunk.lines.splitlines()
            updated_files[file_path] = "\n".join(result_lines)
            touched_files.append(file_path)
        else:
            updated_files[file_path] = original_code
    return updated_files, touched_files

def xml_to_unified_diff(xml_data):
    # Parse the XML data into a dictionary
    data_dict = xmltodict.parse(xml_data)

    # Extract the source and target file names
    src_file = data_dict['root']['src_file']
    tgt_file = data_dict['root']['tgt_file']

    # Extract the hunks data

    hunk_data = data_dict['root']['hunks']

    if "hunk" in hunk_data:
        hunk_data=hunk_data["hunk"]
    elif "Hunk" in hunk_data:
        hunk_data=hunk_data["Hunk"]

    # Create Hunk objects from the parsed data

    src_start = int(hunk_data['src_start'])
    src_lines = int(hunk_data['src_lines'])
    tgt_start = int(hunk_data['tgt_start'])
    tgt_lines = int(hunk_data['tgt_lines'])
    lines = hunk_data['lines']
    # for line in :
    #     if "line" not in line:
    #         text = line
    #     else:
    #         text = line['line']

    #     lines.append(text)

    hunk = Hunk(src_start=src_start, src_lines=src_lines, tgt_start=tgt_start, tgt_lines=tgt_lines, lines=lines)

    # Create a UnifiedDiff object with the hunks
    unified_diff = UnifiedDiff(src_file=src_file, tgt_file=tgt_file, hunks=[hunk])

    return unified_diff
