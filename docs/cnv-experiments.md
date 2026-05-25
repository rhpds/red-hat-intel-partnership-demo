# GPU Experiments on CNV Clusters

## Policy

- **rac-maas** is the production cluster. Do not deploy inference models directly.
- **GPU model deployments** require Ashok's approval before proceeding.
- **Models** should be consumed through MAAS (`litellm-prod.apps.maas.redhatworkshops.io`).
- **Experiments** must use CNV (OpenShift Virtualization) clusters with virtualized environments.

## Using MAAS for Model Access

The gateway is configured by default to route all inference requests through the MAAS LiteLLM proxy. No local model deployment is needed for most use cases.

```bash
# Test inference through MAAS
curl -X POST https://litellm-prod.apps.maas.redhatworkshops.io/v1/completions \
  -H "Authorization: Bearer $LITELLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "granite", "prompt": "Hello", "max_tokens": 50}'
```

## When You Need Direct GPU Access

If your experiment requires deploying a model directly onto GPU hardware:

1. Coordinate with Ashok for approval
2. Use a CNV cluster (not rac-maas)
3. Follow the manifests in `deploy/gaudi-inference/` as a reference
4. Document your findings for the team

## Local Development Without GPU

For local development, use MAAS endpoints or the local CPU fallback:

```bash
# Default: MAAS mode (requires LITELLM_API_KEY in .env)
podman-compose up --build -d

# Optional: local CPU inference (downloads TinyLlama, ~2GB)
podman-compose --profile local-inference up --build -d
```
