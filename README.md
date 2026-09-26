# Resilio

Resilio is an infrastructure monitoring and auto-recovery system that continuously monitors a system's health, detects resource and process-related issues, and performs appropriate recovery actions when required.

It monitors system resources such as CPU, memory, disk, network, and processes, evaluates their health, and provides automated recovery capabilities for supported issues.

## Features

* CPU monitoring
* Memory monitoring
* Disk monitoring
* Network monitoring
* Process monitoring
* System health detection
* Configurable monitoring parameters
* Safe CPU recovery candidate selection
* Automated memory recovery
* Safe process recovery
* Conservative disk recovery coordination
* Network recovery coordination
* Safe process selection for recovery
* Automated testing

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
                       │  Process Health                      | 
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

## Getting Started

### Prerequisites

* Python 3.x
* Git

### Installation

Clone the repository:

```bash
git clone <repository-url>
cd resilio
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file using the provided example configuration:

```bash
copy .env.example .env
```

Update the configuration values as required.

### Run Resilio

Start the Resilio monitoring agent:

```bash
python -m agent.main
```

Resilio will begin monitoring the system and perform recovery actions when supported health conditions require them.

## Recovery safety

CPU and process recovery terminate only a selected process after excluding
Resilio itself and protected system process names. CPU recovery additionally
requires a process to meet the configured process CPU critical threshold and
verifies that total CPU usage falls after termination.

Disk and network recovery are coordinated through safe recovery abstractions.
Resilio does not delete files or reset network interfaces by default because it
does not own a cleanup location or a portable, permission-safe interface reset
operation. They report `recovery_unavailable` until a deployment provides an
explicit, managed cleanup or platform-specific interface action.

### Run Tests

To run the test suite:

```bash
python -m pytest
```
