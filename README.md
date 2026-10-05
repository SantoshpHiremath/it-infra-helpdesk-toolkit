# it-infra-helpdesk-toolkit

A tested IT support ticket-triage and infrastructure-health-monitoring
toolkit, deployed as a running Docker container. I built it to cover
three everyday IT-support jobs in a runnable system: handling and
prioritizing support requests, checking the health of on-site
infrastructure (GPU workstations, servers, network equipment), and
deploying a small service to infrastructure in a container.

## Scope

**There is no real Jira Service Desk, Slack, or company IT queue here.**
The project implements the triage and monitoring logic those tools sit
on top of: a ticket data model, an explicit, tested priority-triage rule
set, and infrastructure health checks, exposed over an HTTP API.

**Disk-usage and host-reachability checks are real** — they read the
actual filesystem and open actual TCP sockets, verified directly (see
Verification). **GPU-workstation telemetry is synthetic** — there is no
GPU hardware or `nvidia-smi` in my development sandbox, so
`SimulatedGpuWorkstationReading` is labeled as simulated input; the
threshold *logic* applied to it is real and tested.

**Network equipment:** The toolkit provides the software layer around network equipment (TCP reachability checks, network-outage ticket triage), and vendor-specific integrations for Ubiquiti, Cisco, Aruba or Mikrotik can plug into it.

**Docker build note.** My development sandbox has no access to Docker
Hub (`docker.io` returns 403), and its container build network path
doesn't share the host shell's CA trust store, so a normal `docker
build` that pulls `python:3.11-slim` and runs `pip install` from
pypi.org fails there — checked directly, not assumed. `Dockerfile` (in
the repo root) is the normal, portable version for a regular machine or
CI runner with standard internet access (see `.github/workflows/ci.yml`,
which builds and smoke-tests it on GitHub Actions).
`Dockerfile.sandbox-local` is the exact Dockerfile I built and ran in
the sandbox for the verification below: it uses a locally pre-cached
base image, with dependency wheels downloaded on the host (which has
network access) and vendored in, installed fully offline via `pip
install --no-index --find-links=wheels/`. It is kept as a record of what
was actually executed.

## What it does

- **`src/ticket.py`** — a `Ticket` dataclass: category (laptop,
  network, server, GPU workstation, account access, AI tooling,
  other), status, priority, affected-user count, blocking-work flag.
- **`src/triage.py`** — explicit priority-triage rules: a network/server
  outage affecting multiple people is always CRITICAL; a single person
  blocked on infrastructure is HIGH; account-access issues have a
  MEDIUM floor even if not explicitly marked blocking, since a
  locked-out account is usually time-sensitive regardless. A documented
  rule set, not an implicit habit.
- **`src/infra_monitor.py`** — disk-usage checks (`shutil.disk_usage`
  against the actual filesystem) and TCP reachability checks (a genuine
  `socket.create_connection` attempt), plus threshold-based evaluation
  of (synthetic) GPU-workstation telemetry.
- **`src/api.py`** — a small Flask API: `/healthz`, `/readyz`,
  `/infra/disk`, and full ticket CRUD (`POST /tickets`, `GET
  /tickets/<id>`, `GET /tickets`) — every created ticket is triaged
  automatically on creation.
- **`Dockerfile`** / **`docker-compose.yml`** — a container deployment
  that I built and ran (see Verification below).
- 41 tests across ticket modeling, triage rules, infrastructure
  monitoring (including a local TCP server spun up inside the test
  itself to verify reachability checking against something genuinely
  listening), and the full HTTP API, all passing.

## Verification

- `python -m pytest -v` — 41/41 tests passing.
- `docker build -f Dockerfile.sandbox-local -t it-infra-helpdesk-toolkit:test .`
  — an image build using the sandbox-local Dockerfile described above.
- `docker run -d -p 18000:8000 it-infra-helpdesk-toolkit:test` — a
  running container, exercised with `curl` requests: `/healthz`
  returned `{"status":"ok"}`, `/infra/disk` returned the container's
  actual disk usage (13.6% used), and `POST /tickets` with a multi-user
  network-outage payload was triaged to `CRITICAL` and was retrievable
  via `GET /tickets` afterward.
- `docker inspect` confirmed the container's own `HEALTHCHECK` reported
  `healthy` after its start period, using the same `/healthz` endpoint a
  monitoring or orchestration layer would poll.

## Running it

```bash
pip install -r requirements.txt
python -m pytest -v                 # run the full test suite
python -m flask --app src.api run --port 8000   # run locally
# or, containerized:
docker build -t it-infra-helpdesk-toolkit .
docker run -p 8000:8000 it-infra-helpdesk-toolkit
```
