import logging
from pathlib import Path

from devon.environment.environment import LocalEnvironment
from devon.environment.tools import create_file
from devon.environment.utils import DotDict


def test_create_file():
    # make temp dir
    import tempfile

    temp_dir = tempfile.mkdtemp()

    paths = ["hello", "test/hello", temp_dir + "/repo.py"]

    ctx = DotDict({})
    ctx.environment = LocalEnvironment(temp_dir)
    ctx.base_path = temp_dir
    ctx.state = DotDict({})
    ctx.state.editor = {}
    ctx.logger = logging.getLogger("mock")
    handler = logging.StreamHandler()
    ctx.logger.addHandler(handler)

    for path in paths:
        create_file(ctx, path, "world")
        new_path = (Path(temp_dir) / Path(path)).as_posix()

        with open(new_path, "r") as f:
            assert f.read() == "world\n"
