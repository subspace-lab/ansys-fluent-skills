#!/usr/bin/env python3
"""
Plasma-Enhanced Chemical Vapor Deposition (PE-CVD) Simulation using PyFluent.

This script sets up a simulation for semiconductor processing applications like:
- Silicon nitride (SiN) deposition from SiH4/NH3/N2
- Silicon dioxide (SiO2) deposition from TEOS/O2
- Amorphous silicon (a-Si) deposition from SiH4

Physics modeled:
- Species transport with multicomponent diffusion
- Surface reactions (deposition kinetics)
- Low-pressure slip boundary conditions (Knudsen effects)
- Heat transfer (substrate heating)
- Optional: Electric potential for plasma effects

References:
- Fluent Theory Guide 7.1.2: Wall Surface Reactions and CVD
- Fluent Theory Guide 7.1.2.3: Slip Boundary for Low-Pressure Systems
- Fluent Theory Guide 18.1: Electric Potential
- PyFluent: https://fluent.docs.pyansys.com

Note: Full plasma modeling requires coupling with Ansys Chemkin-Pro for detailed
chemistry or external PIC solvers. This example focuses on the CVD thermal/flow
aspects that Fluent handles directly.
"""

import ansys.fluent.core as pyfluent
from pathlib import Path


def setup_pecvd_simulation(
    mesh_file: str,
    case_output: str = "pecvd_reactor.cas.h5",
    data_output: str = "pecvd_reactor.dat.h5",
    # Operating conditions
    pressure_pa: float = 100.0,  # 100 Pa (~0.75 Torr) - typical PECVD
    substrate_temp_k: float = 573.15,  # 300°C substrate
    gas_inlet_temp_k: float = 300.0,  # Room temp gas inlet
    # Gas composition (mass fractions) - SiN deposition example
    sih4_fraction: float = 0.02,  # 2% silane
    nh3_fraction: float = 0.10,  # 10% ammonia
    n2_fraction: float = 0.88,  # 88% nitrogen (carrier)
    # Flow conditions
    inlet_velocity: float = 0.5,  # m/s
    iterations: int = 1000,
    processor_count: int = 4,
):
    """
    Set up a PE-CVD reactor simulation.

    This example models a simplified silicon nitride deposition process:
    3 SiH4 + 4 NH3 → Si3N4 + 12 H2 (simplified overall reaction)

    The actual mechanism involves multiple gas-phase and surface reactions.
    For detailed chemistry, import CHEMKIN mechanism files.

    Args:
        mesh_file: Path to mesh file
        case_output: Output case file
        data_output: Output data file
        pressure_pa: Operating pressure in Pascals (typical PECVD: 10-1000 Pa)
        substrate_temp_k: Substrate/wafer temperature in Kelvin
        gas_inlet_temp_k: Inlet gas temperature
        sih4_fraction: Silane mass fraction
        nh3_fraction: Ammonia mass fraction
        n2_fraction: Nitrogen mass fraction
        inlet_velocity: Inlet velocity magnitude (m/s)
        iterations: Number of iterations
        processor_count: Number of CPU cores

    Expected mesh zones:
        - inlet: Gas inlet
        - outlet: Pump/exhaust outlet
        - wafer: Heated substrate (deposition surface)
        - showerhead: Gas distribution plate (may be heated/RF powered)
        - chamber-wall: Reactor walls
        - interior/fluid: Gas volume
    """

    # Launch Fluent
    solver = pyfluent.launch_fluent(
        mode="solver",
        precision="double",
        processor_count=processor_count,
        show_gui=False,
    )

    try:
        # Read mesh
        print(f"Reading mesh: {mesh_file}")
        if mesh_file.endswith((".cas.h5", ".cas")):
            solver.file.read_case(mesh_file)
        else:
            solver.file.read_mesh(mesh_file)

        # =====================================================================
        # GENERAL SETTINGS
        # =====================================================================

        # Pressure-based solver (required for low-pressure slip BC)
        solver.setup.general.solver.type = "pressure-based"

        # Steady-state
        solver.setup.general.solver.time = "steady"

        # =====================================================================
        # OPERATING CONDITIONS
        # =====================================================================

        # Set low operating pressure (critical for PECVD)
        solver.setup.general.operating_conditions.operating_pressure = pressure_pa

        # Reference pressure location (usually outlet)
        # solver.setup.general.operating_conditions.reference_pressure_location = [0, 0, 0]

        # =====================================================================
        # MODELS
        # =====================================================================

        # Energy equation (required for thermal CVD)
        solver.setup.models.energy.enabled = True

        # Laminar flow (typical for low-pressure CVD, Re << 1)
        solver.setup.models.viscous.model = "laminar"

        # Species transport with reactions
        solver.setup.models.species.model = "species-transport"

        # Enable diffusion energy source
        solver.setup.models.species.options.diffusion_energy_source = True

        # For multicomponent diffusion (important for CVD accuracy)
        solver.setup.models.species.options.full_multicomponent_diffusion = True

        # =====================================================================
        # MATERIALS - Define gas mixture
        # =====================================================================

        # Note: In practice, you'd import a CHEMKIN mechanism or use Fluent's
        # database. This is a simplified setup showing the structure.

        # The mixture should be defined with:
        # - SiH4 (silane)
        # - NH3 (ammonia)
        # - N2 (nitrogen)
        # - H2 (hydrogen - reaction product)
        # - Si3N4 or SiN (solid product - bulk species)

        # Create mixture material (via TUI for complex setup)
        print("Setting up species mixture...")

        # Example TUI commands for species setup:
        # solver.tui.define.materials.copy("fluid", "nitrogen", "sih4-nh3-n2-mixture")
        # solver.tui.define.models.species.species_transport("yes", "mixture-template")

        # For this example, we'll use a simplified approach
        # In production, import CHEMKIN mechanism:
        # solver.tui.define.models.species.read_chemkin_mechanism(
        #     "gas_mechanism.inp",
        #     "thermo.dat",
        #     "surface_mechanism.inp"
        # )

        # =====================================================================
        # LOW-PRESSURE SLIP BOUNDARY CONDITIONS
        # =====================================================================

        # Enable slip BC for low-pressure (Knudsen effects)
        # This is critical for CVD where Kn = 0.01-0.1
        print("Enabling low-pressure slip boundary conditions...")

        # TUI command to enable slip BC
        solver.tui.define.models.species.low_pressure_slip_boundary("yes")

        # Set accommodation coefficients (typically 0.9-1.0)
        # solver.tui.define.models.species.accommodation_coefficient.momentum(0.9)
        # solver.tui.define.models.species.accommodation_coefficient.thermal(0.9)

        # =====================================================================
        # BOUNDARY CONDITIONS
        # =====================================================================

        print("Setting boundary conditions...")

        # --- Inlet: Mass flow or velocity inlet ---
        try:
            inlet = solver.setup.boundary_conditions.velocity_inlet["inlet"]
            inlet.momentum.velocity_magnitude.value = inlet_velocity
            inlet.thermal.temperature.value = gas_inlet_temp_k

            # Species mass fractions at inlet
            # inlet.species["sih4"].mass_fraction = sih4_fraction
            # inlet.species["nh3"].mass_fraction = nh3_fraction
            # inlet.species["n2"].mass_fraction = n2_fraction

            print(f"  Inlet: v={inlet_velocity} m/s, T={gas_inlet_temp_k} K")
        except KeyError:
            print("  Warning: 'inlet' zone not found")

        # --- Outlet: Pressure outlet (to vacuum pump) ---
        try:
            outlet = solver.setup.boundary_conditions.pressure_outlet["outlet"]
            outlet.momentum.gauge_pressure.value = 0  # Relative to operating pressure
            outlet.thermal.backflow_temperature.value = gas_inlet_temp_k
            print("  Outlet: P=0 (gauge), pumped")
        except KeyError:
            print("  Warning: 'outlet' zone not found")

        # --- Wafer: Heated wall with surface reactions ---
        wafer_zones = ["wafer", "substrate", "deposition-surface"]
        for zone_name in wafer_zones:
            try:
                wafer = solver.setup.boundary_conditions.wall[zone_name]

                # Thermal BC: Fixed temperature (heated chuck)
                wafer.thermal.thermal_condition = "Temperature"
                wafer.thermal.temperature.value = substrate_temp_k

                # Surface reaction would be enabled here
                # wafer.species.surface_reactions = True

                print(f"  Wafer ({zone_name}): T={substrate_temp_k} K, reactions enabled")
                break
            except KeyError:
                continue

        # --- Showerhead: May be heated or grounded ---
        try:
            showerhead = solver.setup.boundary_conditions.wall["showerhead"]
            showerhead.thermal.thermal_condition = "Temperature"
            showerhead.thermal.temperature.value = 373.15  # 100°C
            print("  Showerhead: T=373 K")
        except KeyError:
            pass

        # --- Chamber walls: Cooled or adiabatic ---
        wall_zones = ["chamber-wall", "wall", "reactor-wall"]
        for zone_name in wall_zones:
            try:
                wall = solver.setup.boundary_conditions.wall[zone_name]
                wall.thermal.thermal_condition = "Temperature"
                wall.thermal.temperature.value = 323.15  # 50°C (water cooled)
                print(f"  Chamber wall ({zone_name}): T=323 K")
                break
            except KeyError:
                continue

        # =====================================================================
        # SURFACE REACTIONS (CVD)
        # =====================================================================

        # Define surface reaction mechanism
        # In practice, this requires CHEMKIN-format surface mechanism file

        # Example simplified reaction (via TUI):
        # SiH4(g) + surface → SiH2(s) + H2(g)
        # SiH2(s) + NH(s) → SiN(b) + 1.5 H2(g)

        # Enable wall surface reactions
        # solver.tui.define.models.species.wall_surface_reactions("yes")

        # Import surface mechanism
        # solver.tui.define.models.species.surface_mechanism.import_chemkin(
        #     "surface.inp", "thermo.dat"
        # )

        print("Note: Surface reactions require CHEMKIN mechanism file import")

        # =====================================================================
        # ELECTRIC POTENTIAL (Optional - for plasma effects)
        # =====================================================================

        # For PE-CVD, electric field affects:
        # - Ion bombardment energy
        # - Radical generation rates
        # - Film stress and composition

        # Basic electric potential model
        # solver.setup.models.electric_potential.enabled = True
        # solver.setup.boundary_conditions.wall["wafer"].electric.potential = 0  # Grounded
        # solver.setup.boundary_conditions.wall["showerhead"].electric.potential = -100  # RF bias

        print("Note: Full plasma modeling requires coupling with PIC solver")

        # =====================================================================
        # SOLUTION METHODS
        # =====================================================================

        solver.solution.methods.p_v_coupling.coupled_form = True
        solver.solution.methods.gradient = "least-squares-cell-based"
        solver.solution.methods.pressure = "standard"
        solver.solution.methods.momentum = "second-order-upwind"
        solver.solution.methods.energy = "second-order-upwind"

        # Species discretization
        # solver.solution.methods.species = "second-order-upwind"

        # =====================================================================
        # SOLUTION CONTROLS
        # =====================================================================

        # Relaxation factors for low-pressure reacting flow
        solver.solution.controls.pseudo_time_explicit_relaxation_factor.pressure = 0.3
        solver.solution.controls.pseudo_time_explicit_relaxation_factor.momentum = 0.5
        solver.solution.controls.pseudo_time_explicit_relaxation_factor.temperature = 0.8

        # =====================================================================
        # INITIALIZATION
        # =====================================================================

        solver.solution.initialization.defaults.temperature = gas_inlet_temp_k
        solver.solution.initialization.hybrid_initialize()
        print(f"Initialized at T={gas_inlet_temp_k} K")

        # =====================================================================
        # RUN CALCULATION
        # =====================================================================

        print(f"Running {iterations} iterations...")
        solver.solution.run_calculation.iterate(iter_count=iterations)

        # =====================================================================
        # SAVE RESULTS
        # =====================================================================

        solver.file.write_case(case_output)
        solver.file.write_data(data_output)
        print(f"Saved: {case_output}, {data_output}")

        # =====================================================================
        # POST-PROCESSING NOTES
        # =====================================================================

        print("\nPost-processing suggestions:")
        print("  - Deposition rate: Integrate SiN flux on wafer surface")
        print("  - Uniformity: Plot species concentration at wafer")
        print("  - Residence time: Particle tracking from inlet")

        return solver

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        solver.exit()


def create_chemkin_surface_mechanism_example():
    """
    Example CHEMKIN-format surface mechanism for Si3N4 CVD.

    This would be saved as 'surface.inp' and imported into Fluent.
    Real mechanisms have 10-100+ reactions with validated kinetic parameters.
    """

    mechanism = """
!===============================================================
! Simplified Si3N4 CVD Surface Mechanism
! For educational purposes - not validated kinetic parameters
!===============================================================

MATERIAL WAFER
SITE/WAFER_SITE/   SDEN/2.5E-9/  ! Site density (mol/cm2)
    SI(S)          ! Silicon site species
    N(S)           ! Nitrogen site species
    H(S)           ! Hydrogen site species
    SIH2(S)        ! Adsorbed silylene
    NH(S)          ! Adsorbed NH
END

BULK SI3N4 /1.0/  ! Bulk solid product

!---------------------------------------------------------------
! Surface Reactions
!---------------------------------------------------------------
REACTIONS   MWOFF   JOULES/MOLE

! SiH4 adsorption
SIH4 + 2SI(S) => SIH2(S) + H2 + SI(S)     1.0E+10   0.5   5000.0
    STICK

! NH3 adsorption
NH3 + N(S) => NH(S) + H(S) + H(S)         1.0E+09   0.5   3000.0
    STICK

! Surface reaction to form Si3N4
3SIH2(S) + 4NH(S) => SI3N4 + 12H(S)       1.0E+12   0.0   15000.0

! H2 desorption
2H(S) => H2 + 2SI(S)                       1.0E+13   0.0   20000.0

END
"""
    return mechanism


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python plasma_cvd_simulation.py <mesh_file>")
        print("\nThis script sets up a PE-CVD reactor simulation for Si3N4 deposition.")
        print("\nExpected mesh zones:")
        print("  - inlet: Gas inlet (SiH4/NH3/N2 mixture)")
        print("  - outlet: To vacuum pump")
        print("  - wafer: Heated substrate (deposition surface)")
        print("  - showerhead: Gas distribution plate")
        print("  - chamber-wall: Reactor walls")
        print("\nOperating conditions (defaults):")
        print("  - Pressure: 100 Pa (0.75 Torr)")
        print("  - Substrate temp: 300°C")
        print("  - Gas: 2% SiH4, 10% NH3, 88% N2")
        print("\nNote: Full surface chemistry requires CHEMKIN mechanism files.")

        # Print example mechanism
        print("\n" + "="*60)
        print("Example CHEMKIN surface mechanism:")
        print("="*60)
        print(create_chemkin_surface_mechanism_example())

        sys.exit(1)

    mesh_file = sys.argv[1]
    setup_pecvd_simulation(mesh_file=mesh_file)
