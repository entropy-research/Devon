import os
import gymnasium as gym

class Environment(gym.Env):


    def __init__(self, path) -> None:

        self.working_dir = os.path.abspath(path)
        
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)

        os.chdir(self.working_dir)
    

    def get_available_actions(self):

        return ["search","exit"]


    def step(self,action):

        if action == "exit":
            return {"result": "Done"}, 0, True, {} 
        else:
            return {"result": "Not Done"}, 0, False, {} 


    def reset():
        pass


    def close(self):
        return super().close()