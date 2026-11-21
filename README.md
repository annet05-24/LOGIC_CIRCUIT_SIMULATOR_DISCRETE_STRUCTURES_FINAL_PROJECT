# Logic Circuit Simulator

A Python tool that turns a propositional logic expression into a working digital
logic circuit. Type an expression, see the circuit built from **AND, OR and NOT**
gates, flip the inputs, and watch the signals travel through the wires.

```
(A AND B) OR NOT C   ──►   parse   ──►   build gates & wires   ──►   draw & simulate
```

## Features

- Parse logical expressions into an Abstract Syntax Tree (AST)
- Validate syntax and report clear error messages
- Simplify expressions using Boolean algebra laws
- Generate complete truth tables
- Convert the expression into an AND/OR/NOT gate circuit with an automatic layout
- Propagate 0/1 signals through the circuit
- Interactive window: toggle inputs, see active wires highlighted, compare against the truth table

## Getting started

Requirements: **Python 3.9+** (Tkinter is included with Python; on Linux you may need
`sudo apt install python3-tk`).

```bash
git clone <repository-url>
cd logic-circuit-simulator
python main.py
```

Run the tests:

```bash
python -m unittest discover -s tests -v
```

> The project currently runs on **mock data** (`USE_MOCK = True` in
> `logic_sim/backend.py`) until the parser and circuit modules are finished.

## How it works

Three modules form a pipeline. Each one is owned by one team member.

| Module | Folder | Owner | Job |
|---|---|---|---|
| Parsing & Logic Engine | `logic_sim/parsing/` | Member 1 | text → AST, validation, simplification, truth table |
| Circuit Generation | `logic_sim/circuit/` | Member 2 | AST → gates/wires, layout, signal propagation |
| User Interface | `logic_sim/ui/` | Member 3 | input, drawing, highlighting, testing dashboard |

The UI talks to the engine only through `logic_sim/backend.py`.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design and
[docs/CONTRACTS.md](docs/CONTRACTS.md) for the exact data formats passed between modules.

## Project structure

```
logic-circuit-simulator/
├── main.py                  # start the app
├── logic_sim/
│   ├── backend.py           # facade: the only thing the UI imports
│   ├── mock_backend.py      # fake data used until the real modules exist
│   ├── parsing/             # Member 1
│   ├── circuit/             # Member 2
│   └── ui/                  # Member 3
├── tests/                   # integration tests (truth table vs circuit)
└── docs/                    # architecture, data contracts, task breakdown
```

## Team

| Member | Name | Responsibility |
|---|---|---|
| 1 | _Mercy_ | Parsing & Logic Engine |
| 2 | _Marinus_ | Circuit Generation & Graph Mapping |
| 3 | _Annet_ | User Interface & Interactive Testing |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Data contracts](docs/CONTRACTS.md)
- [Team tasks and milestones](docs/TEAM_TASKS.md)
- [Contributing guide](CONTRIBUTING.md)

## Status

- [ ] Parser and AST
- [ ] Truth table generator
- [ ] Gate mapping and layout
- [ ] Signal propagation
- [x] UI skeleton running on mock data
- [ ] Integration and end-to-end tests
