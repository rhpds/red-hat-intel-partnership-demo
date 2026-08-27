# CPU Runtime Benchmark: OVMS vs vLLM with OpenVINO

This benchmark compares two serving stacks on the same Intel Xeon 6767P node:

1. OpenVINO Model Server (OVMS) 2025.3
2. vLLM 0.8.4 with the upstream OpenVINO platform plugin

Both serve `OpenVINO/Phi-3.5-mini-instruct-int4-ov` with identical CPU and
memory limits. The runtimes run sequentially on
`ocp-rac-maas-worker06` to avoid cross-runtime contention.

## Safety boundary

- Namespace: `intel-cpu-runtime-benchmark`
- Namespace quota: 72 CPU, 160 GiB RAM, 6 pods, 200 GiB storage
- Runtime allocation: 64 CPU, 128 GiB RAM
- Load generator allocation: 4 CPU, 8 GiB RAM
- No resources are created in `llm-hosting` or `maas-rhdp-dev`
- Runtime deployments are removed after each benchmark arm
- The PVC is retained until results are verified, then may be deleted

## Metrics

- Model startup time
- Time to first token (TTFT): p50, p95, p99
- End-to-end latency: p50, p95, p99
- Inter-token latency
- Output tokens per second
- Requests per second
- Success/error/timeout rate
- Runtime CPU and memory usage (captured separately from OpenShift metrics)

The matrix uses concurrency 1, 2, 4, and 8 with short, medium, and long
prompt/output profiles. Ten warm-up requests precede 100 measured requests per
cell by default.

## Build and run

The vLLM-OpenVINO image is built inside the isolated namespace because no
prebuilt upstream image is available:

```bash
oc apply -f manifests/00-safety.yaml
oc apply -f manifests/01-storage.yaml
oc apply -f manifests/02-vllm-openvino-build.yaml
oc start-build vllm-openvino --follow -n intel-cpu-runtime-benchmark

./run-benchmark.sh ovms
./run-benchmark.sh vllm-openvino
python3 compare.py results/ovms.json results/vllm-openvino.json
```

For a low-cost validation before the full matrix:

```bash
REQUESTS=5 WARMUP=1 ./run-benchmark.sh ovms
REQUESTS=5 WARMUP=1 ./run-benchmark.sh vllm-openvino
```

The runtime is pinned to worker06. The client is pinned to worker04 so load
generation does not consume the CPU allocation being measured.

Do not run both runtime deployments simultaneously. Do not change the selected
node or quota without re-checking production headroom.
