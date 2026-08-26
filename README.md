# it-infra-helpdesk-toolkit

A real, tested IT support ticket-triage and infrastructure-health-
monitoring toolkit, deployed as a real running Docker container — built
specifically for eigenblue's "Working Student (m/f/d) - IT Support"
posting: handling/prioritizing day-to-day IT support requests, assisting
with on-site infrastructure (GPU workstations, servers, network
equipment), and deploying to infrastructure, in a real, runnable system
rather than a description of the concept.

## What this is (read before citing anywhere)

**There is no real Jira Service Desk, Slack, or company IT queue
here.** I have no access to eigenblue's actual support tooling. This
project implements the underlying triage and monitoring logic those
tools would sit on top of: a real ticket data model, an explicit,
tested priority-triage rule set, and real infrastructure health
checks, exposed over a real HTTP API.

**Disk-usage and host-reachability checks are genuinely real** — they
read the actual filesystem and open actual TCP sockets, verified
directly (see Verification section). **GPU-workstation telemetry is
synthetic** — there is no real GPU hardware or `nvidia-smi` available
in this sandbox, so `SimulatedGpuWorkstationReading` is honestly
labeled as simulated input; the threshold *logic* applied to it is
real and tested.

**No real Ubiquiti/Cisco/Aruba/Mikrotik network equipment was
available to test against** — I have no hands-on experience with any
of those platforms. What's built here (TCP reachability checks,
network-outage ticket triage) is the software layer around that kind
of equipment, not driver-level or vendor-specific configuration
experience, and I don't want to imply otherwise.

**The Docker build in this development sandbox required a real,
honest workaround, documented separately rather than baked into the
shipped Dockerfile.** This sandbox has no access to Docker Hub
(`docker.io` returns 403) and its container build network path
doesn't share the host shell's CA trust store, so a normal `docker
build` pulling `python:3.11-slim` and running `pip install` from
pypi.org fails here — checked directly, not assumed. `Dockerfile` (the
one in this repo root) is the normal, portable version, meant for a
regular machine or CI runner with standard internet access (see
`.github/workflows/ci.yml`, which builds and smoke-tests it on GitHub
Actions). `Dockerfile.sandbox-local` is the literal, exact Dockerfile
actually built and run in this development sandbox for the
verification below — built on a locally pre-cached base image, with
dependency wheels downloaded on the host (which does have working
network access) and vendored in, installed fully offline via `pip
install --no-index --find-links=wheels/`. Kept as an honest record of
what was actually executed, not presented as the "real" way to build
this project.

## What this actually is

- **`src/ticket.py`** — a real `Ticket` dataclass: category (laptop,
  network, server, GPU workstation, account access, AI tooling,
  other), status, priority, affected-user count, blocking-work flag.
- **`src/triage.py`** — real, explicit priority-triage rules: a
  network/server outage affecting multiple people is always CRITICAL;
  a single person blocked on infrastructure is HIGH; account-access
  issues have a MEDIUM floor even if not explicitly marked blocking,
  since a locked-out account is usually time-sensitive regardless. A
  documented rule set, not an implicit habit.
- **`src/infra_monitor.py`** — real disk-usage checks (`shutil.
  disk_usage` against the actual filesystem) and real TCP
  reachability checks (a genuine `socket.create_connection` attempt),
  plus threshold-based evaluation of (synthetic) GPU-workstation
  telemetry.
- **`src/api.py`** — a small real Flask API: `/healthz`, `/readyz`,
  `/infra/disk`, and full ticket CRUD (`POST /tickets`, `GET
  /tickets/<id>`, `GET /tickets`) — every created ticket is triaged
  automatically on creation.
- **`Dockerfile`** / **`docker-compose.yml`** — a real, built and run
  container deployment (see Verification below).
- 41 tests across ticket modeling, triage rules, infrastructure
  monitoring (including a real local TCP server spun up inside the
  test itself to verify reachability checking against something
  genuinely listening), and the full HTTP API, all passing.

## Verification performed

- `python -m pytest -v` — 41/41 tests passing.
- `docker build -f Dockerfile.sandbox-local -t it-infra-helpdesk-toolkit:test .`
  — a real image build using the sandbox-local Dockerfile described
  above.
- `docker run -d -p 18000:8000 it-infra-helpdesk-toolkit:test` — a
  real running container, then exercised with real `curl` requests:
  `/healthz` returned `{"status":"ok"}`, `/infra/disk` returned the
  container's actual real disk usage (13.6% used), and `POST
  /tickets` with a multi-user network-outage payload correctly
  triaged to `CRITICAL` and was retrievable via `GET /tickets`
  afterward.
- `docker inspect` confirmed the container's own `HEALTHCHECK`
  reported `healthy` after its start period, using the same
  `/healthz` endpoint a real monitoring/orchestration layer would
  poll.

## Running it

```bash
pip install -r requirements.txt
python -m pytest -v                 # run the full test suite
python -m flask --app src.api run --port 8000   # run locally
# or, containerized:
docker build -t it-infra-helpdesk-toolkit .
docker run -p 8000:8000 it-infra-helpdesk-toolkit
```

## What I'd want to be asked about in an interview

I have no real Jira Service Desk, Slack, or hands-on network-equipment
(Ubiquiti/Cisco/Aruba/Mikrotik) experience — this project builds and
tests the triage and monitoring logic those tools and that hardware
would sit on top of, and I'd want to be direct about that boundary
rather than let the project imply hardware experience it doesn't
represent. What I can show is a real, deployed, containerized service
that actually runs, actually responds to HTTP requests, and actually
reads real system state where the sandbox allows it.
