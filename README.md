# Resilio

Resilio is an infrastructure monitoring and auto-recovery project designed to detect system health issues and respond automatically.

## Current Features

* CPU health monitoring
* Memory health monitoring
* Health status classification: `HEALTHY`, `WARNING`, `CRITICAL`

## Project Setup

```bash
git clone <repository-url>
cd resilio

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

## Run

```bash
python -m agent
```

> Resilio is currently under active development. More monitoring and auto-recovery features will be added incrementally.
