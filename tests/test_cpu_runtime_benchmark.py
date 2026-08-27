import importlib.util
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).parent.parent
BENCHMARK_DIR = ROOT / "benchmarks" / "cpu-runtime"


def load_benchmark_module():
    spec = importlib.util.spec_from_file_location("cpu_runtime_benchmark", BENCHMARK_DIR / "benchmark.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def yaml_documents(name):
    return list(yaml.safe_load_all((BENCHMARK_DIR / "manifests" / name).read_text()))


def test_percentile_interpolates():
    module = load_benchmark_module()
    assert module.percentile([1, 2, 3, 4], 50) == 2.5
    assert module.percentile([], 95) == 0.0


def test_endpoint_normalizes_slashes():
    module = load_benchmark_module()
    assert module.endpoint("http://runtime:8000/", "/v3/") == "http://runtime:8000/v3/chat/completions"


def test_same_model_and_resources_for_both_runtimes():
    ovms = yaml_documents("10-ovms.yaml")[0]
    vllm = yaml_documents("11-vllm-openvino.yaml")[0]
    ovms_container = ovms["spec"]["template"]["spec"]["containers"][0]
    vllm_container = vllm["spec"]["template"]["spec"]["containers"][0]
    assert "OpenVINO/Phi-3.5-mini-instruct-int4-ov" in ovms_container["args"]
    assert "OpenVINO/Phi-3.5-mini-instruct-int4-ov" in vllm_container["args"]
    assert ovms_container["resources"] == vllm_container["resources"]


def test_both_runtimes_pin_to_same_non_gpu_node():
    for manifest in ("10-ovms.yaml", "11-vllm-openvino.yaml"):
        deployment = yaml_documents(manifest)[0]
        selector = deployment["spec"]["template"]["spec"]["nodeSelector"]
        assert selector == {"kubernetes.io/hostname": "ocp-rac-maas-worker06"}


def test_safety_quota_caps_benchmark():
    documents = yaml_documents("00-safety.yaml")
    quota = next(doc for doc in documents if doc["kind"] == "ResourceQuota")
    hard = quota["spec"]["hard"]
    assert hard["limits.cpu"] == "72"
    assert hard["limits.memory"] == "160Gi"
    assert hard["pods"] == "6"


def test_vllm_openvino_source_is_commit_pinned():
    containerfile = (BENCHMARK_DIR / "vllm-openvino" / "Containerfile").read_text()
    assert "80830b7e184cc109ac92f26582e6173602910b36" in containerfile
    assert "git checkout" in containerfile
