# User Story: EV Battery Pack Cooling Simulation Setup via Scripting

## User Request
"Help me set up a simulation for EV battery pack cooling in Ansys Fluent using Python/PyFluent scripting."

## High-Level Task Breakdown

1. **Geometry/Mesh Setup** - Load or create battery pack geometry
2. **Enable Battery Model** - Activate MSMD battery module
3. **Material Properties** - Define thermal/electrical properties for cells, tabs, coolant
4. **Boundary Conditions** - Set inlet/outlet for coolant, thermal BCs on walls
5. **Solver Settings** - Configure transient/steady, convergence criteria
6. **Post-Processing** - Extract temperature distribution, heat generation

---

## What Web Search Provides (High-Level)

Web search returns **tutorials and conceptual overviews**:
- "Simulating Battery Pack Cooling System using Ansys Fluent — Lesson 3"
- "Battery Thermal Management System using Ansys Fluent"
- "Chapter 31: Simulating a Single Battery Cell Using the MSMD Battery Model"

**Problem**: These are workflow guides, not API references. A coding agent needs **function signatures, parameters, and syntax**.

---

## What Code Agents Actually Need (Function-Level)

### Layer 1: PyFluent API Functions

| Task | What Agent Needs to Search |
|------|---------------------------|
| Launch Fluent | `pyfluent.launch_fluent` function signature, parameters |
| Read mesh | `solver.file.read_mesh` or `tui.file.read_case` |
| Enable energy equation | `solver.setup.models.energy.enabled` |
| Enable battery model | `solver.setup.models.battery` or TUI equivalent |
| Set material properties | `solver.setup.materials.fluid` / `solid` API |
| Define boundary conditions | `solver.setup.boundary_conditions.velocity_inlet` |
| Initialize solution | `solver.solution.initialization` |
| Run calculation | `solver.solution.run_calculation` |
| Export results | `solver.results.graphics` / `solver.file.export` |

### Layer 2: TUI Commands (Text User Interface)

When PyFluent API is incomplete, agents need TUI commands:

```
/define/models/addon-module           # Enable battery module
/define/models/energy                 # Enable energy equation
/define/materials/change-create       # Define materials
/define/boundary-conditions/          # Set BCs
/solve/initialize/                    # Initialize
/solve/iterate                        # Run iterations
```

### Layer 3: Settings/Parameters

Specific parameter names and valid values:
- Battery model types: `ecm`, `ntgk`, `newman`
- Coupling methods: `cht`, `fmu-cht`, `rom-cht`
- Energy source options: `joule-heat`, `echem-heat`

---

## Search Queries Code Agents Need

### Generic Function Lookups (Reusable)

```
# PyFluent API
"PyFluent launch_fluent parameters"
"PyFluent solver.setup.models"
"PyFluent boundary_conditions velocity_inlet"
"PyFluent read_mesh file formats"
"PyFluent run_calculation iterations"

# TUI Commands
"Fluent TUI /define/models"
"Fluent TUI /define/boundary-conditions"
"Fluent TUI /solve/initialize"
"Fluent TUI journal file syntax"

# Settings API
"Fluent settings API materials"
"Fluent settings API solver controls"
```

### Domain-Specific (Battery)

```
# Only when user asks about battery specifically
"PyFluent battery model setup"
"Fluent TUI addon-module battery"
"Fluent MSMD model parameters"
```

---

## Proposed Skill Design

### Primary Approach: Web Search + PyAnsys Docs

1. **Web Search** for high-level guidance and finding correct terminology
2. **PyAnsys Documentation** (https://docs.pyansys.com/) for API reference
3. **Ansys Help** for TUI command reference and theory

### Search Strategy for Code Agents

```
Step 1: Identify the task category
  - Mesh operations → search "PyFluent mesh"
  - Model setup → search "PyFluent models" or "Fluent TUI /define/models"
  - Materials → search "PyFluent materials"
  - Boundary conditions → search "PyFluent boundary_conditions"
  - Solver → search "PyFluent solution"
  - Post-processing → search "PyFluent results"

Step 2: Find function/command syntax
  - PyFluent: search "{function_name} parameters example"
  - TUI: search "Fluent TUI {command_path}"

Step 3: Find valid parameter values
  - search "Fluent {parameter_name} options values"
```

---

## Key Documentation Sources

| Source | Content Type | Access Method |
|--------|-------------|---------------|
| [PyFluent Docs](https://fluent.docs.pyansys.com/) | Python API reference | Web fetch |
| [PyAnsys Docs](https://docs.pyansys.com/) | PyAnsys ecosystem | Web fetch |
| [Ansys Help](https://ansyshelp.ansys.com/) | TUI commands, theory | Web search / Playwright |
| [Ansys Learning](https://innovationspace.ansys.com/) | Tutorials, workflows | Web search |

---

## Revised Skill Requirements

### Must Have
1. **PyFluent API lookup** - Function signatures, parameters, examples
2. **TUI command reference** - Command paths, syntax, valid inputs
3. **Settings/parameter lookup** - Valid values for enums, options

### Nice to Have
1. **Workflow guidance** - Step-by-step for common tasks
2. **Example code** - Working PyFluent scripts
3. **Error troubleshooting** - Common errors and fixes

### Out of Scope (Use Web Search)
1. Theory explanations (what is MSMD, what is CHT)
2. Best practices for specific domains (battery, turbomachinery)
3. Tutorial walkthroughs
