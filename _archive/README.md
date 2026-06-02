# Archived Deployment Paths

These directories contain alternative deployment approaches that are no longer the
canonical path for RHDP AI quickstarts. They are preserved for reference.

## What's here

- **agnosticd-config/** — Standalone Ansible playbooks (pre_software, software,
  post_software, destroy_env). Replaced by the Ansible collection at
  `ansible/collections/rhpds/intel_inference/`.

- **agnosticv-catalog/** — Old-format catalog skeleton that referenced the workload
  role directly. Replaced by the agnosticv catalog items at `agnosticv/`.

- **ocp4-workload-intel-rh-inference-demo/** — Original standalone workload role.
  Now lives as a collection role at
  `ansible/collections/rhpds/intel_inference/roles/ocp4_workload_intel_rh_inference_demo/`.

## Canonical deployment path

The RHDP AI quickstart uses:
1. `agnosticv/ai-qs-intel-inference-cluster/` — base cluster provisioning
2. `agnosticv/ai-qs-intel-inference-tenant/` — per-tenant provisioning via
   `rhpds.intel_inference.ocp4_workload_intel_rh_inference_demo` collection role
