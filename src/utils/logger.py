"""Logging utility for tracking every LLM call."""

import csv
import os
import time
from pathlib import Path
from datetime import datetime


class ExperimentLogger:
    """Logs every LLM call to a CSV file for analysis."""

    FIELDNAMES = [
        "timestamp",
        "experiment_id",
        "problem_id",
        "dataset",
        "agent_role",
        "tier",
        "model_name",
        "router_type",
        "input_tokens",
        "output_tokens",
        "latency_s",
        "cost_usd",
        "correct",
        "escalated_from",
        "response_text",
    ]

    def __init__(self, experiment_id: str, output_dir: str | Path):
        self.experiment_id = experiment_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.filepath = self.output_dir / f"{experiment_id}.csv"
        self.call_count = 0
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Create CSV with headers if file doesn't exist
        if not self.filepath.exists():
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def log_call(
        self,
        problem_id: int | str,
        dataset: str,
        agent_role: str,
        tier: int,
        model_name: str,
        router_type: str,
        input_tokens: int,
        output_tokens: int,
        latency_s: float,
        cost_usd: float,
        correct: bool | None = None,
        escalated_from: int | None = None,
        response_text: str = "",
    ):
        """Log a single LLM call."""
        row = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": self.experiment_id,
            "problem_id": problem_id,
            "dataset": dataset,
            "agent_role": agent_role,
            "tier": tier,
            "model_name": model_name,
            "router_type": router_type,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_s": round(latency_s, 3),
            "cost_usd": round(cost_usd, 6),
            "correct": correct,
            "escalated_from": escalated_from,
            # Truncate response for CSV storage (keep first 500 chars)
            "response_text": response_text[:500].replace("\n", " "),
        }

        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writerow(row)

        self.call_count += 1
        self.total_cost += cost_usd
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def summary(self) -> dict:
        """Return experiment summary stats."""
        return {
            "experiment_id": self.experiment_id,
            "total_calls": self.call_count,
            "total_cost_usd": round(self.total_cost, 4),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "log_file": str(self.filepath),
        }

    def print_summary(self):
        """Print a nice summary to console."""
        s = self.summary()
        print(f"\n{'='*50}")
        print(f"Experiment: {s['experiment_id']}")
        print(f"Total calls: {s['total_calls']}")
        print(f"Total cost:  ${s['total_cost_usd']:.4f}")
        print(f"Total tokens: {s['total_input_tokens']} in + {s['total_output_tokens']} out")
        print(f"Log file:    {s['log_file']}")
        print(f"{'='*50}\n")
