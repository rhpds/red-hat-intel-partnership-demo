"""Training demo models — profiles, runs, and serving candidates."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


MODEL_PROFILES = {
    "qwen_2_5_7b": {"family": "Qwen", "name": "Qwen2.5-7B", "params_b": 7, "task": "incident RCA / operations assistant", "training_lane": "gaudi_overdrive", "serving_lane": "gaudi_overdrive"},
    "qwen_2_5_coder_7b": {"family": "Qwen Coder", "name": "Qwen2.5-Coder-7B", "params_b": 7, "task": "build failure explanation / code summary", "training_lane": "gaudi_overdrive", "serving_lane": "gaudi_overdrive"},
    "qwen_2_5_vl_7b": {"family": "Qwen VL", "name": "Qwen2.5-VL-7B", "params_b": 7, "task": "dashboard screenshot interpretation / multimodal", "training_lane": "gaudi_overdrive", "serving_lane": "gaudi_overdrive"},
    "llama_3_1_8b": {"family": "Llama", "name": "Llama-3.1-8B", "params_b": 8, "task": "incident RCA / platform assistant", "training_lane": "gaudi_overdrive", "serving_lane": "gaudi_overdrive"},
    "granite_ops_model": {"family": "Granite", "name": "Granite-Ops", "params_b": 3, "task": "OpenShift troubleshooting / enterprise assistant", "training_lane": "gaudi_overdrive", "serving_lane": "gaudi_overdrive"},
    "phi_small_utility": {"family": "Phi", "name": "Phi-Small", "params_b": 1.5, "task": "lightweight classification / route helper", "training_lane": "xeon_performance", "serving_lane": "xeon_performance"},
}

DATASET_PROFILES = {
    "synthetic_incident_rca_v1": {"task_type": "incident_rca", "modality": "text", "sample_count": 1000, "train_count": 800, "eval_count": 200, "synthetic": True, "description": "Synthetic incident alerts, logs, service metadata, and expected RCA summaries."},
    "synthetic_openshift_troubleshooting_v1": {"task_type": "openshift_troubleshooting", "modality": "text", "sample_count": 500, "train_count": 400, "eval_count": 100, "synthetic": True, "description": "OpenShift error messages, oc describe/events/logs snippets, and expected explanations."},
    "synthetic_dashboard_vision_v1": {"task_type": "dashboard_vision", "modality": "image", "sample_count": 300, "train_count": 240, "eval_count": 60, "synthetic": True, "description": "Dashboard screenshot metadata, chart descriptions, visible symptoms, and expected summaries."},
    "synthetic_code_failure_v1": {"task_type": "code_failure", "modality": "text", "sample_count": 400, "train_count": 320, "eval_count": 80, "synthetic": True, "description": "Build/test failures, stack traces, code snippets, and expected fix explanations."},
    "synthetic_small_classifier_v1": {"task_type": "small_classifier", "modality": "text", "sample_count": 2000, "train_count": 1600, "eval_count": 400, "synthetic": True, "description": "Request metadata, task types, expected route class, and priority class for Xeon-side utility model."},
}

TRAINING_TASKS = {
    "incident_rca_finetune": {"model_profiles": ["qwen_2_5_7b", "llama_3_1_8b"], "datasets": ["synthetic_incident_rca_v1"]},
    "openshift_troubleshooting_finetune": {"model_profiles": ["granite_ops_model", "llama_3_1_8b"], "datasets": ["synthetic_openshift_troubleshooting_v1"]},
    "dashboard_vision_finetune": {"model_profiles": ["qwen_2_5_vl_7b"], "datasets": ["synthetic_dashboard_vision_v1"]},
    "code_failure_finetune": {"model_profiles": ["qwen_2_5_coder_7b"], "datasets": ["synthetic_code_failure_v1"]},
    "small_classifier_tune": {"model_profiles": ["phi_small_utility"], "datasets": ["synthetic_small_classifier_v1"]},
}

VALID_TRAINING_MODES = {"mock_lora", "mock_sft", "real_lora", "real_sft", "real_qlora", "real_adapter_merge"}
VALID_STATUSES = {"created", "running", "completed", "failed", "skipped", "simulated"}
VALID_HARDWARE_LANES = {"xeon_eco", "xeon_performance", "gaudi_overdrive", "unknown"}


@dataclass
class TrainingRun:
    training_run_id: str
    demo_task: str
    model_profile_id: str
    base_model_name: str
    dataset_id: str
    dataset_version: str = "v1"
    training_mode: str = "mock_lora"
    hardware_lane: str = "gaudi_overdrive"
    status: str = "created"
    started_at: str = ""
    completed_at: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    evaluation: Dict[str, Any] = field(default_factory=dict)
    loss_curve: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServingCandidate:
    serving_candidate_id: str
    training_run_id: str
    model_profile_id: str
    artifact_ref: str
    target_lane: str
    status: str = "created"
    endpoint_ref: str = ""
    created_at: str = ""


def list_model_profiles() -> list[dict]:
    return [{"id": k, **v} for k, v in MODEL_PROFILES.items()]


def list_dataset_profiles() -> list[dict]:
    return [{"id": k, **v} for k, v in DATASET_PROFILES.items()]


def list_training_tasks() -> list[dict]:
    return [{"id": k, **v} for k, v in TRAINING_TASKS.items()]
