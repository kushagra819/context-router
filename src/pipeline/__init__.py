"""Unified multi-agent pipeline (baselines + routed experiments)."""

from src.pipeline.dataset_adapters import (
    DatasetAdapter,
    Problem,
    get_adapter,
    available_datasets,
    ROLES,
)
from src.pipeline.routed_pipeline import RoutedPipeline, PipelineResult, AgentCall

__all__ = [
    "DatasetAdapter",
    "Problem",
    "get_adapter",
    "available_datasets",
    "ROLES",
    "RoutedPipeline",
    "PipelineResult",
    "AgentCall",
]
