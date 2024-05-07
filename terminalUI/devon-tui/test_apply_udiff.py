import os
import pytest
from apply_udiff import apply_udiff

@pytest.fixture
def setup_files(tmp_path):
    # Create sample udiff file
    udiff_content = """
--- a/sample.txt
+++ b/sample.txt
@@ -1,3 +1,3 @@
 line1
-line2
+updated line2
 line3
"""
    udiff_file = tmp_path / "sample.udiff"
    udiff_file.write_text(udiff_content)

    # Create sample target file
    target_file = tmp_path / "sample.txt"
    target_file.write_text("line1\nline2\nline3")

    return str(udiff_file), str(target_file)

def test_apply_udiff_success(setup_files):
    udiff_path, target_path = setup_files

    apply_udiff(udiff_path)

    with open(target_path, "r") as f:
        patched_content = f.read()

    assert patched_content == "line1\nupdated line2\nline3"

def test_apply_udiff_invalid_path():
    # Test applying udiff with an invalid file path
    invalid_path = "nonexistent.udiff"
    
    with pytest.raises(FileNotFoundError):
        apply_udiff(invalid_path)
