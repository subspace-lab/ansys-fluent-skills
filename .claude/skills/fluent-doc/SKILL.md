---
name: fluent-doc
description: Look up Ansys Fluent and PyFluent documentation for CFD simulation scripting. Use when user asks about PyFluent Python API, Fluent TUI commands, CFD physics/theory (turbulence, heat transfer, multiphase, radiation), or simulation setup. Includes CLI for fetching detailed content from Ansys Help.
---

# Fluent Documentation Lookup

## Strategy: WebSearch → URL → CLI Fetch

### Step 1: WebSearch for Discovery (Semantic Search)

WebSearch finds exact sections with semantic understanding:

```
# Find specific theory sections
WebSearch: "site:ansyshelp.ansys.com Fluent Theory Guide SST k-omega"
WebSearch: "site:ansyshelp.ansys.com Fluent surface reactions CVD"
WebSearch: "site:ansyshelp.ansys.com Fluent species transport equations"

# PyFluent API
WebSearch: "PyFluent boundary_conditions velocity_inlet"
WebSearch: "PyFluent models energy enabled"

# Check if Fluent supports a feature
WebSearch: "Ansys Fluent plasma simulation"  # Discovers: use CFX or Charge Plus
```

**Why WebSearch first**: Handles synonyms, partial matches, and tells you if a feature exists.

### Step 2: CLI Fetch Content (From URL)

After WebSearch returns a URL like:
`https://ansyshelp.ansys.com/.../corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html`

Extract the path and fetch:

```bash
# Fetch using URL path (most reliable)
uv run fluent-doc url "corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html" -o sst.txt
uv run fluent-doc url "corp/v252/en/flu_th/flu_th_cvd.html" -o cvd.txt

# Or browse TOC for section names
uv run fluent-doc toc --filter turbulence
uv run fluent-doc toc --guide user --filter boundary
```

### Quick Lookup (Skip WebSearch)

For well-known sections, use CLI directly:

```bash
uv run fluent-doc find "heat transfer" -o output.txt
uv run fluent-doc find "species transport" --guide user
```

## PyFluent Quick Reference

```python
import ansys.fluent.core as pyfluent

solver = pyfluent.launch_fluent(mode="solver", processor_count=4)
solver.file.read_case("case.cas.h5")

# Models
solver.setup.models.energy.enabled = True
solver.setup.models.viscous.model = "k-omega"
solver.setup.models.viscous.k_omega_model = "sst"

# Boundary conditions
inlet = solver.setup.boundary_conditions.velocity_inlet["inlet"]
inlet.momentum.velocity_magnitude.value = 1.0

# Solve
solver.solution.initialization.hybrid_initialize()
solver.solution.run_calculation.iterate(iter_count=500)
```

## Common URL Paths (v252)

| Topic | URL Path |
|-------|----------|
| SST k-ω | `corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html` |
| CVD/Surface Reactions | `corp/v252/en/flu_th/flu_th_cvd.html` |
| Species Transport | `corp/v252/en/flu_th/flu_th_sec_volumetric.html` |
| Heat Transfer | `corp/v252/en/flu_th/flu_th_sec_hxfer_theory.html` |
| Electric Potential | `corp/v252/en/flu_th/flu_th_sec_potential_theory.html` |

## What Fluent Does NOT Have

Use WebSearch to discover limitations:
- **Plasma discharge**: Use Ansys CFX or Ansys Charge Plus (PIC solver)
- **Detailed chemistry**: Couple with Ansys Chemkin-Pro
- **Electromagnetics**: Use Ansys Maxwell/HFSS
