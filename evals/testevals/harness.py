import json
import os
import random
import shutil
import subprocess
from typing import List, Optional
import asyncio
from pydantic import BaseModel

from requirements.test_gen.testgen import get_tests_from_requirements

requirements_directory = "requirements"
requirements_files = [
    f
    for f in os.listdir(requirements_directory)
    if os.path.isfile(os.path.join(requirements_directory, f))
]


class TestInferenceModel(BaseModel):
    eval_instance: str
    requirement: str
    test_code: str


class TestResultModel(BaseModel):
    buggy_pass_count: int
    buggy_fail_count: int
    fixed_pass_count: int
    fixed_fail_count: int
    output: str
    insights: Optional[str]
    coverage_summary: Optional[str]



def calculate_metrics(result: TestResultModel) -> int:

    buggy_pass_count = result.buggy_pass_count
    buggy_fail_count = result.buggy_fail_count
    fixed_pass_count = result.fixed_pass_count
    fixed_fail_count = result.fixed_fail_count

    if fixed_fail_count != 0:
        return 0
    
    return fixed_pass_count - buggy_pass_count + buggy_fail_count


def run_eval(eval: TestInferenceModel) -> TestResultModel:

    test_code, eval_instance = eval.test_code, eval.eval_instance

    import os

    evalbed_directory = "evalbed"
    if os.path.exists(evalbed_directory):
        shutil.rmtree(evalbed_directory)
        print("Deleted existing evalbed directory")
    os.makedirs(evalbed_directory)

    with open(os.path.join(evalbed_directory, "test_evalbed.py"), "w") as f:
        f.write(test_code)

    shutil.copy(
        os.path.join("buggy", eval_instance + ".py"),
        os.path.join(evalbed_directory, eval_instance + ".py"),
    )



    subprocess.run(["pytest", "-v", "--json-report"],capture_output=True,cwd=evalbed_directory)
    # print("BUGGY TEST RESULT: ", result)
    with open(evalbed_directory + "/.report.json", "r") as f:
        result = json.load(f)

    buggy_pass_count = result["summary"].get("passed", 0)
    buggy_fail_count = result["summary"].get("failed", 0)

    shutil.copy(
        os.path.join("fixed", eval_instance + ".py"),
        os.path.join(evalbed_directory, eval_instance + ".py"),
    )
    subprocess.run(["pytest", "-v", "--json-report"],capture_output=True,cwd=evalbed_directory)

    with open(evalbed_directory + "/" + ".report.json", "r") as f:
        result = json.load(f)

    fixed_pass_count = result["summary"].get("passed", 0)
    fixed_fail_count = result["summary"].get("failed", 0)

    print("BUGGY TEST RESULT: ", buggy_pass_count, buggy_fail_count)
    print("FIXED TEST RESULT: ", fixed_pass_count, fixed_fail_count)

    return TestResultModel(
        buggy_pass_count=buggy_pass_count,
        buggy_fail_count=buggy_fail_count,
        fixed_pass_count=fixed_pass_count,
        fixed_fail_count=fixed_fail_count,
        output=json.dumps(result),
        insights=None,
        coverage_summary=None,
    )


def run_eval_all(evals: List[TestInferenceModel], model : str = "claude-3-haiku-20240307", temperature : float = 0.5,prompt : str = "",num : int = 10):

    total_results: List[TestResultModel] = []
    for eval in evals:
        result = run_eval(eval)
        total_results.append(result)
    # print("RESULT: ", result)

    for result in total_results:
        print("Buggy Pass: ", result.buggy_pass_count)
        print("Buggy Fail: ", result.buggy_fail_count)
        print("Fixed Pass: ", result.fixed_pass_count)
        print("Fixed Fail: ", result.fixed_fail_count)
        print("Metric: ", calculate_metrics(result))
    # print("Total Results: ", total_results)

    average_metric = sum([calculate_metrics(result) for result in total_results]) / num
    print("Average Metric: ", average_metric)

    with open("experiment.json","a") as f:
        f.write(json.dumps({
            "model": model,
            "temperature": temperature,
            "average_metric": average_metric,
            "results": [{
                "buggy_pass_count": result.buggy_pass_count,
                "buggy_fail_count": result.buggy_fail_count,
                "fixed_pass_count": result.fixed_pass_count,
                "fixed_fail_count": result.fixed_fail_count,
            } for result in total_results],
            "prompt": prompt
        }) + "\n")


def get_evals():
    evals = []
    for requirements_file in requirements_files:
        with open(os.path.join(requirements_directory, requirements_file), "r") as f:
            requirement = f.read()
            print("Running eval for: ", requirement)

        evals.append({
            "eval_instance": requirements_file.split(".")[0],
            "requirement": requirement
        })

    return evals



async def run_eval_with_config(model: str, temperature: float,promptv : int):

    inference_file = "-".join([model, str(temperature), str(promptv), "inferences.json"])


    evals = get_evals()
    inferences = []

    if os.path.exists(inference_file):
        with open(inference_file, "r") as f:
            inferences = json.load(f)
            inferences = [TestInferenceModel(**inference) for inference in inferences]
    else:

        for eval in evals:

            import asyncio

            async def generate_inference(eval):
                try:
                    inference = get_tests_from_requirements(eval["requirement"], temperature=temperature, model=model)
                    return TestInferenceModel(
                        eval_instance=eval["eval_instance"],
                        requirement=eval["requirement"],
                        test_code=inference,
                    )
                except Exception as e:
                    print("Error: ", e)
                    return None

            async def generate_inferences(eval,num):
                tasks = [asyncio.create_task(generate_inference(eval)) for _ in range(num)]
                results = await asyncio.gather(*tasks)
                for inference in results:
                    if inference:
                        inferences.append(inference)

            await generate_inferences(eval,10)


        
        with open(inference_file, "w") as f:
            f.write(json.dumps([inference.model_dump() for inference in inferences]))

    with open(inference_file, "r") as f:
        inferences = json.load(f)
        inferences = [TestInferenceModel(**inference) for inference in inferences]

    run_eval_all(inferences, model=model, temperature=temperature, prompt=promptv)

async def main():
    tasks = []
    
    for model, temperature, promptv in experiments:
        tasks.append(asyncio.create_task(run_eval_with_config(model, temperature, promptv)))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    model = "claude-3-sonnet-20240229"
    temperature = 0
    promptv = 2

    experiments = [
        ("claude-3-sonnet-20240229", 0.5, 2),
        ("claude-3-sonnet-20240229", 1, 2),
        ("claude-3-opus-20240229", 0, 2),
        ("claude-3-opus-20240229", 0.5, 2),
        ("claude-3-opus-20240229", 1, 2),
    ]



    asyncio.run(main())



    # import os

    # inferences: List[TestInferenceModel] = []


    # os.mkdir("temp")

    # for inference in inferences:
    #     with open("temp/" + inference.eval_instance + str(random.randint(0, 1000)) + ".py", "w") as f:
    #         f.write(inference.test_code)

    
