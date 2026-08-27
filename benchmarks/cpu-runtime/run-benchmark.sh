#!/usr/bin/env bash
set -euo pipefail

RUNTIME="${1:-}"
NS="intel-cpu-runtime-benchmark"
ROOT="$(cd "$(dirname "$0")" && pwd)"
RESULTS_DIR="$ROOT/results"
REQUESTS="${REQUESTS:-100}"
WARMUP="${WARMUP:-10}"

case "$RUNTIME" in
  ovms)
    MANIFEST="$ROOT/manifests/10-ovms.yaml"
    DEPLOYMENT="ovms-benchmark"
    SERVICE="ovms-benchmark"
    API_PREFIX="v3"
    ;;
  vllm-openvino)
    MANIFEST="$ROOT/manifests/11-vllm-openvino.yaml"
    DEPLOYMENT="vllm-openvino-benchmark"
    SERVICE="vllm-openvino-benchmark"
    API_PREFIX="v1"
    ;;
  *)
    echo "usage: $0 {ovms|vllm-openvino}" >&2
    exit 2
    ;;
esac

mkdir -p "$RESULTS_DIR"
oc delete deployment ovms-benchmark vllm-openvino-benchmark -n "$NS" --ignore-not-found --wait=true
oc apply -f "$MANIFEST"
STARTED="$(date +%s)"
oc rollout status "deployment/$DEPLOYMENT" -n "$NS" --timeout=30m
READY="$(date +%s)"

oc create configmap cpu-benchmark-client -n "$NS" \
  --from-file=benchmark.py="$ROOT/benchmark.py" \
  --dry-run=client -o yaml | oc apply -f -
oc delete job "benchmark-$RUNTIME" -n "$NS" --ignore-not-found --wait=true
oc process -f "$ROOT/manifests/20-benchmark-job.yaml" \
  -p "RUNTIME=$RUNTIME" -p "SERVICE=$SERVICE" -p "API_PREFIX=$API_PREFIX" \
  -p "REQUESTS=$REQUESTS" -p "WARMUP=$WARMUP" | oc apply -f -
oc wait --for=condition=complete "job/benchmark-$RUNTIME" -n "$NS" --timeout=6h
oc logs "job/benchmark-$RUNTIME" -n "$NS" > "$RESULTS_DIR/$RUNTIME.json"
oc adm top pod -n "$NS" -l "app=$DEPLOYMENT" > "$RESULTS_DIR/$RUNTIME-resource-snapshot.txt" 2>/dev/null || true
printf '%s\n' "$((READY - STARTED))" > "$RESULTS_DIR/$RUNTIME-startup-seconds.txt"
oc delete deployment "$DEPLOYMENT" -n "$NS" --wait=true

echo "saved $RESULTS_DIR/$RUNTIME.json"
