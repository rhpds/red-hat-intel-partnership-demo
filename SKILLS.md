# Claude Code Skills

This project includes Claude Code slash commands for common operations. Type these in any Claude Code session from this project directory.

## Available Skills

### `/deploy`
Build and deploy to the infra01 OpenShift cluster.

```
/deploy              # Deploy gateway + frontend
/deploy gateway      # Deploy gateway only
/deploy frontend     # Deploy frontend only
```

Handles cross-architecture build (arm64 Mac → amd64 cluster), pushes to the internal registry, and triggers a rolling restart. Verifies pods are healthy before returning.

### `/test`
Run the test suite.

```
/test                # Run all tests
/test rag            # Run RAG pipeline tests only
/test chat           # Run chat streaming tests only
/test gateway        # Run gateway tests only
```

### `/scan`
Run NovaScan capacity scanner against this repo or any other.

```
/scan                # Scan this repo
/scan ~/Documents/other-demo       # Scan another repo
/scan ~/Documents/other-demo 60    # Scan with 60-seat lab capacity
```

Returns: provisioning tier, deployment topology, per-seat resources, infrastructure detected, models found, and lab sizing.

### `/novascan` (global)
Same as `/scan` but available from any directory. Installed at `~/.claude/commands/novascan.md`.

## Setup

Skills are stored in `.claude/commands/` (project-level) and `~/.claude/commands/` (global). They're loaded automatically by Claude Code — no installation needed.

To add a new skill, create a markdown file in `.claude/commands/` with the skill name as the filename.

## Related Tools

| Tool | Repo | Purpose |
|------|------|---------|
| **NovaScan** | [rhpds/NovaScan](https://github.com/rhpds/NovaScan) | Capacity scanner — scan repos, recommend provisioning tiers |
| **LiftOff** | ~/Documents/liftoff | Provisioning engine — AgnosticV configs, Ansible roles |
