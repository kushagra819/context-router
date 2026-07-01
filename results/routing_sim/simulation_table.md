# Routing Simulation (offline estimates)

> EXACT for single-tier & oracle; ESTIMATE for mixed/random/content (verifier-tier proxy). Confirm with live `run_experiment.py`.

| dataset | router | N | EM% | cost$ | routeAcc% | over% | under% |
|---|---|---|---|---|---|---|---|
| gsm8k | oracle | 200 | 98.5 | 0.048505 | 100.0 | 0.0 | 0.0 |
| gsm8k | fixed_t1 | 200 | 94.5 | 0.031443 | 95.94 | 0.0 | 4.06 |
| gsm8k | fixed_t2 | 200 | 96.0 | 0.218554 | 2.54 | 95.94 | 2.54 |
| gsm8k | fixed_t3 | 200 | 97.0 | 0.822031 | 1.52 | 98.48 | 1.52 |
| gsm8k | fixed_t4 | 200 | 97.0 | 1.182422 | 0.0 | 100.0 | 1.52 |
| gsm8k | fixed_mixed | 200 | 94.5 | 0.482664 | 95.94 | 0.0 | 4.06 |
| gsm8k | random | 200 | 97.0 | 0.555693 | 29.95 | 69.54 | 1.52 |
