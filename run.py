from ga_loop import run_experiment

# tag, k_eval pairs -----------------------------------------------------------
EXPERIMENTS = [
    #("baseline_1", 0),
    #("baseline_2", 0),
    #("hitl_1", 5),
    ("hitl_2", 20),
]

for tag, k in EXPERIMENTS:
    run_experiment(tag, k_eval=k)
