#!/usr/bin/env python3
"""
Baking Oven Temperature Distribution Simulation using PyFluent.

This script sets up a CFD simulation for analyzing temperature distribution
in a baking oven, including:
- Natural convection (buoyancy-driven flow)
- Radiation heat transfer (S2S model for enclosure)
- Conduction through solid walls

Physics:
- Energy equation for heat transfer
- Laminar or k-epsilon turbulence (depending on Rayleigh number)
- S2S radiation model for surface-to-surface radiation in enclosure
- Boussinesq approximation for natural convection

References:
- Fluent Theory Guide 5.2.1: Heat Transfer Theory (Energy Equation)
- Fluent Theory Guide 5.3.7: Surface-to-Surface (S2S) Radiation Model
- PyFluent docs: https://fluent.docs.pyansys.com
"""

import ansys.fluent.core as pyfluent
from pathlib import Path


def setup_baking_oven_simulation(
    mesh_file: str,
    case_output: str = "baking_oven.cas.h5",
    data_output: str = "baking_oven.dat.h5",
    heater_temp: float = 473.15,  # 200°C in Kelvin
    ambient_temp: float = 298.15,  # 25°C in Kelvin
    wall_emissivity: float = 0.9,
    iterations: int = 500,
    processor_count: int = 4,
):
    """
    Set up and run a baking oven temperature distribution simulation.

    Args:
        mesh_file: Path to mesh file (.msh or .cas.h5)
        case_output: Output case file path
        data_output: Output data file path
        heater_temp: Heater surface temperature in Kelvin (default: 473.15 K = 200°C)
        ambient_temp: Initial/ambient temperature in Kelvin (default: 298.15 K = 25°C)
        wall_emissivity: Emissivity of oven walls for radiation (default: 0.9)
        iterations: Number of solver iterations
        processor_count: Number of CPU cores for parallel solving

    Expected mesh zones:
        - heater-top, heater-bottom: Heating element surfaces
        - wall-* : Oven walls (insulated or with heat loss)
        - interior: Air cavity inside oven
        - food (optional): Solid zone for food item
    """

    # Launch Fluent in solver mode
    solver = pyfluent.launch_fluent(
        mode="solver",
        precision="double",
        processor_count=processor_count,
        show_gui=False,
    )

    try:
        # Read mesh
        print(f"Reading mesh: {mesh_file}")
        if mesh_file.endswith(".cas.h5") or mesh_file.endswith(".cas"):
            solver.file.read_case(mesh_file)
        else:
            solver.file.read_mesh(mesh_file)

        # =====================================================================
        # GENERAL SETTINGS
        # =====================================================================
        # Enable gravity for natural convection (negative y-direction)
        solver.setup.general.gravity.enabled = True
        solver.setup.general.gravity.y_component = -9.81

        # =====================================================================
        # MODELS
        # =====================================================================

        # Enable energy equation (required for heat transfer)
        # Ref: Fluent Theory Guide 5.2.1 - Energy Equation
        solver.setup.models.energy.enabled = True

        # Viscous model - Laminar for low Rayleigh number natural convection
        # For Ra > 10^9, consider k-epsilon with enhanced wall treatment
        solver.setup.models.viscous.model = "laminar"

        # Alternative for turbulent natural convection:
        # solver.setup.models.viscous.model = "k-epsilon"
        # solver.setup.models.viscous.k_epsilon_model = "realizable"
        # solver.setup.models.viscous.near_wall_treatment = "enhanced-wall-treatment"

        # Enable S2S radiation model for enclosure radiation
        # Ref: Fluent Theory Guide 5.3.7 - S2S assumes gray-diffuse surfaces
        solver.setup.models.radiation.model = "s2s"

        # =====================================================================
        # MATERIALS
        # =====================================================================

        # Air properties with Boussinesq approximation for natural convection
        # Boussinesq: density varies linearly with temperature for buoyancy
        air = solver.setup.materials.fluid["air"]
        air.density.option = "boussinesq"
        air.density.boussinesq_temperature = ambient_temp
        air.thermal_expansion_coefficient = 0.00335  # 1/T for ideal gas at ~300K

        # Thermal conductivity and specific heat
        air.thermal_conductivity.value = 0.0262  # W/m-K at ~300K
        air.specific_heat.value = 1006.43  # J/kg-K

        # Viscosity
        air.viscosity.value = 1.7894e-5  # kg/m-s

        # =====================================================================
        # CELL ZONE CONDITIONS
        # =====================================================================

        # Set fluid zone (air inside oven)
        # Assumes zone named "interior" or "fluid"
        try:
            solver.setup.cell_zone_conditions.fluid["interior"].material = "air"
        except KeyError:
            # Try alternative zone name
            for zone_name in solver.setup.cell_zone_conditions.fluid.keys():
                solver.setup.cell_zone_conditions.fluid[zone_name].material = "air"
                print(f"Set fluid zone: {zone_name}")
                break

        # =====================================================================
        # BOUNDARY CONDITIONS
        # =====================================================================

        # --- Heater surfaces (constant temperature) ---
        heater_zones = ["heater-top", "heater-bottom", "heater"]
        for zone_name in heater_zones:
            try:
                wall = solver.setup.boundary_conditions.wall[zone_name]
                # Thermal BC: Fixed temperature
                wall.thermal.thermal_condition = "Temperature"
                wall.thermal.temperature.value = heater_temp
                # Radiation BC: Opaque wall with emissivity
                wall.radiation.emissivity = wall_emissivity
                print(f"Set heater BC: {zone_name} at {heater_temp} K")
            except KeyError:
                continue

        # --- Oven walls (insulated or with heat loss) ---
        # Option 1: Adiabatic (perfectly insulated)
        # Option 2: Convection to ambient (heat loss through walls)
        wall_zones = ["wall-top", "wall-bottom", "wall-left", "wall-right",
                      "wall-front", "wall-back", "wall"]
        for zone_name in wall_zones:
            try:
                wall = solver.setup.boundary_conditions.wall[zone_name]
                # Option 1: Adiabatic walls (no heat loss)
                wall.thermal.thermal_condition = "Heat Flux"
                wall.thermal.heat_flux.value = 0

                # Option 2: Convection heat loss (uncomment to use)
                # wall.thermal.thermal_condition = "Convection"
                # wall.thermal.heat_transfer_coeff = 10.0  # W/m2-K
                # wall.thermal.free_stream_temp = ambient_temp

                # Radiation properties
                wall.radiation.emissivity = wall_emissivity
                print(f"Set wall BC: {zone_name}")
            except KeyError:
                continue

        # --- Door (if present, may have different properties) ---
        try:
            door = solver.setup.boundary_conditions.wall["door"]
            door.thermal.thermal_condition = "Convection"
            door.thermal.heat_transfer_coeff = 5.0  # Lower insulation
            door.thermal.free_stream_temp = ambient_temp
            door.radiation.emissivity = 0.7  # Glass door lower emissivity
            print("Set door BC with convection heat loss")
        except KeyError:
            pass

        # =====================================================================
        # RADIATION SETTINGS (S2S specific)
        # =====================================================================

        # Compute view factors for S2S model
        # This is required for S2S radiation to work
        print("Computing view factors for S2S radiation...")
        solver.tui.define.models.radiation.s2s_parameters.compute_view_factors()

        # =====================================================================
        # SOLUTION METHODS
        # =====================================================================

        # Pressure-velocity coupling
        solver.solution.methods.p_v_coupling.coupled_form = True

        # Spatial discretization
        solver.solution.methods.gradient = "least-squares-cell-based"
        solver.solution.methods.pressure = "body-force-weighted"  # Better for natural convection
        solver.solution.methods.momentum = "second-order-upwind"
        solver.solution.methods.energy = "second-order-upwind"

        # =====================================================================
        # SOLUTION CONTROLS
        # =====================================================================

        # Under-relaxation factors for natural convection
        # May need adjustment for convergence
        solver.solution.controls.pseudo_time_explicit_relaxation_factor.pressure = 0.3
        solver.solution.controls.pseudo_time_explicit_relaxation_factor.momentum = 0.7
        solver.solution.controls.pseudo_time_explicit_relaxation_factor.temperature = 0.9

        # =====================================================================
        # INITIALIZATION
        # =====================================================================

        # Set reference values for natural convection scaling
        solver.setup.reference_values.temperature = ambient_temp

        # Initialize with ambient temperature
        solver.solution.initialization.defaults.temperature = ambient_temp
        solver.solution.initialization.hybrid_initialize()
        print(f"Initialized at ambient temperature: {ambient_temp} K")

        # =====================================================================
        # MONITORS
        # =====================================================================

        # Create temperature monitors at key locations
        # (Adjust coordinates based on your geometry)
        # solver.solution.monitor.surface_monitor.create(
        #     name="avg-temp-center",
        #     surface_names=["interior"],
        #     report_type="area-weighted-avg",
        #     field="temperature"
        # )

        # =====================================================================
        # RUN CALCULATION
        # =====================================================================

        print(f"Running {iterations} iterations...")
        solver.solution.run_calculation.iterate(iter_count=iterations)

        # Check convergence
        print("Checking residuals...")

        # =====================================================================
        # SAVE RESULTS
        # =====================================================================

        solver.file.write_case(case_output)
        solver.file.write_data(data_output)
        print(f"Saved case: {case_output}")
        print(f"Saved data: {data_output}")

        # =====================================================================
        # POST-PROCESSING (optional)
        # =====================================================================

        # Get temperature statistics
        # min_temp = solver.solution.report_definitions.surface.create(
        #     name="min-temp",
        #     surface_names=["interior"],
        #     report_type="minimum",
        #     field="temperature"
        # )

        print("Simulation complete!")
        return solver

    except Exception as e:
        print(f"Error during simulation: {e}")
        raise
    finally:
        # Close Fluent session
        solver.exit()


def create_simple_oven_mesh_commands():
    """
    Return TUI commands to create a simple box oven geometry in Fluent Meshing.

    This is a helper showing how to create a basic geometry.
    For production, use SpaceClaim or external CAD.
    """
    commands = """
    # Simple box oven: 0.5m x 0.4m x 0.3m (W x H x D)
    # Heater at top, food shelf at center

    # In Fluent Meshing or with mesher.tui:
    # 1. Create box geometry
    # 2. Name boundaries appropriately
    # 3. Generate mesh with boundary layers near walls

    # Example boundary naming:
    # - heater-top: Top heating element
    # - wall-bottom, wall-left, etc.: Oven walls
    # - interior: Fluid zone (air)
    """
    return commands


# =============================================================================
# ALTERNATIVE: TUI-based setup for more control
# =============================================================================

def setup_via_tui(solver, heater_temp: float, ambient_temp: float):
    """
    Alternative setup using TUI commands for finer control.

    Some settings may require TUI when settings API doesn't expose them.
    """
    # Enable energy
    solver.tui.define.models.energy("yes", "no", "no", "no", "no", "no", "no")

    # Enable S2S radiation
    solver.tui.define.models.radiation.s2s("yes")

    # Set operating conditions for buoyancy
    solver.tui.define.operating_conditions.gravity("yes", 0, -9.81, 0)
    solver.tui.define.operating_conditions.operating_temperature(ambient_temp)

    # Boussinesq for air
    solver.tui.define.materials.change_create(
        "air", "air", "yes", "boussinesq", ambient_temp, "no", "no", "no", "no", "no"
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python baking_oven_simulation.py <mesh_file>")
        print("\nExample:")
        print("  python baking_oven_simulation.py oven_mesh.msh")
        print("\nExpected mesh zones:")
        print("  - heater-top, heater-bottom: Heating surfaces")
        print("  - wall-*: Oven walls")
        print("  - interior: Air cavity")
        sys.exit(1)

    mesh_file = sys.argv[1]

    # Run simulation with default parameters
    setup_baking_oven_simulation(
        mesh_file=mesh_file,
        heater_temp=473.15,  # 200°C
        ambient_temp=298.15,  # 25°C
        iterations=500,
    )
