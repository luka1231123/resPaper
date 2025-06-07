from ga_loop import run_experiment

seed=1
exp_id = "noHITL"
k_eval = 10

if __name__ == "__main__":
    run_experiment(exp_id=exp_id, k_eval=k_eval, seed=seed)