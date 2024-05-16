from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import traceback
from typing import List, Optional

from devon_agent.agent import TaskAgent

from devon_agent.environments.swebenchenv import SWEEnvEnvironment
from devon_agent.sweenvsession import (
    SWEEnvSession,
    SWEEnvSessionArguments,
    get_instances,
)
from swebench import KEY_INSTANCE_ID, KEY_MODEL, KEY_PREDICTION

from devon_agent.utils import Event

@dataclass
class Args:
    image_name : str
    container_name : Optional[str] = None
    timeout : Optional[int] = None
    no_mirror : Optional[bool] = False
    model : str = "claude-opus"
    temperature : float = 0.0
    data_path : str = "princeton-nlp/SWE-bench_Lite"
    exp_name : str = "default"
    split : str = "test"
    specific_issues : Optional[List[str]] = None
    skip_existing : bool = False

def save_predictions(traj_dir, instance_id, submission):
    output_file = Path(traj_dir) / "all_preds.jsonl"
    model_patch = submission
    datum = {
        KEY_MODEL: Path(traj_dir).name,
        KEY_INSTANCE_ID: instance_id,
        KEY_PREDICTION: model_patch,
    }
    with open(output_file, "a+") as fp:
        print(json.dumps(datum), file=fp, flush=True)
    logger.info(f"Saved predictions to {output_file}")


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
    env.setup()

    # env = SWEEnv(args.environment,batch)
    agent = TaskAgent(name="devon", model=args.model, temperature=args.temperature)
    # print("EXPERIMENT_NAME: ", args.exp_name)
    traj_dir = (
        Path("trajectories")
        / Path(args.exp_name)
        / Path("_".join([args.model, str(args.temperature)]))
    )

    for index in range(len(data)):
        try:
            # Reset environment
            record = data[index]
            instance_id = record["instance_id"]
            if should_skip(args, traj_dir, instance_id):
                continue
            logger.info("▶️  Beginning task " + str(index))
            try:
                env.reset(record)
            except Exception as e:
                logger.error(f"Error resetting environment: {e}")
                env.teardown()
                env.setup()
                continue
            # if info is None:
            #     continue

            agent = TaskAgent(
                name="devon", model=args.model, temperature=args.temperature
            )

            # # Get info, patch information
            # issue = getattr(env, "query", None)
            # files = []
            # if "patch" in env.record:
            #     files = "\n".join(
            #         [f"- {x.path}" for x in PatchSet(env.record["patch"]).modified_files]
            #     )
            # # Get test files, F2P tests information
            # test_files = []
            # if "test_patch" in env.record:
            #     test_patch_obj = PatchSet(env.record["test_patch"])
            #     test_files = "\n".join(
            #         [f"- {x.path}" for x in test_patch_obj.modified_files + test_patch_obj.added_files]
            #     )
            # tests = ""
            # if "FAIL_TO_PASS" in env.record:
            #     tests = "\n".join([f"- {x}" for x in env.record["FAIL_TO_PASS"]])

            # setup_args = {
            #     "issue": issue,
            #     "files": files,
            #     "test_files": test_files,
            #     "tests": tests
            # }
            # print(agent.default_model.args.model_name)

            os.makedirs(traj_dir, exist_ok=True)

            try:

                session = SWEEnvSession(
                    SWEEnvSessionArguments(
                        # image_name=args.image_name,
                        # container_name=args.container_name,
                        # timeout=args.timeout,
                        # no_mirror=args.no_mirror,
                        sweenv=env,
                        record=record,
                    ),
                    agent=agent,
                )
                session.enter()
                session.event_log.append(Event(
                    type="ModelRequest",
                    content="",
                    producer="system",
                    consumer="devon"

                ))
                submission = session.run_event_loop()
            except Exception as e:
                logger.error(f"Error running agent: {e}")
                traceback.print_exc()
                continue
            save_predictions(traj_dir, instance_id, submission)

        except KeyboardInterrupt:
            logger.info("Exiting InterCode environment...")
            env.close()
            break
        except Exception as e:
            traceback.print_exc()
            logger.warning(f"❌ Failed on {record['instance_id']}: {e}")
            env.teardown()
            env.setup()
            continue




if __name__ == "__main__":
    

    args = Args(
        image_name="swe-agent",
        timeout=300,
        container_name="swe-agent",
    )
    process_batch(args)

