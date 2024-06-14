import json
import logging
import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from swebench import KEY_INSTANCE_ID, KEY_MODEL, KEY_PREDICTION

from devon_agent.agents.default.agent import TaskAgent
from devon_agent.environments.swebenchenv import SWEEnvEnvironment
from devon_agent.sweenvsession import (SWEEnvSession, SWEEnvSessionArguments,
                                       get_instances)
from devon_agent.utils import Event


@dataclass
class Args:
    image_name: str
    container_name: Optional[str] = None
    timeout: Optional[int] = None
    no_mirror: Optional[bool] = False
    model: str = "claude-opus"
    temperature: float = 0.0
    data_path: str = "princeton-nlp/SWE-bench_Lite"
    exp_name: str = "default"
    split: str = "test"
    specific_issues: Optional[List[str]] = None
    skip_existing: bool = False


logger = logging.getLogger(__name__)


def process_batch(args):
    print(args)
    # args.environment.specific_issues = batch

    gh_token = os.environ.get("GITHUB_TOKEN", None)
    data_path = args.data_path
    specific_issues = args.specific_issues
    data = get_instances(
        data_path,
        None,
        args.split,
        token=gh_token,
        specific_issues=specific_issues,
    )  # Load data from path
    env = SWEEnvEnvironment(
        logger,
        container_name=args.container_name,
        image_name=args.image_name,
        persistent=args.container_name if args.container_name else False,
        timeout=args.timeout,
        no_mirror=args.no_mirror,
        token=gh_token,
    )
    # env.setup()

    # env = SWEEnv(args.environment,batch)
    agent = TaskAgent(name="devon", model=args.model, temperature=args.temperature)

    """
    input: data, agent, traj dir, env
    
    try:
        #in session
        for index in data:
            try:
                1. reset environment with instance (should skip/not)
                2. setup dirs
                3. run loop over submit loop
            except keyboard exception as e:
                raise e
            except exception:
                handle normally + continue

    except:
        env.close


    """

    # print("EXPERIMENT_NAME: ", args.exp_name)
    traj_dir = (
        Path("trajectories")
        / Path(args.exp_name)
        / Path("_".join([args.model, str(args.temperature)]))
    )
    try:
        session = SWEEnvSession(
            SWEEnvSessionArguments(
                # image_name=args.image_name,
                # container_name=args.container_name,
                # timeout=args.timeout,
                # no_mirror=args.no_mirror,
                sweenv=env,
                skip_existing=True,
            ),
            agent=agent,
            data=data,
            traj_dir=traj_dir,
        )
        session.enter()
        session.run_event_loop()
        session.exit()
    except KeyboardInterrupt:
        logger.info("Exiting InterCode environment...")
        env.teardown()


if __name__ == "__main__":
    args = Args(
        image_name="swe-agent", timeout=300, container_name="swe-agent", model="gpt4-o"
    )
    process_batch(args)
