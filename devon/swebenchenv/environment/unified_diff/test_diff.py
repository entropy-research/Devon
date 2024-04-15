

import os
from anthropic import Anthropic
from devon.swebenchenv.environment.unified_diff.create_diff import construct_versions_from_diff_hunk, extract_diffs, parse_multi_file_diff2
from devon.swebenchenv.environment.unified_diff.diff_types import MultiFileDiff2
from devon.swebenchenv.environment.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts
from devon.swebenchenv.environment.unified_diff.utils import create_code_fence, match_stripped_lines2
from devon_agent.agent.clients.client import ClaudeSonnet, Message

goal = """my goal is to improve the error handling in the URLValidator class.

The current implementation catches a ValueError raised by urlsplit() when it encounters an invalid URL, like one with an invalid IPv6 address. But instead of showing the actual error message from urlsplit(), it just raises a generic ValidationError with a predetermined message."""

diff_code = """
Okay, I understand the issue and the required changes. Here are the diffs to fix it:

<DIFF>
--- django__django/django/core/validators.py
+++ django__django/django/core/validators.py
@@ -142,10 +142,12 @@ class URLValidator(RegexValidator):
             scheme, netloc, path, query, fragment = urlsplit(value)
         except ValueError as e:
             # urlsplit() raised a ValueError, e.g. for an invalid IPv6 URL.
-            raise ValidationError(self.message, code=self.code, params={'value': value})
+            raise ValidationError(
+                str(e),
+                code=self.code,
+                params={'value': value},
+            )
         try:
             netloc = punycode(netloc)  # IDN -> ACE
         except UnicodeError:  # invalid domain part
             raise e
</DIFF>

The key changes are:

1. Catch the `ValueError` raised by `urlsplit()` and store it in the `e` variable.
2. Instead of raising a generic `ValidationError`, raise it with the string representation of the caught `ValueError` as the error message.
3. Pass the `code` and `params` to the `ValidationError` as before.
4. If there is a `UnicodeError` raised when trying to convert the netloc to punycode, re-raise the original `ValueError` caught earlier.

This way, instead of a generic error message, the actual `ValueError` message from `urlsplit()` will be shown when it fails to parse the URL, giving a more informative error."""

class Hallucination(Exception):
    pass

def create_recover_prompt(original, diff):

    return f"""
The original code looks like this: {original}
    
You generated a diff that looked like this: {diff}

Applying this diff failed! The context lines and the src lines from the diff did not match the real code in the file!

Please explain how to fix this, and then generate a new diff that will match.
"""

def match_with_recover(content, diff):
    diffs = extract_diffs(diff)

    all_diffs = []
    for diff in diffs:
        file_diffs = parse_multi_file_diff2(diff)
        # print(file_diffs)
        all_diffs.extend(file_diffs)

    print(all_diffs)

    diff_m = MultiFileDiff2(files=all_diffs)

    src_lines = [(i, line) for i, line in enumerate(testcode_content.splitlines())]

    for file_diff in diff_m.files:
        for hunk in file_diff.hunks:
            old, new = construct_versions_from_diff_hunk(hunk)

            print("\n".join(old))
            print("\n".join(new))

            begin, end = match_stripped_lines2(src_lines, old)

            if not ( begin and end ):
                raise Hallucination()
        
            return True

if __name__ == "__main__":
    with open("./testcode.py", "r") as file:
        testcode_content = file.read()

    api_key=os.environ.get("ANTHROPIC_API_KEY")
    anthrpoic_client = Anthropic(api_key=api_key)
    diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system, max_tokens=4096)

    fixed = False
    error_context = []
    while not fixed:
        print(diff_code)
        input()
        try:
            fixed = match_with_recover(testcode_content, diff_code)
        except Hallucination as e:
            #Get model to explain itself and why the error happened

            diff_code = diff_model.chat([
                Message(
                    role="user",
                    content=create_recover_prompt(testcode_content, diff_code)
                )
            ])

    print(fixed)
