# Arcade Talk Track: The 5-Minute Executive

**Audience**: Partner / Customer executive  
**Duration**: 3–5 minutes  
**Goal**: Show the problem, the architecture, and one live workflow  

---

## Scene 1: Landing Page (45s)

**Page**: Overview (`/`)

**Action**: Open the demo URL. The landing page loads with Intel + Red Hat co-branding and a live health badge.

**Talk track**:
> "This is the Intel–Red Hat AI Inference Platform. It solves a real problem enterprises face today: not every AI workload needs a GPU. A simple HR policy lookup doesn't need the same hardware as a deep security analysis — but most platforms route everything the same way."

**Click**: Scroll to the three hardware cards (Xeon 6 / Gaudi / OpenShift AI).

> "The platform has two hardware paths. Intel Xeon 6 with AMX handles small, fast tasks at a fraction of the cost. Intel Gaudi 3 handles the heavy reasoning. Red Hat OpenShift AI ties them together with intelligent routing."

**Click**: "See How It Works" button.

---

## Scene 2: Architecture (45s)

**Page**: Architecture (`/architecture`)

**Action**: The 5-layer stack diagram is visible.

**Talk track**:
> "Here's the stack. Applications at the top, our routing engine in the middle, OpenShift AI managing the serving runtimes, all running on Intel hardware. The routing engine is the key — it classifies every request and sends it to the right hardware automatically."

**Click**: Scroll to the live backend cards.

> "These are live. You can see each backend's health, what accelerator it's using, and its cost per thousand tokens. The Xeon 6 backends are a fraction of the GPU cost."

**Click**: Navigate to "Try It Live" in the sidebar.

---

## Scene 3: Live Workflow (90s)

**Page**: Try It Live (`/try-it`)

**Action**: The Enterprise RAG tab is selected by default.

**Talk track**:
> "Let's run a real AI workflow. This is Enterprise RAG — Retrieval-Augmented Generation. Four steps, each routed to the right hardware."

**Click**: Click the first scenario card ("Analyze infrastructure risks").

> "Watch what happens. The first three steps — embedding, search, and reranking — run on Xeon 6. They're lightweight operations that don't need a GPU. Only the final answer generation goes to Gaudi."

**Wait**: The 4-step pipeline executes. Each step shows a hardware badge and latency.

> "Three of four steps on Xeon 6 at CPU pricing. The platform made that decision automatically based on what each step actually needs. That's where the cost savings come from — not by compromising quality, but by matching hardware to workload."

**Click**: Navigate to "Run at Scale" in the sidebar.

---

## Scene 4: Scale (60s)

**Page**: Run at Scale (`/workload`)

**Action**: The Incident Storm profile is pre-selected.

**Talk track**:
> "One request is interesting. Let's see what happens at enterprise scale."

**Click**: Set Power Mode to "Drive" (25 requests). Click the scenario card.

> "This is an incident storm — 25 mixed requests hitting the platform simultaneously. Watch the live feed."

**Wait**: Requests stream through. The route distribution builds.

> "Look at the hardware utilization. The platform automatically split the workload — lightweight tasks on Xeon 6, heavy reasoning on Gaudi. No manual configuration, no overprovisioning. Every request got the right hardware for its workload."

---

## Scene 5: Close (30s)

**Talk track**:
> "That's the Intel–Red Hat AI Inference Platform. Intelligent routing across Xeon 6 and Gaudi, running on OpenShift, with full governance and audit trails. It's available today as a Red Hat demo — we can have it running in your environment in under an hour."

---

## Key Messages to Hit

1. **Not every AI workload needs a GPU** — route by workload, not by default
2. **Cost savings are automatic** — the routing engine decides, not the developer
3. **Enterprise-ready** — OpenShift, governance, audit trails, multi-tenant
4. **Intel hardware advantage** — Xeon 6 AMX for small tasks, Gaudi 3 for heavy reasoning
