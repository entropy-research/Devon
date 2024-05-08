
#  first argument
if [ -z "$1" ]; then
    echo "Experiment name not specified."
    exit 1
fi
exp_name=$1
# task-list path
task_list_path=${2:-tasklist}
model=${3:-claude-opus}
# temprature with default of 0
temperature=${4:-0}

python3 devon/run_bench.py  --exp_name $exp_name --task_list_path $task_list_path --model $model --temperature $temperature

all_preds_path="/root/Devon/trajectories/${exp_name}/${model}_${temperature}/all_preds.jsonl"

cd ../SWE-bench
source ~/.zshrc
conda activate swe-bench

python3 run_eval_report.py $all_preds_path $exp_name