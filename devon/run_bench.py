

import asyncio
import json
import logging
import os
import re
import traceback
import yaml

import concurrent.futures

from dataclasses import dataclass
from getpass import getuser
from pathlib import Path
from rich.logging import RichHandler
from simple_parsing import parse
from simple_parsing.helpers import FrozenSerializable, FlattenedAccess

from devon.agent.model import ModelArguments
from devon.agent.thread import Agent
from devon.swebenchenv.environment.swe_env import EnvironmentArguments, SWEEnv
from devon.swebenchenv.environment.utils import get_data_path_name
from swebench import KEY_INSTANCE_ID, KEY_MODEL, KEY_PREDICTION
from unidiff import PatchSet

handler = RichHandler(show_time=False, show_path=False)
handler.setLevel(logging.DEBUG)
logger = logging.getLogger("run_dev")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.propagate = False
logging.getLogger("simple_parsing").setLevel(logging.WARNING)


@dataclass(frozen=True)
class ScriptArguments(FlattenedAccess, FrozenSerializable):
    exp_name: str
    environment: EnvironmentArguments
    instance_filter: str = ".*"  # Only run instances that completely match this regex
    skip_existing: bool = True  # Skip instances with existing trajectories
    suffix: str = ""
    tasklist_path: str = "tasklist"
    model: str = "claude-opus"
    temperature: float = 0
    batch_size: int = 3

    @property
    def run_name(self):
        """Generate a unique name for this run based on the arguments."""
        model_name = self.agent.model.model_name.replace(":", "-")
        data_stem = get_data_path_name(self.environment.data_path)
        config_stem = Path(self.agent.config_file).stem

        temp = self.agent.model.temperature
        top_p = self.agent.model.top_p

        per_instance_cost_limit = self.agent.model.per_instance_cost_limit
        install_env = self.environment.install_environment

        return (
            f"{model_name}__{data_stem}__{config_stem}__t-{temp:.2f}__p-{top_p:.2f}"
            + f"__c-{per_instance_cost_limit:.2f}__install-{int(install_env)}"
            + (f"__{self.suffix}" if self.suffix else "")
        )
    
def process_batch(batch,args):
    print(batch)
    # args.environment.specific_issues = batch

    env = SWEEnv(args.environment,batch)
    print("gadsvevfa")
    agent = Agent("primary",args.model, args.temperature)
    print("EXPERIMENT_NAME: ", args.exp_name)
    traj_dir = Path("trajectories") / Path(args.exp_name) / Path("_".join([agent.default_model.args.model_name, str(agent.default_model.args.temperature)]))


    for index in range(len(env.data)):
        try:
            # Reset environment
            instance_id = env.data[index]["instance_id"]
            if should_skip(args, traj_dir, instance_id):
                continue
            logger.info("▶️  Beginning task " + str(index))
            try:
                observation, info = env.reset(index)
            except Exception as e:
                logger.error(f"Error resetting environment: {e}")
                env.reset_container()
                continue
            if info is None:
                continue

            agent = Agent("primary", args.model, args.temperature)

            # Get info, patch information
            issue = getattr(env, "query", None)
            files = []
            if "patch" in env.record:
                files = "\n".join(
                    [f"- {x.path}" for x in PatchSet(env.record["patch"]).modified_files]
                )
            # Get test files, F2P tests information
            test_files = []
            if "test_patch" in env.record:
                test_patch_obj = PatchSet(env.record["test_patch"])
                test_files = "\n".join(
                    [f"- {x.path}" for x in test_patch_obj.modified_files + test_patch_obj.added_files]
                )
            tests = ""
            if "FAIL_TO_PASS" in env.record:
                tests = "\n".join([f"- {x}" for x in env.record["FAIL_TO_PASS"]])

            setup_args = {
                "issue": issue,
                "files": files,
                "test_files": test_files,
                "tests": tests
            }
            print(agent.default_model.args.model_name)


            os.makedirs(traj_dir, exist_ok=True)
            save_arguments(traj_dir, args)

            try:
                
                info = agent.run(
                    setup_args=setup_args,
                    env=env,
                    observation=observation,
                    traj_dir=traj_dir,
                    return_type="info",
                )
            except Exception as e:
                logger.error(f"Error running agent: {e}")
                traceback.print_exc()
                continue
            save_predictions(traj_dir, instance_id, info)

        except KeyboardInterrupt:
            logger.info("Exiting InterCode environment...")
            env.close()
            break
        except Exception as e:
            traceback.print_exc()
            logger.warning(f"❌ Failed on {env.record['instance_id']}: {e}")
            env.reset_container()
            continue


def main(args: ScriptArguments):
    logger.info(f"📙 Arguments: {args.dumps_yaml()}")

    print(args.__dict__)

    if args.tasklist_path:
        with open(args.tasklist_path, "r") as f:
            tasks = f.readlines()
        tasks = [x.strip() for x in tasks]

    batch_size = args.batch_size
    # divide tasks into batches of size batch_size
    batches = [tasks[i:i+batch_size] for i in range(0, len(tasks), batch_size)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for batch in batches:
            print(batch)
            future = executor.submit(process_batch, list(batch), args)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                # Process the result if needed
            except Exception as e:
                # Handle the exception
                print(f"An exception occurred: {e}")

        
    


def save_arguments(traj_dir, args):
    """Save the arguments to a yaml file to the run's trajectory directory."""
    log_path = traj_dir / "args.yaml"

    if log_path.exists():
        try:
            other_args = args.load_yaml(log_path)
            if (args.dumps_yaml() != other_args.dumps_yaml()):  # check yaml equality instead of object equality
                logger.warning("**************************************************")
                logger.warning("Found existing args.yaml with different arguments!")
                logger.warning("**************************************************")
        except Exception as e:
            logger.warning(f"Failed to load existing args.yaml: {e}")

    with log_path.open("w") as f:
        args.dump_yaml(f)


def should_skip(args, traj_dir, instance_id):
    """Check if we should skip this instance based on the instance filter and skip_existing flag."""
    # Skip instances that don't match the instance filter
    # if re.match(args.instance_filter, instance_id) is None:
    #     logger.info(f"Instance filter not matched. Skipping instance {instance_id}")
    #     return True

    # If flag is set to False, don't skip
    if not args.skip_existing:
        return False

    # Check if there's an existing trajectory for this instance
    log_path = traj_dir / f"{instance_id}.traj"

    if log_path.exists():
        with log_path.open("r") as f:
            data = json.load(f)
        # If the trajectory has no exit status, it's incomplete and we will redo it
        exit_status = data["info"].get("exit_status", None)
        if exit_status == "early_exit" or exit_status is None:
            logger.info(f"Found existing trajectory with no exit status: {log_path}")
            logger.info("Removing incomplete trajectory...")
            os.remove(log_path)
        else:
            logger.info(f"⏭️ Skipping existing trajectory: {log_path}")
            return True
        return False

def save_predictions(traj_dir, instance_id, info):
    output_file = Path(traj_dir) / "all_preds.jsonl"
    model_patch = info["submission"] if "submission" in info else None
    datum = {
        KEY_MODEL: Path(traj_dir).name,
        KEY_INSTANCE_ID: instance_id,
        KEY_PREDICTION: model_patch,
    }
    with open(output_file, "a+") as fp:
        print(json.dumps(datum), file=fp, flush=True)
    logger.info(f"Saved predictions to {output_file}")


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Run benchmark with specified parameters.")
    parser.add_argument("--exp_name", type=str, required=True, help="Experiment name.")
    parser.add_argument("--task_list_path", type=str, default="tasklist", help="Path to the task list file.")
    parser.add_argument("--model", type=str, default="opus", help="Model to use for the experiment.")
    parser.add_argument("--temperature", type=float, default=0, help="Temperature setting for the model.")

    args = parser.parse_args()

    exp_name = args.exp_name
    task_list_path = args.task_list_path
    model = args.model
    temperature = args.temperature

#     with open ("tasklist", "r") as f:
#         tasks = f.readlines()
#     tasks = [x.strip() for x in tasks]

#     issues = [
#         "astropy__astropy-14995",
#         "django__django-10914",
#         "django__django-11039",
#         "django__django-11049",
#         "django__django-11099",
#         "django__django-11133",
#         "django__django-11815",
#         "django__django-12286",
#         "django__django-12453",
#         "django__django-12700",
#         "django__django-12983",
#         "django__django-13028",
#         "django__django-13315",
#         "django__django-13590",
#         "django__django-13658",
#         "django__django-13660",
#         "django__django-13710",
#         "django__django-13925",
#         "django__django-13964",
#         "django__django-14382",
#         "django__django-14608",
#         "django__django-14672",
#         "django__django-14752",
#         "django__django-14855",
#         "django__django-14915",
#         "django__django-15498",
#         "django__django-15789",
#         "django__django-15814",
#         "django__django-15851",
#         "django__django-16041",
#         "django__django-16046",
#         "django__django-16139",
#         "django__django-16255",
#         "django__django-16379",
#         "django__django-16527",
#         "django__django-16595",
#         "django__django-16873",
#         "matplotlib__matplotlib-26020",
#         "psf__requests-3362",
#         "psf__requests-863",
#         "pydata__xarray-5131",
#         "pytest-dev__pytest-11143",
#         "pytest-dev__pytest-5227",
#         "pytest-dev__pytest-5692",
#         "pytest-dev__pytest-7373",
#         "scikit-learn__scikit-learn-13496",
#         "scikit-learn__scikit-learn-13497",
#         "scikit-learn__scikit-learn-13584",
#         "scikit-learn__scikit-learn-14894",
#         "sympy__sympy-13480",
#         "sympy__sympy-13647",
#         "sympy__sympy-13971",
#         "sympy__sympy-14774",
#         "sympy__sympy-16988",
#         "sympy__sympy-18532",
#         "sympy__sympy-20212",
#         "sympy__sympy-21847",
#         "sympy__sympy-22005",
#         "sympy__sympy-23117",
#         "sympy__sympy-24152",
#         "sympy__sympy-24213"
#     "astropy__astropy-14995",
#     "pytest-dev__pytest-5692",
#     "psf__requests-2317",
#     "django__django-13230",
#     "pytest-dev__pytest-5227",
#     "django__django-12286",
#     "django__django-16873",
#     "scikit-learn__scikit-learn-14894",
#     "scikit-learn__scikit-learn-10297",
#     "pylint-dev__pylint-5859",
#     "django__django-14382",
#     "django__django-16255",
#     "sphinx-doc__sphinx-8713",
#     "django__django-16595",
#     "sympy__sympy-24152",
#     "sympy__sympy-23262",
#     "sympy__sympy-13971",
#     "django__django-11583",
#     "scikit-learn__scikit-learn-15535",
#     "sympy__sympy-13647",
#     "django__django-13658",
#     "django__django-10914",
#     "django__django-15814",
#     "django__django-12983",
#     "django__django-14915",
#     "sympy__sympy-13480",
#     "sympy__sympy-24213",
#     "django__django-11133",
#     "matplotlib__matplotlib-23964",
#     "matplotlib__matplotlib-26020",
#     "django__django-13401",
#     "django__django-11099",
#     "django__django-16046",
#     "django__django-16527",
#     "pytest-dev__pytest-11143",
#     "django__django-15347",
#     "django__django-12453",
#     "django__django-14787",
#     "django__django-16379",
#     "django__django-13447",
#     "sympy__sympy-14774",
#     "psf__requests-2674",
#     "scikit-learn__scikit-learn-13584",
#     "matplotlib__matplotlib-26011",
#     "django__django-14999",
#     "django__django-15213",
#     "django__django-14752",
#     "django__django-16139",
#     "django__django-14672",
#     "sympy__sympy-16988",
#     "mwaskom__seaborn-3010",
#     "django__django-11039",
#     "django__django-14855",
#     "django__django-14238"
#     "sympy__sympy-16988",
# #    "astropy__astropy-12907",
#     "django__django-13230",
#     "django__django-17051",
#     "django__django-11049",
#     "pytest__pytest-7373",
#     "pytest__pytest-5221",
#     "django__django-12700",
#     "sympy__sympy-12481",
# #    "matplotlib__matplotlib-25079",
#     "django__django-12856",
#     "django__django-16229",
#     "django__django-11283",
#     "sympy__sympy-14817",
#     "sympy__sympy-16106",
#     "scikit-learn__scikit-learn-14817",
# #    "matplotlib__matplotlib-24334",
#     "pytest__pytest-7432",
# #    "astropy__astropy-12907",
#     "psf__requests-2674",
# ]

    defaults = ScriptArguments(
        suffix="",
        environment=EnvironmentArguments(
            image_name="swe-agent",
            data_path="princeton-nlp/SWE-bench_Lite",
            split="test",
            verbose=True,
            # container_name="swe-agent4",
            install_environment=True,
            # django-14787
            # django-16046
            # django-13447
            # django-11583
            # "pytest__pytest-7373"
            # specific_issues=["django__django-14915"]
        ),
        skip_existing=True,
        model=model,
        temperature=temperature,
        exp_name=exp_name
    )

    main(defaults)
