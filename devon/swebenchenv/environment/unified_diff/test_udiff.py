from devon.swebenchenv.environment.unified_diff.udiff import match_stripped_lines_context


def test_match_lines2_empty_file():
    file_lines = []
    old_lines = ["line 1", "line 2", "line 3"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start is None and end is None

def test_match_lines2_one_old_line():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3")]
    old_lines = ["line 2"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    # print(start, end)
    assert start == 1 and end == 1

def test_match_lines2_two_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4")]
    old_lines = ["line 2", "line 3"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start == 1 and end == 2

def test_match_lines2_three_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4"), (4, "line 5")]
    old_lines = ["line 2", "line 3", "line 4"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start == 1 and end == 3

def test_match_lines2_four_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4"), (4, "line 5"), (5, "line 6")]
    old_lines = ["line 2", "line 3", "line 4", "line 5"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start == 1 and end == 4

def test_match_lines2_five_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4"), (4, "line 5"), (5, "line 6"), (6, "line 7")]
    old_lines = ["line 2", "line 3", "line 4", "line 5", "line 6"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start == 1 and end == 5

def test_match_lines2_empty_lines_in_file():
    file_lines = [(0, "line 1"), (1, ""), (2, "line 2"), (3, ""), (4, "line 3"), (5, "line 4")]
    old_lines = ["line 2", "line 3"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start == 2 and end == 4

def test_match_lines2_empty_lines_in_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3"), (3, "line 4")]
    old_lines = ["", "line 2", "", "line 3", ""]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start == 1 and end == 2

def test_match_lines2_empty_lines_in_both():
    file_lines = [(0, ""), (1, "line 1"), (2, ""), (3, "line 2"), (4, ""), (5, "line 3"), (6, "")]
    old_lines = ["", "line 2", "", "line 3", ""]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start == 3 and end == 5

def test_match_lines2_all_empty_lines_in_file():
    file_lines = [(0, ""), (1, ""), (2, ""), (3, "")]
    old_lines = ["line 1", "line 2"]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start is None and end is None

def test_match_lines2_all_empty_lines_in_old_lines():
    file_lines = [(0, "line 1"), (1, "line 2"), (2, "line 3")]
    old_lines = ["", "", ""]
    start, end = match_stripped_lines_context(file_lines, old_lines)
    assert start is None and end is None