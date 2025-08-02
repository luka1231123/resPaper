from ga_loop import run_experiment
import config as C
seed=C.SEED
exp_id = "HITL"
k_eval = 0

if __name__ == "__main__":
    run_experiment(exp_id=exp_id, k_eval=k_eval, seed=seed)