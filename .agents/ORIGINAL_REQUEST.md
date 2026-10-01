# Original User Request

## 2026-09-30T13:06:07Z

Use a full team of agents ("avec autant d'agent de nécéssaire"). Develop an open-source, modern, simple, and robust industrial electrical sizing calculation engine (an open-source alternative to Caneco BT), strictly complying with the French standards NF C 15-100 and practical calculation guide UTE C 15-105.

Working directory: c:\Users\cjose\antigravity project\ampy
Integrity mode: development

## Requirements

### R1. Normative Cable Sizing Engine (NF C 15-100 & UTE C 15-105)
Implement an automated electrical cable sizing engine in Python supporting:
- Calculation of design operating current Ib for single-phase (230V) and three-phase (400V) systems across active power (kW), apparent power (kVA), or direct current (A) inputs, factoring in power factor (cos phi).
- Application of standard correction factors from NF C 15-100 Part 5-52 / IEC 60364-5-52:
  - Reference installation methods (letters B, C, E, F; conduit, cable tray, embedded, free air).
  - k1: Installation method correction factor.
  - k2: Multi-cable grouping reduction factor.
  - k3: Ambient temperature correction factor (for PVC and XLPE / PR insulation).
- Calculation of effective permissible current Iz = I0 * prod(ki) and verification of standard protection coordination condition (Ib <= In <= Iz).
- Automatic selection of standard cross-sections (1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300 mm²) for Copper and Aluminium conductors.
- Calculation of exact relative voltage drop (dU in V and %) accounting for conductor resistivity rho (at operating temperature) and linear reactance lambda, ensuring dU <= dU_max.
- Calculation of thermal stress limit for conductors (I²t <= k²S²).

### R2. CLI and Modularity
- Provide an intuitive and clean Command Line Interface (CLI) in Python using Typer/Rich and Pydantic schemas.
- Allow running one-shot sizing calculations via command-line flags or by supplying a YAML/JSON configuration file.
- Format results into clear, readable terminal reports showing all intermediate factors (k1, k2, k3, Iz, dU, selected section and protection rating).
- Package the core calculation logic cleanly into a reusable Python library so it can be imported by future network graph and UI modules.

### R3. Automated Test Suite & Normative Reference Benchmark
- Implement a comprehensive test suite (pytest) verifying mathematical formulas and normative table lookups.
- Include automated benchmark test cases directly sourced from official UTE C 15-105 worked examples (e.g. standard motor circuits, distribution cables, temperature and grouping derating).

## Acceptance Criteria

### Normative Sizing Correctness
- [ ] Operating current Ib, derating factor products prod(k), and admissible current Iz match standard tables and formula derivations without discrepancies.
- [ ] Voltage drop calculations (dU) accurately distinguish between single-phase (b=2) and three-phase (b=1) distribution and match theoretical values within 0.5% tolerance.
- [ ] Benchmark test suite reproduces UTE C 15-105 test scenarios with 100% test pass rate.

### Software Quality & CLI Usability
- [ ] Running pytest in the working directory passes all unit and integration tests.
- [ ] CLI command executes successfully on sample cable inputs (both direct parameters and JSON/YAML file input) and displays a detailed summary table.
- [ ] Code is organized cleanly with type annotations, Pydantic data validation, and modular structure.
