import math
import re
from difflib import SequenceMatcher
from pathlib import Path

from devon_agent.tool import Tool, ToolContext

# from .editblock_prompts import EditBlockPrompts
import re
from pathlib import Path
from difflib import SequenceMatcher

from devon_agent.tools.utils import make_abs_path, read_file, write_file

class EditBlockTool(Tool):
    @property
    def name(self):
        return "edit_file"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, context: ToolContext):
        pass
        # context.state['edit_history'] = []

    def cleanup(self, context: ToolContext):
        pass
        # context.state['edit_history'] = []

    def documentation(self, format="docstring"):
        if format == "docstring":
            return """edit <edit_text>

edit contains *SEARCH/REPLACE block*.

Every *SEARCH/REPLACE block* must use this format:
1. The file path alone on a line, verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc.
2. The opening fence and code language, eg: ```python
3. The start of search block: <<<<<<< SEARCH
4. A contiguous chunk of lines to search for in the existing source code
5. The dividing line: =======
6. The lines to replace into the source code
7. The end of the replace block: >>>>>>> REPLACE
8. The closing fence: ```

Every *SEARCH* section must *EXACTLY MATCH* the existing source code, character for character, including all comments, docstrings, etc.

*SEARCH/REPLACE* blocks will replace *all* matching occurrences.
Include enough lines to make the SEARCH blocks unique.

Include *ALL* the code being searched and replaced!

Only create *SEARCH/REPLACE* blocks for files that the user has added to the chat!

To move code within a file, use 2 *SEARCH/REPLACE* blocks: 1 to delete it from its current location, 1 to insert it in the new location.

If you want to put code in a new file, use a *SEARCH/REPLACE block* with:
- A new file path, including dir name if needed
- An empty `SEARCH` section
- The new file's contents in the `REPLACE` section

Ex. 

mathweb/flask/app.py
```python
<<<<<<< SEARCH
from flask import Flask
=======
import math
from flask import Flask
>>>>>>> REPLACE
```

mathweb/flask/app.py
```python
<<<<<<< SEARCH
def factorial(n):
    "compute factorial"

    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

=======
>>>>>>> REPLACE
```

mathweb/flask/app.py
```python
<<<<<<< SEARCH
    return str(factorial(n))
=======
    return str(math.factorial(n))
>>>>>>> REPLACE
```
"""
        elif format == "manpage":
            return """NAME
edit - edit files

SYNOPSIS
edit [edit_text]

DESCRIPTION
The edit command takes a target [edit_text]. The edit_test is made of *SEARCH/REPLACE block*.

*SEARCH/REPLACE block*
Every *SEARCH/REPLACE block* must use this format:
1. The file path alone on a line, verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc.
2. The opening fence and code language, eg: ```python
3. The start of search block: <<<<<<< SEARCH
4. A contiguous chunk of lines to search for in the existing source code
5. The dividing line: =======
6. The lines to replace into the source code
7. The end of the replace block: >>>>>>> REPLACE
8. The closing fence: ```

Every *SEARCH* section must *EXACTLY MATCH* the existing source code, character for character, including all comments, docstrings, etc.

*SEARCH/REPLACE* blocks will replace *all* matching occurrences.
Include enough lines to make the SEARCH blocks unique.

Include *ALL* the code being searched and replaced!

Only create *SEARCH/REPLACE* blocks for files that the user has added to the chat!

To move code within a file, use 2 *SEARCH/REPLACE* blocks: 1 to delete it from its current location, 1 to insert it in the new location.

If you want to put code in a new file, use a *SEARCH/REPLACE block* with:
- A new file path, including dir name if needed
- An empty `SEARCH` section
- The new file's contents in the `REPLACE` section

EXAMPLES

mathweb/flask/app.py
```python
<<<<<<< SEARCH
from flask import Flask
=======
import math
from flask import Flask
>>>>>>> REPLACE
```

mathweb/flask/app.py
```python
<<<<<<< SEARCH
def factorial(n):
    "compute factorial"

    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

=======
>>>>>>> REPLACE
```

mathweb/flask/app.py
```python
<<<<<<< SEARCH
    return str(factorial(n))
=======
    return str(math.factorial(n))
>>>>>>> REPLACE
```
"""

    def function(self, context: ToolContext, *args, **kwargs):
        print("raw_command",context.get('raw_command', ''))
        raw_command = context.get('raw_command', '')
        edit_content = self._extract_edit_content(raw_command)
        if not edit_content:
            return "Error: No edit content provided"
        print("edit_content",edit_content)
        edits = list(self.find_original_update_blocks(edit_content))
        results = self.apply_edits(context, edits)

        return self._format_results(results)

    def _extract_edit_content(self, raw_command: str) -> str:
        print("checking if found",raw_command)
        if raw_command.strip().startswith("edit"):
            print("edit command",raw_command)
            return raw_command.strip()[5:].strip()
        return ""

    def find_original_update_blocks(self, content):
        HEAD = "<<<<<<< SEARCH"
        DIVIDER = "======="
        UPDATED = ">>>>>>> REPLACE"
        separators = "|".join([HEAD, DIVIDER, UPDATED])
        split_re = re.compile(r"^((?:" + separators + r")[ ]*\n)", re.MULTILINE | re.DOTALL)

        pieces = re.split(split_re, content)
        pieces.reverse()
        processed = []
        current_filename = None

        try:
            while pieces:
                print(pieces)
                cur = pieces.pop()
                if cur.strip() != HEAD:
                    processed.append(cur)
                    continue

                processed.append(cur)  # original_marker
                filename = self.find_filename(processed[-2].splitlines())
                if not filename:
                    if current_filename:
                        filename = current_filename
                    else:
                        raise ValueError("Missing filename")

                current_filename = filename
                original_text = pieces.pop()
                processed.append(original_text)
                divider_marker = pieces.pop()
                processed.append(divider_marker)
                if divider_marker.strip() != DIVIDER:
                    raise ValueError(f"Expected `{DIVIDER}` not {divider_marker.strip()}")

                updated_text = pieces.pop()
                processed.append(updated_text)
                updated_marker = pieces.pop()
                processed.append(updated_marker)
                if updated_marker.strip() != UPDATED:
                    raise ValueError(f"Expected `{UPDATED}` not `{updated_marker.strip()}")

                yield filename, original_text, updated_text
        except Exception as e:
            processed = "".join(processed)
            raise ValueError(f"{processed}\n^^^ Error parsing SEARCH/REPLACE block: {str(e)}")

    def find_filename(self, lines):
        lines.reverse()
        lines = lines[:3]
        for line in lines:
            filename = line.strip().rstrip(':')
            if filename and not filename.startswith('```'):
                return filename

    def apply_edits(self, context: ToolContext, edits):
        results = []
        for filename, original, updated in edits:
            # file_path = Path(context["environment"].get_cwd()) / filename
            # print("file_path",file_path.as_posix())
            # if not file_path.exists():
            #     results.append({'status': 'error', 'message': f"File not found: {filename}"})
            #     continue

            file_path = make_abs_path(context, filename)

            file_exists = (
                context["environment"]
                .execute(f"test -e {file_path} && echo 'exists'")[0]
                .strip()
                == "exists"
            )
            content = read_file(context, file_path=file_path)
            new_content = self.replace_most_similar_chunk(content, original, updated)
            
            if new_content == content:
                results.append({'status': 'error', 'message': f"No changes made in {filename}"})
            else:
                write_file(context,file_path, new_content)
                results.append({'status': 'success', 'message': f"Successfully edited {filename}"})
                # context.state['edit_history'].append({
                #     'filename': filename,
                #     'old_content': content,
                #     'new_content': new_content
                # })

        return results

    def replace_most_similar_chunk(self, whole, part, replace):
        whole_lines = whole.splitlines()
        part_lines = part.splitlines()
        replace_lines = replace.splitlines()

        res = self.perfect_or_whitespace(whole_lines, part_lines, replace_lines)
        if res:
            return "\n".join(res)

        if len(part_lines) > 2 and not part_lines[0].strip():
            res = self.perfect_or_whitespace(whole_lines, part_lines[1:], replace_lines)
            if res:
                return "\n".join(res)

        return self.replace_closest_edit_distance(whole_lines, part, part_lines, replace_lines)

    def perfect_or_whitespace(self, whole_lines, part_lines, replace_lines):
        res = self.perfect_replace(whole_lines, part_lines, replace_lines)
        if res:
            return res

        return self.replace_part_with_missing_leading_whitespace(whole_lines, part_lines, replace_lines)

    def perfect_replace(self, whole_lines, part_lines, replace_lines):
        part_tup = tuple(part_lines)
        part_len = len(part_lines)

        for i in range(len(whole_lines) - part_len + 1):
            whole_tup = tuple(whole_lines[i : i + part_len])
            if part_tup == whole_tup:
                return whole_lines[:i] + replace_lines + whole_lines[i + part_len :]

    def replace_part_with_missing_leading_whitespace(self, whole_lines, part_lines, replace_lines):
        leading = [len(p) - len(p.lstrip()) for p in part_lines if p.strip()] + [
            len(p) - len(p.lstrip()) for p in replace_lines if p.strip()
        ]

        if leading and min(leading):
            num_leading = min(leading)
            part_lines = [p[num_leading:] if p.strip() else p for p in part_lines]
            replace_lines = [p[num_leading:] if p.strip() else p for p in replace_lines]

        num_part_lines = len(part_lines)

        for i in range(len(whole_lines) - num_part_lines + 1):
            add_leading = self.match_but_for_leading_whitespace(
                whole_lines[i : i + num_part_lines], part_lines
            )

            if add_leading is not None:
                replace_lines = [add_leading + rline if rline.strip() else rline for rline in replace_lines]
                return whole_lines[:i] + replace_lines + whole_lines[i + num_part_lines :]

        return None

    def match_but_for_leading_whitespace(self, whole_lines, part_lines):
        num = len(whole_lines)

        if not all(whole_lines[i].lstrip() == part_lines[i].lstrip() for i in range(num)):
            return

        add = set(
            whole_lines[i][: len(whole_lines[i]) - len(part_lines[i])]
            for i in range(num)
            if whole_lines[i].strip()
        )

        return add.pop() if len(add) == 1 else None

    def replace_closest_edit_distance(self, whole_lines, part, part_lines, replace_lines):
        similarity_thresh = 0.8
        max_similarity = 0
        most_similar_chunk_start = -1
        most_similar_chunk_end = -1

        scale = 0.1
        min_len = max(3, int(len(part_lines) * (1 - scale)))
        max_len = min(len(whole_lines), int(len(part_lines) * (1 + scale)))

        for length in range(min_len, max_len + 1):
            for i in range(len(whole_lines) - length + 1):
                chunk = "\n".join(whole_lines[i : i + length])
                similarity = SequenceMatcher(None, chunk, part).ratio()

                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_chunk_start = i
                    most_similar_chunk_end = i + length

        if max_similarity < similarity_thresh:
            return "\n".join(whole_lines)

        return "\n".join(
            whole_lines[:most_similar_chunk_start]
            + replace_lines
            + whole_lines[most_similar_chunk_end:]
        )

    def _format_results(self, results):
        output = []
        for result in results:
            if result['status'] == 'success':
                output.append(f"✅ {result['message']}")
            else:
                output.append(f"❌ {result['message']}")
        return "\n".join(output)

# Example usage:
# edit_tool = EditFileTool()
# edit_tool.register_pre_hook(lambda ctx: print("Starting edit..."))
# edit_tool.register_post_hook(lambda ctx, res: print(f"Edit completed: {res}"))