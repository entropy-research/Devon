


# rsync trajectories
trajectories=$1
pred=$2

echo "Copying trajectories to remote server..."
rsync -avz -e "ssh -i ~/.ssh/hetzner"  --relative $trajectories/ root@5.78.117.161:/root/SWE-agent

echo "Running evaluation script..."
ssh -i ~/.ssh/hetzner root@5.78.117.161 "source miniconda3/bin/activate && cd /root/SWE-agent/evaluation && conda activate swe-agent && sh run_eval.sh /root/SWE-agent/trajectories/$pred/all_preds.jsonl"

echo "Copying results to local machine..."

scp -i ~/.ssh/hetzner root@5.78.117.161:/root/SWE-agent/trajectories/$pred/results.json $trajectories/$pred/results.json
scp -i ~/.ssh/hetzner root@5.78.117.161:/root/SWE-agent/trajectories/$pred/scorecards.json $trajectories/$pred/scorecards.json

