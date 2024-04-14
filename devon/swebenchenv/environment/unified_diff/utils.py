import difflib
from devon_agent.agent.tools.unified_diff.create_diff import FileDiff, MultiFileDiff, construct_versions_from_diff_hunk, extract_diffs, parse_multi_file_diff2
import os

from devon_agent.agent.tools.unified_diff.diff_types import MultiFileDiff2

import docker
import os

class DockerOSEmulator:
    def __init__(self, container_id):
        self.client = docker.from_env()
        self.container = self.client.containers.get(container_id)

    def path_exists(self, path):
        """
        Check if a file or directory exists in the container.
        """
        try:
            self.container.exec_run(f"test -e {path}")
            return True
        except docker.errors.ContainerError:
            return False

    def makedirs(self, path):
        """
        Create directories recursively in the container.
        """
        self.container.exec_run(f"mkdir -p {path}")

    def remove(self, path):
        """
        Remove a file from the container.
        """
        self.container.exec_run(f"rm {path}")

    def is_abs(self, path):
        """
        Check if a path is absolute in the container.
        """
        return os.path.isabs(path)

    def dirname(self, path):
        """
        Get the directory name of a path in the container.
        """
        return os.path.dirname(path)

    def open(self, path, mode="r"):
        """
        Open a file in the container.
        """
        return DockerFile(self.container, path, mode)

class DockerFile:
    def __init__(self, container, path, mode):
        self.container = container
        self.path = path
        self.mode = mode

    def write(self, content):
        """
        Write content to the file in the container.
        """
        self.container.exec_run(f"echo '{content}' > {self.path}")

    def read(self):
        """
        Read the content of the file from the container.
        """
        result = self.container.exec_run(f"cat {self.path}")
        return result.output.decode("utf-8")

    def close(self):
        """
        Close the file (no-op).
        """
        pass

def first_and_last_content_lines(lines):
    start = 0
    for i, line in enumerate(lines):
        if line != '':
            start = i
            break

    end = 0
    for i, line in enumerate(reversed(lines)):
        if line != '':
            end = i + 1
            break

    return start, end


def match_stripped_lines(file_lines, old_lines):
    stripped_file_lines = [(i, line.strip()) for i, line in file_lines]
    old_lines = [line.strip() for line in old_lines]

    start, end  = first_and_last_content_lines(old_lines)

    i = 0
    while i < len(stripped_file_lines):
        if len(old_lines) > 0 and stripped_file_lines[i][1] == old_lines[start]:
            j = 1
            while i + j < len(stripped_file_lines) and stripped_file_lines[i + j][1] != old_lines[-end]:
                j += 1

            start_line = stripped_file_lines[i][0]  # Add 1 to convert from 0-based index to 1-based line number
            end_line = stripped_file_lines[i + j][0]

            return start_line, end_line
        else:
            i += 1

    return None, None


def find_nth_content_line(lines, n):
    start = 0
    for i, line in enumerate(lines):
        if line != '':
            start = i
            break
    
    count = 0
    end = start
    while end < len(lines) and count < n:

        if lines[end] != '':
            count += 1

        end += 1

    return lines[start:end] #maybe off by one? dont think so though, need to test

def create_code_fence(old_lines):
    if len(old_lines) < 4:
        start_fence = find_nth_content_line(old_lines, len(old_lines))
        end_fence = start_fence
    else:
        start_fence = find_nth_content_line(old_lines, 3)
        end_fence = list(reversed(find_nth_content_line(list(reversed(old_lines)), 3)))
    
    return start_fence, end_fence

def match_fence(lines, fence):
    subset_length = len(fence)
    
    if subset_length > 0:
        for i in range(len(lines) - subset_length + 1):
            match = [line[1] for line in lines[i:i+subset_length]]
            # if match[0] == fence[0]:
                # print(match, fence)
            if match == fence:
                return lines[i][0], lines[i+subset_length-1][0]

    return None, None

def match_stripped_lines2(file_lines, old_lines):

    stripped_file_lines = [(i, line.strip()) for i, line in file_lines]
    stripped_old_lines = [line.strip() for line in old_lines]

    stripped_file_lines = [t for t in stripped_file_lines if t[1] != ""]
    stripped_old_lines = [line for line in stripped_old_lines if line != ""]

    begin_fence, stop_fence = create_code_fence(old_lines=stripped_old_lines)

    begin_start, begin_end = match_fence(stripped_file_lines, begin_fence)
    stop_start, stop_end = match_fence(stripped_file_lines, stop_fence)

    start = begin_start
    end = stop_end

    return start, end


def test_match_lines2_empty_file():
    file_lines = []
    old_lines = ["line 1", "line 2", "line 3"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start is None and end is None

def test_match_lines2_one_old_line():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3")]
    old_lines = ["line 2"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    # print(start, end)
    assert start == 1 and end == 1

def test_match_lines2_two_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4")]
    old_lines = ["line 2", "line 3"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start == 1 and end == 2

def test_match_lines2_three_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4"), (4, "line 5")]
    old_lines = ["line 2", "line 3", "line 4"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start == 1 and end == 3

def test_match_lines2_four_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4"), (4, "line 5"), (5, "line 6")]
    old_lines = ["line 2", "line 3", "line 4", "line 5"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start == 1 and end == 4

def test_match_lines2_five_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4"), (4, "line 5"), (5, "line 6"), (6, "line 7")]
    old_lines = ["line 2", "line 3", "line 4", "line 5", "line 6"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start == 1 and end == 5

def test_match_lines2_empty_lines_in_file():
    file_lines = [(0, "line 1"), (1, ""), (2, "line 2"), (3, ""), (4, "line 3"), (5, "line 4")]
    old_lines = ["line 2", "line 3"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start == 2 and end == 4

def test_match_lines2_empty_lines_in_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4")]
    old_lines = ["", "line 2", "", "line 3", ""]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start == 1 and end == 2

def test_match_lines2_empty_lines_in_both():
    file_lines = [(0, ""), (1, "line 1"), (2, ""), (3, "line 2"), (4, ""), (5, "line 3"), (6, "")]
    old_lines = ["", "line 2", "", "line 3", ""]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start == 3 and end == 5

def test_match_lines2_all_empty_lines_in_file():
    file_lines = [(0, ""), (1, ""), (2, ""), (3, "")]
    old_lines = ["line 1", "line 2"]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start is None and end is None

def test_match_lines2_all_empty_lines_in_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3")]
    old_lines = ["", "", ""]
    start, end = match_stripped_lines2(file_lines, old_lines)
    assert start is None and end is None


if __name__ == "__main__":
    
    res = """Okay, here are the diffs to fix the issue with URLField.clean() raising ValueError instead of ValidationError:

<DIFF>
--- django/forms/fields.py
+++ django/forms/fields.py
@@ -1044,8 +1044,11 @@
             try:
                 return list(urlsplit(url))
             except ValueError:
-                # urlparse.urlsplit can raise a ValueError with some
-                # misformatted URLs.
-                raise ValidationError(self.error_messages['invalid'], code='invalid')
+                # urlparse.urlsplit can raise ValueError with some malformed URLs.
+                # Catch that and re-raise as a ValidationError.
+                raise ValidationError(
+                    self.error_messages['invalid'],
+                    code='invalid',
+                    params={'value': url},
+                )
</DIFF>

This change catches the ValueError raised by urlsplit() when it fails to parse a malformed URL, and re-raises it as a Django ValidationError with the 'invalid' code and the original URL value passed as the 'params' argument.

The key things:

1. Catch the ValueError exception 
2. Raise a ValidationError instead
3. Pass the 'invalid' error message code
4. Pass the original URL value in the 'params' dict for better error messaging

With this change, invalid URLs passed to URLField.clean() will now raise a proper ValidationError that can be handled by Django's form validation system, instead of the low-level ValueError."""

    diffs = extract_diffs(res)

    all_diffs = []
    for diff in diffs:
        file_diffs = parse_multi_file_diff2(diff)
        all_diffs.extend(file_diffs)

    changes = MultiFileDiff2(files=all_diffs)

    for file_diff in all_diffs:
        for hunk in file_diff.hunks:
            old, new = construct_versions_from_diff_hunk(hunk)

            # print("\n".join(old))
            # print("\n".join(new))

            old_fence = create_code_fence(old)
            print(old_fence)


