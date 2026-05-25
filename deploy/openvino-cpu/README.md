# OpenShift Manifests - OpenVINO CPU Inference Path

> **IMPORTANT:** These manifests deploy inference servers directly to a cluster.
> For production use, consume models through MAAS
> (`litellm-prod.apps.maas.redhatworkshops.io`) rather than deploying
> your own inference endpoints. Use CNV clusters for experiments.

OpenVINO-based inference deployment for embeddings and classification on Intel Xeon 6 with AMX-BF16 acceleration.
