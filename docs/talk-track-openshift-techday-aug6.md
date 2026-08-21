# Red Hat OpenShift Tech Day — Intel SA Enablement
## Presenter Script (30-45 min)
### August 6, 2026

---

**Target audience:** Intel Solution Architects
**Format:** Presentation with discussion, no live demo (demo platform referenced for follow-up)
**Pacing:** ~2 min per slide average, with deeper dwell on slides 4, 7-8, 11-12, and 16

---

## SLIDE 1 — Title
**[~1 min]**

> Good afternoon everyone, and welcome to the Red Hat OpenShift Tech Day.
>
> I'm Jonathan Kershaw — most people just call me Kersh — I'm on the Portfolio team at Red Hat, and I spend my time making open source software do interesting things on Intel hardware.
>
> Today's session is specifically for you, as Intel SAs, and here's why: when you're sitting across from a customer talking about Xeon 6 or Gaudi, the conversation increasingly lands on "what platform runs all of this?" The answer is OpenShift. And by the end of today, you'll be able to talk about it with confidence.
>
> This is not a certification course. It's a working session — I want you fluent enough to have that first platform conversation with a customer, and to know exactly where to go deeper.

---

## SLIDE 2 — Why We're Here
**[~2 min]**

> Four outcomes. Let me walk through them because they frame everything else.
>
> **One: Understand.** By the time we're done, you'll be fluent in the OpenShift environment — what it is, how it's built, and how it gets installed. Not just "it's Kubernetes" — the actual architecture and the decisions behind it.
>
> **Two: Go deeper.** This is the first of two sessions. Today is the platform. The follow-on OpenShift AI tech day builds on this foundation and puts actual AI workloads on top — model serving, inference, the whole stack. You need today's context before that session makes sense.
>
> **Three: Enable partners.** This is the commercial reason we're all here. You take what you learn today and use it in partner conversations. When a partner asks "why wouldn't I just run upstream Kubernetes?" — you'll have a real answer, not a marketing slide.
>
> **Four: Bring it back.** When you find a real customer use case — and you will — bring it back to the Red Hat and Intel team. That's how joint wins happen.
>
> The baseline goal is simple: every SA in this room leaves with the same understanding of the OpenShift environment.

---

## SLIDE 3 — Agenda
**[~1 min]**

> Here's the plan for the next 30-odd minutes.
>
> We start with what OpenShift actually is — and specifically what Red Hat adds on top of upstream Kubernetes, because that's the question you'll get asked most.
>
> Then architecture — control plane, worker nodes, the immutable OS underneath everything. The stuff that matters when someone asks "how does this thing work?"
>
> Then installation — four supported paths, enough detail that you can walk a customer through what an install looks like without ever touching a terminal.
>
> Then we bring it home to Intel — where Xeon and accelerators fit in, and the partner sell motion you'll take into the field.
>
> Let's get into it.

---

## SLIDE 4 — What is Red Hat OpenShift?
**[~3 min]**

> Let's start with the one-liner: OpenShift is Red Hat's enterprise application platform, built on Kubernetes.
>
> Now, that sentence does a lot of work, so let me unpack it.
>
> **Kubernetes at the core.** This is 100% upstream Kubernetes. Not a fork, not a proprietary flavor. The APIs are the same. The ecosystem tools work. If a customer has Kubernetes skills, those skills transfer directly. No lock-in at the orchestration layer.
>
> **Batteries included.** This is where it diverges from upstream. Out of the box, you get CI/CD pipelines, monitoring, logging, an internal image registry, and a software-defined networking stack. With upstream Kubernetes, you have to assemble all of that yourself — choose a CNI plugin, choose a monitoring stack, choose a CI system, wire them together, and then maintain every one of those choices independently. OpenShift ships it integrated and tested.
>
> **Runs anywhere.** Bare metal in your datacenter, virtualized on VMware or RHEV, private cloud, public cloud — AWS, Azure, GCP — and at the edge. Same platform, same APIs, same operational model everywhere. That's the hybrid cloud story in practice, not just in a deck.
>
> **Fully supported.** One Red Hat subscription covers the whole stack — the OS, the platform, the services on top. One vendor to call, one SLA, one throat to grab if something goes wrong at 2 AM.
>
> The key mental model — and this is the thing I'd want you to take away — is that Kubernetes gives you the engine. OpenShift gives you the paved road. The developer experience, the security guardrails, and the lifecycle automation that make it production-ready on day one, not day ninety.

---

## SLIDE 5 — OpenShift vs. Plain Kubernetes
**[~3 min]**

> This is the comparison slide you'll use most in customer conversations, so let me walk through it carefully.
>
> On the left: upstream Kubernetes. It's a container orchestration engine, and it's excellent at that job. But that's where it stops. Everything else — you assemble yourself. You pick a CI/CD system. You pick a container registry. You figure out logging. You harden security manually. And you handle your own installations and upgrades. The Kubernetes project explicitly says: "we give you the building blocks, you build the house."
>
> On the right: OpenShift. Everything Kubernetes does, plus...
>
> **Integrated build, CI/CD, and GitOps.** OpenShift Pipelines — based on Tekton — and OpenShift GitOps — based on Argo CD — ship with the platform. Developers get a paved path from code commit to running container without stitching together three different open source projects.
>
> **Enterprise support and lifecycle.** This is a big one. Red Hat supports OpenShift releases for over 10 years. Kubernetes upstream releases every four months and each release is supported for about 14 months. If you're an enterprise that needs stability, that's a real gap.
>
> **Secure by default.** Every node runs Red Hat Enterprise Linux CoreOS — RHCOS — which is immutable and container-optimized. SELinux is enforced, not optional. Security Context Constraints — SCCs — restrict what containers can do out of the box. The default posture is locked down; you open things up deliberately, not the other way around.
>
> **Built-in registry, monitoring, logging, networking.** Prometheus and Grafana for monitoring. Elasticsearch and Kibana for logging. An internal image registry. OVN-Kubernetes for networking. All integrated, all supported.
>
> **Operators for everything.** Installation, upgrades, day-2 operations — all driven by Operators. One-click upgrades through the console. That's not a small thing when you're running 50 clusters.
>
> The short version for a customer conversation: "Kubernetes is the engine. You can build everything around it yourself — or you can get it pre-built, integrated, tested, and supported. That's OpenShift."

---

## SLIDE 6 — One Consistent Platform, Everywhere
**[~2 min]**

> This is the "runs anywhere" story in visual form.
>
> The point here isn't just that OpenShift can be installed on different infrastructure — lots of things can be installed on different infrastructure. The point is it's the **same platform** everywhere.
>
> Same APIs. Same console. Same operational model. Same security posture. An application you build and test on OpenShift in your datacenter runs the same way on OpenShift in AWS, in Azure, at the edge.
>
> For Intel, this matters because it means Xeon 6 workloads run the same way whether the customer's cluster is on bare metal in their datacenter or in a cloud provider's Xeon-based instances. The platform doesn't change. The operational experience doesn't change. The only thing that changes is where the silicon lives.
>
> And that's a selling point for both of us — Intel doesn't care where the customer runs, as long as they're running on Intel. Red Hat doesn't care where the customer runs, as long as they're running on OpenShift. Happy coincidence.

---

## SLIDE 7 — Architecture at a Glance
**[~3 min]**

> Let's look at the full stack. This is OpenShift top to bottom, and it's worth understanding each layer because you'll reference them in conversations.
>
> **Start at the bottom: infrastructure.** Physical servers, virtual machines, private cloud, public cloud, edge. OpenShift abstracts across all of them. This is the layer where Intel silicon lives — Xeon CPUs, Gaudi accelerators, network adapters, the hardware.
>
> **One layer up: RHEL CoreOS.** This is the operating system on every single node. It's immutable — you don't SSH in and install packages. It's container-optimized — the OS exists to run containers, nothing else. And SELinux is enforced everywhere. This is the security foundation.
>
> **Then Kubernetes.** The API server, the scheduler, etcd for state, controllers, and Operators. Standard Kubernetes components, but managed and upgraded as a unit through the OpenShift lifecycle.
>
> **Platform services.** Networking — OVN-Kubernetes by default. Storage — CSI drivers for whatever backend you're using. The internal registry. Monitoring with Prometheus. Logging. Security services including OAuth, RBAC, and those Security Context Constraints I mentioned.
>
> **Developer services.** The developer console, build pipelines, CI/CD, GitOps, and the OperatorHub — a marketplace of pre-packaged capabilities you can install with a click.
>
> **And at the top: applications.** Containers, virtual machines — yes, OpenShift runs VMs natively through OpenShift Virtualization — serverless functions, and AI/ML models. All on the same platform, scheduled by the same control plane.
>
> The callout at the bottom is the key message: every layer of this stack runs on Intel architecture. From the bare metal up to the models being served. That's the "full stack, co-engineered" story.

---

## SLIDE 8 — How a Cluster is Built
**[~3 min]**

> Let's zoom into the architecture and look at how a cluster is actually constructed. Two types of nodes.
>
> **Control plane — three nodes for high availability.** These run the brains of the cluster:
>
> - The **kube-apiserver** — every interaction with the cluster goes through this. CLI commands, console clicks, API calls from applications. It's the front door.
> - **etcd** — the distributed key-value store that holds all cluster state. This is the thing you back up. If you lose etcd, you lose the cluster's memory.
> - The **scheduler** — decides which worker node runs each pod, based on resource requests, affinity rules, and constraints.
> - The **controller manager** — runs the control loops that watch the desired state and make the actual state match.
> - **Cluster Operators** — these are the OpenShift-specific addition. Each one manages a specific piece of the platform — networking, monitoring, ingress, the image registry. They handle installation, configuration, and upgrades of their component automatically.
>
> **Worker nodes — this is where your workloads actually run.** And this is where you scale out on Intel Xeon. Each worker node runs:
>
> - A **kubelet** — the agent that talks to the control plane and manages pods on that node.
> - **CRI-O** — the container runtime. Not Docker — CRI-O is lighter, purpose-built for Kubernetes, and it's what OpenShift uses by default.
> - **kube-proxy** — handles network rules so pods can talk to each other and to the outside world.
> - And then **your pods** — your actual application workloads.
>
> Underneath everything, on every node, control plane and worker: **RHEL CoreOS**. Immutable, container-optimized, SELinux enforced.
>
> When a customer asks "how big does the control plane need to be?" — the answer for most production deployments is three nodes, and they don't need to be massive. The compute investment goes into worker nodes, which is where the Intel Xeon story really plays.

---

## SLIDE 9 — Key Concepts / Building Blocks
**[~1 min]**

> Quick vocabulary check — you'll see these on the slide and hear them in every OpenShift conversation.
>
> **Pods** run your containers. **Deployments** describe how many you want and keep them running. **Services** give pods a stable network address. **Routes** expose them externally with a URL.
>
> The one to remember: **Operators**. They encode operational knowledge — install, configure, upgrade, repair — into code that runs inside the cluster. The platform itself is managed by Operators, and customers add more from the OperatorHub for things like databases, accelerator support, and AI tooling.
>
> **Projects** give you logical isolation — different teams, different security policies, same cluster.
>
> These are on the slide for reference. Let's keep moving.

---

## SLIDE 10 — Section Break: How OpenShift Installs
**[~30 sec]**

> OK, you understand what OpenShift is and how it's built. Now let's talk about how it gets installed.
>
> Four supported paths. I'll give you enough detail to walk a customer through an install conversation without ever opening a terminal. That's the goal — you don't need to be the installer, you need to be able to explain what happens.

---

## SLIDE 11 — Four Ways to Install
**[~3 min]**

> Four installation methods, each for a different scenario.
>
> **Installer-Provisioned Infrastructure — IPI.** This is the fully automated path. You provide a configuration file, the installer provisions the infrastructure — VMs, networking, DNS — and builds the cluster end to end. This is the path for cloud deployments on AWS, Azure, GCP, and for bare-metal environments with BMC/IPMI access. Lowest effort, most opinionated.
>
> **User-Provisioned Infrastructure — UPI.** You provision the infrastructure yourself — VMs, networking, load balancers, DNS — and then the installer builds the cluster on top of what you've prepared. This is for environments where the customer has existing infrastructure automation, or where security policy requires pre-provisioned machines. More control, more work.
>
> **Agent-Based Installer.** This is the newer approach, and the one you'll likely see most in the field. It generates a bootable ISO. You boot your servers from it — bare metal or VM — and the installer discovers the nodes, validates hardware, and builds the cluster. No bootstrap node required, works in disconnected environments. This is the path for bare-metal data center deployments on Intel hardware.
>
> **Assisted Installer.** A hosted SaaS service at console.redhat.com. You register your nodes, it generates a discovery ISO, you boot from it, and a wizard walks you through the rest. Lowest barrier to entry, great for demos and proofs of concept. The catch: it needs outbound internet access to the hosted service.
>
> For your Intel conversations, the agent-based installer is usually the most relevant. Customer has Xeon servers in a rack, wants OpenShift — agent-based installer, boot from ISO, done in under an hour.

---

## SLIDE 12 — What an Install Looks Like
**[~3 min]**

> Let me make that concrete. This is the actual flow for a bare-metal install on Intel Xeon servers. Six steps.
>
> **Step one: Prepare.** DNS records, DHCP or static IPs, a load balancer for the API and ingress endpoints, and your pull secret from console.redhat.com. Confirm the Intel hardware meets the minimums — and for Xeon 6, it will, comfortably.
>
> **Step two: Configure.** Write the `install-config.yaml`. This is the single configuration file that defines your cluster — how many nodes, what network CIDRs, what platform you're targeting, your pull secret, your SSH key. It's YAML, it's version-controlled, it's repeatable.
>
> **Step three: Generate.** Run `openshift-install` — it reads your config, generates Kubernetes manifests and Ignition configs, and builds the bootable ISO or agent image. Everything the cluster needs to bootstrap itself is baked into that artifact.
>
> **Step four: Bootstrap.** A temporary bootstrap node stands up the initial control plane — the API server, etcd, the core operators. Once the permanent control plane is healthy, the bootstrap node hands off and can be removed. It's scaffolding, not permanent infrastructure.
>
> **Step five: Provision.** Control plane nodes boot RHCOS from the generated image, pull their Ignition config, and join the cluster. Then worker nodes do the same. Each node is configured identically from the same source of truth.
>
> **Step six: Ready.** The installer prints a console URL and drops a `kubeconfig` file. You're live. The whole thing, once prerequisites are in place, takes under an hour.
>
> This is not a "three-day engagement" install. It's automated, repeatable, and fast. And that matters when you're trying to get a customer to proof-of-concept stage quickly.

---

## SLIDE 13 — Cluster Topologies
**[~1 min]**

> Three sizes. **SNO** — one Xeon server, control plane and workloads together. Edge, demos, quick proofs of concept. **Compact** — three nodes wearing both hats. Full HA, real workloads, sweet spot for PoCs. **Standard HA** — three dedicated control plane plus as many workers as the job demands. Production.
>
> The question to ask: "What's the use case, and where does it run?" Match the topology to the answer.

---

## SLIDE 14 — Intel + OpenShift
**[~3 min]**

> Now let's bring this back to Intel, because this is where the two stories converge.
>
> OpenShift is the platform. Intel provides the silicon underneath it. And they're co-engineered — not just "tested on" — actually co-engineered upstream.
>
> **Intel Xeon 6 with AMX.** Advanced Matrix Extensions are built into the CPU. That means matrix math — the kind AI inference depends on — runs on hardware you're already buying for general-purpose compute. No additional accelerator card for many inference workloads. The customer's existing Xeon 6 servers can serve models today.
>
> **Intel Gaudi accelerators.** When the workload genuinely needs dedicated AI silicon — large model training, high-throughput inference at scale — Gaudi plugs into the same OpenShift cluster. Same scheduler, same management plane, same operational model. You don't build a separate AI cluster.
>
> **Intel networking and storage.** Ethernet adapters, IPUs, Optane — the infrastructure layer is Intel silicon too. OpenShift's networking and storage abstractions run on top of Intel hardware at every level.
>
> **The Node Feature Discovery and device plugin operators.** These are the glue. NFD automatically detects Intel hardware capabilities — AMX support, GPU presence, specific CPU features — and labels the nodes. The Intel device plugin operator exposes accelerators as schedulable Kubernetes resources. Together, they let OpenShift schedule workloads to the right hardware automatically.
>
> The message for partner conversations: Intel provides the full silicon portfolio. Red Hat provides the platform. Together, the customer gets one consistent environment from CPU to accelerator, and they don't have to choose one or the other — they use both, matched to the workload.

---

## SLIDE 15 — Foundation for OpenShift AI
**[~2 min]**

> Everything we've covered today is the foundation. The next tech day builds directly on top of it.
>
> OpenShift AI is where you go from "I have a platform" to "I'm serving models, running inference, building AI applications." It adds model serving — vLLM, llm-d — model training, data science notebooks, pipeline orchestration. All on the same cluster, the same Intel silicon.
>
> The reason we're doing this in two sessions and not one: you need to understand the platform before the AI layer makes sense. When someone asks "where does the model server run?" the answer is "in a pod, on a worker node, scheduled by the control plane, on Intel Xeon or Gaudi hardware." Every one of those terms should now mean something specific to you.
>
> The follow-on session will cover model serving on Xeon 6 with AMX, GPU scheduling with Gaudi, the llm-d distributed inference engine, and the hands-on labs where you run it yourself.
>
> Today: the platform. Next time: the AI workloads. Full stack, co-engineered by Intel and Red Hat.

---

## SLIDE 16 — The Partner Sell Motion
**[~3 min]**

> OK, let's talk about how you actually use this.
>
> You're Intel SAs. You sell silicon. The question is: how does OpenShift make your silicon sale easier?
>
> **Conversation starter.** When a customer is evaluating AI infrastructure, the platform question comes up fast. "Where do I run my models?" If you can position OpenShift as the answer — and now you can — you've anchored the conversation on Intel hardware. OpenShift runs on Xeon. The AI workloads run on Xeon and Gaudi. The platform sale pulls the silicon sale through.
>
> **Proof of concept path.** This is the tactical play. Customer has a use case. You propose a compact three-node cluster on Xeon 6, install OpenShift with the agent-based installer, deploy a model, and show inference running on their hardware. That's a PoC you can execute in a day, not a quarter.
>
> **Differentiation from hyperscaler lock-in.** Every cloud provider has a managed Kubernetes service. But those services are tuned for that cloud's ecosystem. OpenShift runs the same everywhere — on-prem on Intel bare metal, in any cloud, at the edge. The customer isn't locked into one cloud's AI stack. They own their platform, they own their data, they run on Intel silicon wherever they choose.
>
> **The joint team.** When you find a real opportunity, you don't carry it alone. You bring in the Red Hat team, we build it together. Intel brings the hardware expertise and the customer relationship. Red Hat brings the platform and the AI stack. Joint wins.
>
> The outcome we want from today: SAs who can position Intel plus OpenShift confidently, and a repeatable path from first conversation to joint proof of concept.

---

## SLIDE 17 — Takeaways
**[~2 min]**

> Let me run through what you're leaving with today. Six things you can now do.
>
> **Explain OpenShift.** You can describe what it is and — critically — how it differs from plain Kubernetes. That comparison slide is your best friend.
>
> **Read the architecture.** You can point to the control plane, the worker nodes, RHCOS, and the operator framework. When someone draws a diagram, you can follow it.
>
> **Talk through an install.** You can walk a customer through the four install methods and the six-step install flow. You know which method to recommend for which scenario.
>
> **Right-size a cluster.** SNO for edge, compact for PoCs, standard HA for production. You can match the topology to the use case.
>
> **Position the Intel value.** You can connect Xeon 6, AMX, Gaudi, and the device plugin operators to the OpenShift platform story. The silicon and the platform, together.
>
> **Tee up the next conversation.** Whether that's the OpenShift AI tech day, a hands-on lab, or a customer PoC — you know where this goes next.
>
> That's six things you couldn't do an hour ago. Not bad for a Wednesday.

---

## SLIDE 18 — Training Sessions and Next Steps
**[~2 min]**

> Logistics. Three things on your radar.
>
> **The AI Forum sessions** hosted by Stewart Gretchen — there's an OpenShift AI fundamentals session on August 26th. If you want the deeper AI layer, that's the one to join. It builds directly on what we covered today.
>
> **The OpenShift Setup Lab.** This is optional, self-paced, hands-on. If you want to actually install OpenShift yourself — on a VM, with your own hands — email Sridhar and Caiti for VM access. The guide walks you through installation and configuration step by step. I'd recommend it. There's a difference between understanding an install and having done one.
>
> **SMG Tech Accelerate on September 17th.** This is the big one. Hands-on workshop: Agentic AI with Intel Xeon and Red Hat AI. You'll deploy models using Model-as-a-Service in OpenShift AI and implement agentic AI quickstarts. This is where it goes from slides to working code. Registration link is on the slide.
>
> If you do one thing after today, register for Tech Accelerate. That's where you'll get hands-on with the AI workloads and walk away with something you can demo to a customer.

---

## SLIDE 19 — Section Break: Demo Platform
**[~30 sec]**

> Before we wrap, let me show you one more thing — the tool you'll actually use when you want to get hands-on or show this to a customer. The Red Hat Demo Platform.

---

## SLIDES 20-22 — Red Hat Demo Platform, Catalog, and Lab Example
**[~3 min total]**

> This is the Red Hat Demo Platform — RHDP. Self-service catalog of curated workshops, demos, and training environments. OpenShift, OpenShift AI, AMQ Streams, CodeReady Workspaces — all pre-built, all provisioned on demand.
>
> **How do you get in?** RHDP portal, partner credentials. No special access request.
>
> **How does it work?** Browse the catalog, pick a tile, order it. The platform provisions your environment — takes 15 minutes to an hour depending on size. You get connection instructions by email. The Intel-specific tiles are in here too — model deployment on Xeon 6, AI inference labs.
>
> *(advance to slide 22)*
>
> And this is what it looks like inside a lab. Browser-based workspace, everything pre-configured, step-by-step modules. No local setup. Your partner opens a browser and within minutes they're deploying a model on Xeon 6 hardware.
>
> The takeaway: when a partner or customer says "can I see this?" — you log into RHDP, spin up a tile, and hand them a URL. Same-day demo, not a next-quarter engagement.

---

## SLIDE 23 — Resources
**[~30 sec]**

> Resource links are on the slide — bookmark the page. The two you'll use most: **RHDP** for demos and labs, and the **Intel Software Catalog** for optimized frameworks like OpenVINO and oneAPI. The rest — YouTube, Twitch, OKD, Partner Training — are there when you need to go deeper or share something with a partner.

---

## SLIDE 24 — Thank You
**[~1 min]**

> That's it from me. Let's recap what happened.
>
> You walked in knowing Intel silicon. You're walking out understanding the platform that runs on top of it, and you've seen the tools — the demo platform, the catalog, the labs — that let you put this in front of a partner or customer this week, not next quarter.
>
> Next up: the OpenShift AI tech day. That's where we put AI workloads on this platform and give you something to demo live. Same cluster, same Intel silicon, real models running real inference.
>
> Two resources on the slide — the OpenShift product page and the Intel technology enabling repo on GitHub. Both worth bookmarking.
>
> Questions? I'm here for as long as you need. And if something comes up later — a customer conversation, a sizing question, a "how does this work" moment — reach out. That's what the joint team is for.
>
> Thanks everyone.

---

## Pacing Summary

| Slides | Section | Time |
|--------|---------|------|
| 1 | Title & intro | ~1 min |
| 2-3 | Why we're here & agenda | ~3 min |
| 4-6 | What OpenShift is | ~8 min |
| 7-9 | Architecture deep dive | ~7 min |
| 10-13 | Installation & sizing | ~8 min |
| 14-15 | Intel + OpenShift & OpenShift AI | ~5 min |
| 16-17 | Partner motion & takeaways | ~5 min |
| 18 | Training sessions | ~2 min |
| 19-22 | Demo platform walkthrough | ~4 min |
| 23-24 | Resources & close | ~2 min |
| **Total** | | **~45 min** |

**If running short (under 35 min):** Expand Q&A after slide 14 (Intel + OpenShift) and add a live walkthrough of the RHDP portal during slides 20-22 if you have a browser available.

**Q&A windows:** Natural pause points after slide 8 (architecture), slide 14 (Intel + OpenShift), and slide 22 (demo platform). Consider asking "any questions before we move on?" at those transitions.
