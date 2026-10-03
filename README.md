# Resilio

Resilio is an infrastructure monitoring and auto-recovery agent that continuously monitors system health, detects resource exhaustion and process-related failures, and performs verified, non-destructive recovery actions to maintain system stability.

## Features

- **System Telemetry**: Continuous collection of CPU, memory, root disk, network interface, and process metrics via `psutil`.
- **Tri-State Health Evaluation**: Classifies component states into `HEALTHY`, `WARNING`, or `CRITICAL` based on configurable thresholds.
- **Verified Recovery Dispatch**: Centralized `RecoveryManager` performs a recovery action, collects fresh health evidence through `RecoveryVerifier`, and applies the Phase 6 retry/cooldown policy per component.
- **Safe CPU Relief**: Identifies and terminates verified high-CPU candidate processes while excluding protected OS processes and the agent itself.
- **Memory Reclamation**: Executes Python runtime garbage collection with pre- and post-execution metric verification.
- **Defensive Process Recovery**: Safely terminates unresponsive or out-of-bounds target processes with PID validation and termination timeouts.
- **Guarded Disk & Network Recovery**: Non-destructive abstractions that avoid unauthorized cleanup or interface disruption by default, supporting pluggable cleanup and restart hooks.
- **Automated Test Suite**: 74 unit and integration tests covering collectors, health evaluation, and recovery workflows.

## Architecture

```text
                           ┌─────────────────────────────┐
                           │          Resilio            │
                           │     Monitoring Agent        │
                           └──────────────┬──────────────┘
                                          │
                                          ▼
                       ┌──────────────────────────────────────┐
                       │          System Collectors           │
                       │                                      │
                       │  CPU      Memory      Disk           │
                       │  Network  Process                    │
                       └──────────────────┬───────────────────┘
                                          │
                                          │ Raw system metrics
                                          ▼
                       ┌──────────────────────────────────────┐
                       │           Health Detection           │
                       │                                      │
                       │  CPU Health      Memory Health       │
                       │  Disk Health     Network Health      │
                       │  Process Health                      │
                       │                                      │
                       │  HEALTHY / WARNING / CRITICAL        │
                       └──────────────────┬───────────────────┘
                                          │
                                 ┌────────┴────────┐
                                 │                 │
                           HEALTHY/WARNING      CRITICAL
                                 │                 │
                                 ▼                 ▼
                           ┌────────────┐   ┌──────────────────┐
                           │  No        │   │ Recovery Manager │
                           │  Recovery  │   │                  │
                           │  Required  │   │ Routes recovery  │
                           └────────────┘   │ by component     │
                                            └────────┬─────────┘
                                                     │
                        ┌────────────────────────────┼──────────────────────────┐
                        │                            │                          │
                        ▼                            ▼                          ▼
               ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
               │ CPU Recovery    │        │ Memory Recovery │        │ Process Recovery│
               │                 │        │                 │        │                 │
               │ Safe candidate  │        │ Garbage         │        │ Safe candidate  │
               │ selection       │        │ collection      │        │ selection       │
               │ + verification  │        │ + verification  │        │ + verification  │
               └─────────────────┘        └─────────────────┘        └─────────────────┘
                        │                            │                          │
                        └────────────────────────────┼──────────────────────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ Disk / Network       │
                                          │ Recovery             │
                                          │                      │
                                          │ Safe recovery        │
                                          │ abstractions /       │
                                          │ coordination         │
                                          └──────────┬───────────┘
                                                     │
                                                     ▼
                                          ┌──────────────────────┐
                                          │ Recovery Result      │
                                          │                      │
                                          │ Recovered            │
                                          │ Failed               │
                                          │ Not Required         │
                                          │ Unavailable          │
                                          └──────────────────────┘
```

## Tech Stack

- **Language**: Python 3.10+
- **Telemetry & Process Control**: `psutil`
- **Configuration**: `python-dotenv`
- **Testing**: `pytest`

## Configuration

Runtime parameters are configured via environment variables in a `.env` file (see `.env.example`):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `MONITOR_INTERVAL` | `5` | Monitoring interval in seconds |
| `MAX_RECOVERY_ATTEMPTS` | `2` | Consecutive unverified outcomes allowed before a component enters cooldown |
| `RECOVERY_COOLDOWN_SECONDS` | `60` | Cooldown duration per component after its recovery-attempt budget is exhausted |
| `LOG_LEVEL` | `INFO` | Recovery log verbosity (`DEBUG`, `INFO`, `WARNING`, or `ERROR`) |
| `CPU_WARNING_THRESHOLD` | `80` | CPU warning threshold (%) |
| `CPU_CRITICAL_THRESHOLD` | `90` | CPU critical threshold (%) |
| `MEMORY_WARNING_THRESHOLD` | `70` | Memory warning threshold (%) |
| `MEMORY_CRITICAL_THRESHOLD` | `85` | Memory critical threshold (%) |
| `DISK_WARNING_THRESHOLD` | `80` | Disk warning threshold (%) |
| `DISK_CRITICAL_THRESHOLD` | `90` | Disk critical threshold (%) |
| `PROCESS_NAME` | `python.exe` | Target process executable name |
| `PROCESS_CPU_WARNING_THRESHOLD` | `80` | Process CPU warning threshold (%) |
| `PROCESS_CPU_CRITICAL_THRESHOLD` | `90` | Process CPU critical threshold (%) |
| `PROCESS_MEMORY_WARNING_THRESHOLD` | `70` | Process memory warning threshold (%) |
| `PROCESS_MEMORY_CRITICAL_THRESHOLD` | `85` | Process memory critical threshold (%) |
| `NETWORK_INTERFACE` | `Wi-Fi` | Target network interface identifier |

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/mitheshshettyy/Resilio.git
cd Resilio
```

Create and activate a virtual environment:

- **Windows**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\activate
  ```

- **Linux / macOS**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Configuration Setup

Create a `.env` file from the example template:

- **Windows**:
  ```powershell
  copy .env.example .env
  ```

- **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

Update the configuration values in `.env` as needed.

### Running Resilio

Start the monitoring agent:

```bash
python -m agent.main
```

To stop the agent, press `Ctrl+C`.

## Recovery Safety

Resilio incorporates defensive safeguards across all recovery mechanisms:

- **Self-Protection**: Compares candidate process IDs against `os.getpid()` to prevent terminating the agent itself.
- **Protected System Processes**: Never terminates critical operating system processes (including `system`, `services.exe`, `lsass.exe`, `csrss.exe`, `wininit.exe`, and `dwm.exe`).
- **Post-Action Verification**: Actions report `recovered` only if post-recovery measurements confirm a reduction in resource usage or verified process termination.
- **Fresh Policy Verification**: After an action, `RecoveryVerifier` reads current CPU, memory, disk, or network health. `HEALTHY` and `WARNING` are verified outcomes; `CRITICAL` is not verified. Process verification remains explicitly unsupported until it has a defined fresh-health contract.
- **Bounded Retries**: The existing Phase 6 policy allows two consecutive unverified results per component. The following request enters a configurable cooldown. A verified result resets that component's state; other components are unaffected.
- **Recovery Logs**: Standard Python logging records each request, action, verification result, failed outcome, and cooldown suppression. Configure `LOG_LEVEL` for runtime visibility.
- **Conservative Disk & Network Strategy**: Does not delete files or reset interfaces by default. These modules return `recovery_unavailable` unless an explicit, managed cleanup function or platform-specific restart action is provided.

## Testing

Run the test suite using `pytest`:

```bash
python -m pytest
```
