import logging
from pathlib import Path

from devon_agent.environment import LocalEnvironment
from devon_agent.session import Session, SessionArguments
# from devon_agent.tools import create_file
from devon_agent.tools.edittools import EditFileTool
from devon_agent.tools.utils import normalize_path
from devon_agent.utils import DotDict


# def test_create_file():
#     # make temp dir
#     import tempfile

#     temp_dir = tempfile.mkdtemp()

#     paths = ["hello", "test/hello", temp_dir + "/repo.py"]

#     ctx = DotDict({})
#     ctx.environment = LocalEnvironment(temp_dir)
#     ctx.base_path = temp_dir
#     ctx.state = DotDict({})
#     ctx.state.editor = {}
#     ctx.logger = logging.getLogger("mock")
#     handler = logging.StreamHandler()
#     ctx.logger.addHandler(handler)

#     for path in paths:
#         create_file(ctx, path, "world")
#         new_path = (Path(temp_dir) / Path(path)).as_posix()

#         with open(new_path, "r") as f:
#             assert f.read() == "world\n"


def test_edit_file():
    import tempfile

    temp_dir = tempfile.mkdtemp()

    snake_game_path = Path(temp_dir) / Path("snake_game.py")
    command = f"""
edit_file <<<                                                                    
--- {snake_game_path}                       
+++ {snake_game_path}                          
@@ -0,0 +1,50 @@                                                                 
import pygame                                                                    
import time                                                                      
import random                                                                    
                                                                                
pygame.init()
>>>  """
    content = """
import pygame                                                                    
import time                                                                      
import random                                                                    
                                                                                
pygame.init()"""


    session = Session(
        args=SessionArguments(
            path=temp_dir,
            user_input="",
            name="test"

        ),
        agent=None
    )
    et = EditFileTool()
    le = LocalEnvironment(temp_dir)
    le.setup(session)
    le.register_tools({
        "edit_file": et
    })

    with open(snake_game_path, "w") as f:
        f.write("")

    et({
        "session": session,
        "raw_command": command,
        "environment": le,
    })

    # create file with the content

    # check if the file was edited
    with open(Path(temp_dir) / Path("snake_game.py"), "r") as f:
        assert f.read() == content

