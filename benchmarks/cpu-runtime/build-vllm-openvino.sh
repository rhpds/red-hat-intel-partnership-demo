#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
IMAGE="${IMAGE:-quay.io/redhat-gpte/intel-vllm-openvino:0.8.4-80830b7}"
COMMIT="80830b7e184cc109ac92f26582e6173602910b36"

podman build --platform linux/amd64 \
  --build-arg "VLLM_OPENVINO_COMMIT=$COMMIT" \
  -t "$IMAGE" \
  -f "$ROOT/vllm-openvino/Containerfile" \
  "$ROOT/vllm-openvino"
podman push "$IMAGE"
