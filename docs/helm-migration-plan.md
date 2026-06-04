# Helm+Make Migration Plan — Intel Demo

## Context

All production RHDP AI quickstarts use the `quickstart_deploy_via_make` pattern:
- App repo contains a `helm/` directory with Chart.yaml, values.yaml, templates/
- AgnosticV tenant config calls `agnosticd.ai_quickstarts.quickstart_deploy_via_make`
- This role clones the repo and runs `make install` in the helm/ directory

Our Intel demo currently uses custom Ansible roles in `rhpds.intel_inference` to deploy each component (gateway, frontend, postgres) via Jinja2 templates. This works but diverges from the standard pattern, making it harder for the RHDP team to maintain.

## What Changes

### Create: `helm/` directory in demo repo

```
helm/
  Chart.yaml
  values.yaml
  Makefile              # install/uninstall targets
  templates/
    namespace.yaml
    secrets.yaml
    gateway-configmap.yaml
    postgres-deployment.yaml
    postgres-service.yaml
    postgres-pvc.yaml
    gateway-deployment.yaml
    gateway-service.yaml
    gateway-route.yaml
    frontend-deployment.yaml
    frontend-service.yaml
    frontend-route.yaml
```

### values.yaml (replaces Ansible defaults/main.yml)

```yaml
namespace: "{{ .Release.Namespace }}"

gateway:
  image: quay.io/intel-redhat/inference-gateway:latest
  replicas: 2
  resources:
    requests: { cpu: 500m, memory: 256Mi }
    limits: { cpu: "1", memory: 512Mi }

frontend:
  image: quay.io/intel-redhat/inference-frontend:latest
  replicas: 1
  resources:
    requests: { cpu: 100m, memory: 64Mi }
    limits: { cpu: 500m, memory: 128Mi }

postgres:
  enabled: true
  image: registry.redhat.io/rhel9/postgresql-15:latest
  storage: 10Gi
  resources:
    requests: { cpu: 250m, memory: 256Mi }
    limits: { cpu: "1", memory: 512Mi }

litellm:
  apiBase: ""   # Set by agnosticv
  apiKey: ""    # Set by agnosticv secret

localCpuInference:
  enabled: false
  image: quay.io/intel-redhat/vllm-cpu:latest
  model: TinyLlama/TinyLlama-1.1B-Chat-v1.0
  resources:
    requests: { cpu: "4", memory: 8Gi }
    limits: { cpu: "8", memory: 16Gi }
  modelCacheSize: 20Gi

rateLimit:
  rpm: 85
```

### Makefile (in helm/)

```makefile
NAMESPACE ?= default
RELEASE ?= intel-inference

install:
	helm upgrade --install $(RELEASE) . \
		--namespace $(NAMESPACE) \
		--create-namespace \
		$(EXTRA_HELM_ARGS)

uninstall:
	helm uninstall $(RELEASE) --namespace $(NAMESPACE)
```

### AgnosticV tenant config changes

Replace the custom Ansible role reference with the standard make-based deploy:

```yaml
# Before (LiftOff custom roles):
workloads:
  - rhpds.intel_inference.ocp4_workload_intel_rh_inference_demo
  - rhpds.intel_inference.ocp4_workload_intel_cpu_inference

# After (standard quickstart pattern):
workloads:
  - agnosticd.ai_quickstarts.quickstart_deploy_via_make

quickstart_deploy_via_make_repo_url: https://github.com/rhpds/red-hat-intel-partnership-demo
quickstart_deploy_via_make_scm_ref: main
quickstart_deploy_via_make_directory: helm
quickstart_deploy_via_make_params:
  NAMESPACE: "user-{{ guid }}-intel-inference"
  EXTRA_HELM_ARGS: >-
    --set litellm.apiKey={{ litellm_virtual_key }}
    --set litellm.apiBase={{ litellm_api_endpoint }}
    --set postgres.password={{ common_password }}
```

## What Stays the Same

- The demo app code (gateway, frontend) doesn't change
- Container images don't change
- The provisioning flow (Sandbox API → namespace → deploy) doesn't change
- The three-tier model (pilot/partner/dedicated) doesn't change

## What Gets Removed from LiftOff

- `ansible/collections/rhpds/intel_inference/roles/ocp4_workload_intel_rh_inference_demo/` (replaced by Helm)
- `ansible/collections/rhpds/intel_inference/roles/ocp4_workload_intel_cpu_inference/` (merged into Helm)
- All Jinja2 templates (replaced by Helm templates)

## Benefits

1. Follows the standard RHDP pattern — easier for the platform team to maintain
2. CheckSum can parse `values.yaml` for accurate resource estimates
3. Developers can test locally with `helm install` without needing Ansible
4. `helm diff` for change review before deploying
5. Values file serves as documentation of all configurable parameters

## Risks

- Helm templates are less flexible than Ansible (no conditional role inclusion)
- The `localCpuInference.enabled` flag replaces the Ansible role split
- Need to validate Helm works with the Sandbox API provisioner
- Migration period where both patterns exist

## Implementation Order

1. Create `helm/` in demo repo with Chart.yaml, values.yaml, templates
2. Convert each Ansible Jinja2 template to Helm template
3. Test `make install` locally against a cluster
4. Update one LiftOff agnosticv config to use `quickstart_deploy_via_make`
5. Validate end-to-end through Sandbox API
6. Migrate remaining tiers
7. Remove Ansible roles from LiftOff collection
