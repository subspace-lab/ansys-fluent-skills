# Ansys Fluent Skills

Claude Code skill for looking up Ansys Fluent and PyFluent documentation.

## Overview

This skill helps code agents find function-level API documentation for automating Ansys Fluent simulations via Python (PyFluent) or TUI commands.

## Architecture

Uses WebSearch + WebFetch instead of browser automation:

```
┌─────────────────────────────────────────┐
│         Code Agent Request              │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│     WebSearch: Find relevant docs       │
│  - PyFluent API queries                 │
│  - site:ansyshelp.ansys.com for TUI     │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    WebFetch: Get detailed content       │
│  - fluent.docs.pyansys.com              │
│  - GitHub examples                      │
└─────────────────────────────────────────┘
```

## Documentation Sources

| Source | URL | Content |
|--------|-----|---------|
| PyFluent Docs | fluent.docs.pyansys.com | Python API reference |
| PyAnsys | docs.pyansys.com | Ecosystem overview |
| Ansys Help | ansyshelp.ansys.com | TUI commands, theory |
| GitHub | github.com/ansys/pyfluent | Examples |

## Project Structure

```
ansys-fluent-skills/
├── .claude/skills/fluent-doc/
│   └── SKILL.md           # Skill definition with search patterns
├── md-files/              # Documentation and planning
├── CLAUDE.md              # Quick reference
├── README.md
└── .gitignore
```

## Search Patterns

### PyFluent API
```
PyFluent {category} {feature}
PyFluent boundary_conditions velocity_inlet
PyFluent models energy enabled
PyFluent viscous k-omega sst
```

### TUI Commands
```
site:ansyshelp.ansys.com Fluent TUI {command}
site:ansyshelp.ansys.com Fluent /define/models/energy
site:ansyshelp.ansys.com Fluent Text Command List
```

## Key PyFluent Patterns

```python
import ansys.fluent.core as pyfluent

# Launch
solver = pyfluent.launch_fluent(mode="solver", processor_count=4)

# Read case
solver.file.read_case("case.cas.h5")

# Enable models
solver.setup.models.energy.enabled = True
solver.setup.models.viscous.model = "k-omega"

# Boundary conditions
inlet = solver.setup.boundary_conditions.velocity_inlet["inlet"]
inlet.momentum.velocity_magnitude.value = 1.0

# Run
solver.solution.initialization.hybrid_initialize()
solver.solution.run_calculation.iterate(iter_count=100)
```

## Requirements

- Claude Code with WebSearch and WebFetch tools
- No additional installation needed

## License

Apache 2.0
