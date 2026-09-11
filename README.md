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
* Automated memory recovery
* Process recovery
* Safe process selection for recovery
* Automated testing

## Architecture

```text
                 ┌─────────────────────┐
                 │   System Monitoring │
                 │                     │
                 │ CPU • Memory • Disk │
                 │ Network • Process   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │   Health Detection  │
                 │                     │
                 │ Evaluate system     │
                 │ health & conditions │
                 └──────────┬──────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
              Healthy              Critical
                 │                     │
                 ▼                     ▼
          ┌─────────────┐    ┌──────────────────┐
          │  No Action  │    │ Recovery Manager │
          └─────────────┘    └────────┬─────────┘
                                      │
                           ┌──────────┴──────────┐
                           │                     │
                           ▼                     ▼
                    ┌──────────────┐     ┌───────────────┐
                    │    Memory    │     │    Process    │
                    │   Recovery   │     │   Recovery    │
                    └──────────────┘     └───────────────┘
```

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

### Run Tests

To run the test suite:

```bash
python -m pytest
```
