# Ansys Fluent Skills - Implementation Plan

## Overview

Create a skill for looking up Ansys Fluent documentation, optimized for **code agents** that need **function-level API references** rather than high-level tutorials.

### Key Insight

Web search provides high-level tutorials and workflows, but code agents need:
- **Function signatures** and parameters
- **TUI command syntax** and paths
- **Valid parameter values** and options
- **Code examples** with correct syntax

## Architecture: Hybrid Approach

```
┌─────────────────────────────────────────────────────────────────┐
│                     Code Agent Request                          │
│        "Set up battery cooling simulation in PyFluent"          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 1: Web Search                          │
│  - High-level workflow guidance                                 │
│  - Find correct terminology                                     │
│  - Discover which APIs/commands to use                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Layer 2: PyFluent Docs Fetch                    │
│  - fluent.docs.pyansys.com                                      │
│  - Function signatures, parameters                              │
│  - Code examples                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Layer 3: Ansys Help (TUI Reference)                │
│  - ansyshelp.ansys.com (via Playwright if needed)               │
│  - TUI command paths and syntax                                 │
│  - Parameter valid values                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Documentation Sources

| Source | URL | Content | Access |
|--------|-----|---------|--------|
| **PyFluent Docs** | fluent.docs.pyansys.com | Python API reference | WebFetch |
| **PyAnsys Docs** | docs.pyansys.com | Ecosystem overview | WebFetch |
| **Ansys Help** | ansyshelp.ansys.com | TUI commands, theory | WebSearch / Playwright |
| **GitHub PyFluent** | github.com/ansys/pyfluent | Source code, examples | WebFetch |

## What Code Agents Search For

### Category 1: PyFluent API (Python)

| Task | Search Query |
|------|-------------|
| Launch Fluent | `PyFluent launch_fluent parameters` |
| Read mesh | `PyFluent read mesh case file` |
| Enable models | `PyFluent solver.setup.models` |
| Set materials | `PyFluent materials fluid solid` |
| Boundary conditions | `PyFluent boundary_conditions inlet outlet` |
| Run solver | `PyFluent run_calculation iterations` |
| Post-process | `PyFluent results contour export` |

### Category 2: TUI Commands

| Task | Search Query |
|------|-------------|
| File operations | `Fluent TUI /file/read-case` |
| Model setup | `Fluent TUI /define/models` |
| Materials | `Fluent TUI /define/materials` |
| Boundary conditions | `Fluent TUI /define/boundary-conditions` |
| Solver controls | `Fluent TUI /solve/set` |
| Initialize | `Fluent TUI /solve/initialize` |
| Iterate | `Fluent TUI /solve/iterate` |

### Category 3: Specific Features

| Feature | Search Query |
|---------|-------------|
| Battery model | `Fluent MSMD battery model parameters` |
| Turbulence | `Fluent k-epsilon k-omega SST setup` |
| Multiphase | `Fluent VOF Eulerian mixture model` |
| Heat transfer | `Fluent CHT conjugate heat transfer` |
| UDF | `Fluent UDF DEFINE_PROFILE example` |

## Implementation Options

### Option A: Skill with WebSearch + WebFetch (Recommended)

Leverage existing tools without new CLI:

```markdown
# .claude/skills/fluent-doc/SKILL.md

## Fluent Documentation Lookup

When user needs Fluent/PyFluent help:

1. **High-level guidance**: Use WebSearch
   - Query: "{topic} Ansys Fluent tutorial"

2. **PyFluent API**: Use WebFetch on PyFluent docs
   - URL: https://fluent.docs.pyansys.com/version/stable/api/...

3. **TUI commands**: Use WebSearch with site filter
   - Query: "site:ansyshelp.ansys.com Fluent TUI {command}"

4. **Examples**: Use WebFetch on GitHub
   - URL: https://github.com/ansys/pyfluent/tree/main/examples
```

**Pros**: No new code, leverages existing tools
**Cons**: Less structured, requires knowing URL patterns

### Option B: Minimal CLI for Ansys Help (If Needed)

Only if Ansys Help requires authentication or complex JS:

```
ansys-fluent-skills/
├── src/fluent_doc/
│   ├── __init__.py
│   ├── cli.py          # Single command: tui-lookup
│   └── core.py         # Playwright for Ansys Help only
├── .claude/skills/fluent-doc/
│   └── SKILL.md
├── pyproject.toml
└── CLAUDE.md
```

**Pros**: Handles auth/JS issues
**Cons**: More maintenance

### Option C: Full CLI (Like comsol-skills)

Complete search/retrieve implementation:

```
fluent-search search "boundary conditions"
fluent-search retrieve <url>
```

**Pros**: Full control, consistent interface
**Cons**: Most effort, may duplicate WebSearch

## Recommended Approach: Option A + Minimal B

1. **Primary**: Use WebSearch + WebFetch (no code needed)
2. **Fallback**: Minimal Playwright CLI only if Ansys Help is inaccessible

## Project Structure (Minimal)

```
ansys-fluent-skills/
├── .claude/
│   └── skills/fluent-doc/
│       └── SKILL.md         # Main skill definition
├── md-files/
│   ├── implementation-plan.md
│   ├── user-story-battery-cooling.md
│   └── search-patterns.md   # Common search patterns
├── src/fluent_doc/          # Only if Playwright needed
│   ├── __init__.py
│   └── tui_lookup.py
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

## SKILL.md Design

```markdown
# Fluent Documentation Skill

## When to Use
- User asks about PyFluent API functions
- User needs TUI command syntax
- User wants to set up Fluent simulation via scripting

## Search Strategy

### Step 1: Identify Task Category
Map user request to category:
- Mesh/geometry → mesh operations
- Physics setup → models API
- Materials → materials API
- BCs → boundary_conditions API
- Solving → solution API
- Results → post-processing API

### Step 2: Choose Documentation Source

| Need | Source | Method |
|------|--------|--------|
| PyFluent function | fluent.docs.pyansys.com | WebFetch |
| TUI command | ansyshelp.ansys.com | WebSearch |
| Code example | github.com/ansys/pyfluent | WebFetch |
| Concept/theory | ansyshelp.ansys.com | WebSearch |

### Step 3: Construct Query

PyFluent API:
- "PyFluent {class}.{method}"
- "PyFluent solver.setup.{category}"

TUI Commands:
- "Fluent TUI /{menu}/{submenu}"
- "site:ansyshelp.ansys.com Fluent {command}"

### Common Patterns

| User Says | Search For |
|-----------|-----------|
| "read mesh" | `PyFluent file read_mesh` |
| "set velocity inlet" | `PyFluent boundary_conditions velocity_inlet` |
| "enable energy" | `PyFluent models energy enabled` |
| "k-epsilon" | `PyFluent viscous k_epsilon` |
| "run 100 iterations" | `PyFluent run_calculation iterate` |
```

## Next Steps

1. **Test WebSearch effectiveness** for PyFluent/TUI lookups
2. **Test WebFetch** on fluent.docs.pyansys.com
3. **Create SKILL.md** with search patterns
4. **Document common queries** in search-patterns.md
5. **Only if needed**: Implement Playwright fallback

## Success Criteria

- Code agent can find PyFluent function signatures
- Code agent can find TUI command syntax
- Code agent can find valid parameter values
- No authentication issues blocking access
