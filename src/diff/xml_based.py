import xmltodict
from typing import List
from diff.unified_diff import UnifiedDiff, Hunk

def apply_xml_diff(original_lines: str, diff: UnifiedDiff) -> List[str]:
    result_lines = original_lines.splitlines()[:]

    for hunk in diff.hunks:
        src_start = hunk.src_start - 1
        src_end = src_start + hunk.src_lines
        tgt_start = hunk.tgt_start - 1
        tgt_end = tgt_start + hunk.tgt_lines

        # Replace the original lines with the modified lines from the hunk
        result_lines[src_start:src_end] = hunk.lines.splitlines()

    return "".join(result_lines)

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

    hunk = Hunk(src_start=src_start, src_lines=src_lines, tgt_start=tgt_start, tgt_lines=tgt_lines, lines=lines)

    # Create a UnifiedDiff object with the hunks
    unified_diff = UnifiedDiff(src_file=src_file, tgt_file=tgt_file, hunks=[hunk])

    return unified_diff