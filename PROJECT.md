# Project: ampy — Industrial Electrical Cable Sizing Engine

A modern, simple, robust, open-source industrial electrical sizing calculation engine strictly complying with the French standards **NF C 15-100** and practical calculation guide **UTE C 15-105**.

---

## Architecture

The project is structured as a modular Python library with an ergonomic Typer/Rich CLI and a rigorous 4-tier pytest test suite.

```
                    ┌─────────────────────────┐
                    │       User / CLI        │
                    │  (Typer, Rich, YAML)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Pydantic Schemas     │
                    │   (ampy.core.models)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      SizingEngine       │
                    │   (ampy.core.engine)    │
                    └──────┬───────────┬──────┘
                           │           │
       ┌───────────────────▼──┐     ┌──▼───────────────────┐
       │   Normative Tables   │     │  Pure Calculations   │
       │  (ampy.core.tables)  │     │ (ampy.core.formulas) │
       │ - I0 reference table │     │ - Ib (1P, 3P, DC)    │
       │ - k1, k2, k3 factors │     │ - dU (exact rho, X)  │
       │ - Standard In series │     │ - Thermal stress I²t │
       └──────────────────────┘     └──────────────────────┘
```

---

## Feature Inventory

Every feature identified during the Survey phase is mapped to a specific milestone:

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | `F01_IB_1P` | Design operating current $I_b$ for 1-phase 230V across kW, kVA, A with $\cos\varphi$ | M1 | ORIGINAL_REQUEST §R1 |
| 2 | `F02_IB_3P` | Design operating current $I_b$ for 3-phase 400V across kW, kVA, A with $\cos\varphi$ | M1 | ORIGINAL_REQUEST §R1 |
| 3 | `F03_HARMONICS` | Neutral & 3rd harmonic derating ($i_{h3}$ per Table E.52.1) | M1 | Normative Survey |
| 4 | `F04_VOLTAGE_DROP` | Exact $\Delta U$ ($V$ and $\%$) with $b=1, 2$, $\rho_1$ at operating temp, and $\lambda$ | M1 | ORIGINAL_REQUEST §R1 |
| 5 | `F05_THERMAL_STRESS` | Short-circuit adiabatic limit ($I^2 t \le k^2 S^2$, $S_{\min} = \sqrt{I^2 t}/k$) | M1 | ORIGINAL_REQUEST §R1 |
| 6 | `F06_PYDANTIC_SCHEMAS` | Strict Pydantic v2 domain schemas with validation and units | M1 | ORIGINAL_REQUEST §R2 |
| 7 | `F07_PACKAGING` | Modern `pyproject.toml` with `src/ampy` layout and dependencies | M1 | ORIGINAL_REQUEST §R2 |
| 8 | `F08_INSTALL_METHODS` | Reference installation methods (B, C, E, F) and standard code mapping | M2 | ORIGINAL_REQUEST §R1 |
| 9 | `F09_I0_TABLES` | Complete reference current $I_0$ tables (Cu/Al, PVC/XLPE, 2/3 loaded, B, C, E, F, 1.5-300 mm²) | M2 | ORIGINAL_REQUEST §R1 |
| 10 | `F10_K1_FACTORS` | Installation method correction factor $k_1$ | M2 | ORIGINAL_REQUEST §R1 |
| 11 | `F11_K2_FACTORS` | Multi-circuit grouping reduction factor $k_2$ (Table 52N touching/spaced) | M2 | ORIGINAL_REQUEST §R1 |
| 12 | `F12_K3_FACTORS` | Ambient temperature factor $k_3$ for PVC (70°C) and XLPE (90°C), 10°C to 60°C | M2 | ORIGINAL_REQUEST §R1 |
| 13 | `F13_IN_SERIES` | Standard circuit breaker rating series $I_n$ (1A to 630A) | M2 | Normative Survey |
| 14 | `F14_SIZING_ENGINE` | Multi-constraint iterative SizingEngine ($I_b \le I_n \le I_z$ and $\Delta U\% \le \Delta U_{\max}$) | M3 | ORIGINAL_REQUEST §R1 |
| 15 | `F15_SECTION_SELECTOR` | Automatic standard section selection (1.5 to 300 mm²) for Cu and Al | M3 | ORIGINAL_REQUEST §R1 |
| 16 | `F16_CONSTRAINTS_TAGGING` | Governing constraint identification (`Iz`, `dU`, `thermal_stress`) and design margins | M3 | Architecture Survey |
| 17 | `F17_PUBLIC_API` | Clean library export facade (`from ampy import SizingEngine, CircuitDefinition, SizingResult`) | M3 | ORIGINAL_REQUEST §R2 |
| 18 | `F18_CLI_FLAGS` | One-shot sizing via Typer CLI flags (`ampy size ...`) | M4 | ORIGINAL_REQUEST §R2 |
| 19 | `F19_CLI_CONFIG` | Sizing execution via YAML/JSON configuration files (`--config circuit.yaml`) | M4 | ORIGINAL_REQUEST §R2 |
| 20 | `F20_RICH_REPORTS` | Rich terminal formatting with summary panel, audit tables, and compliance badges | M4 | ORIGINAL_REQUEST §R2 |
| 21 | `F21_JSON_EXPORT` | Machine-readable JSON output flag (`--json`) | M4 | ORIGINAL_REQUEST §R2 |
| 22 | `F22_TEST_SUITE_T1_4` | Comprehensive 4-tier test suite (Unit, Boundaries, Pairwise Combinatorial, Benchmarks) | E2E / M5 | ORIGINAL_REQUEST §R3 |
| 23 | `F23_UTE_BENCHMARKS` | 5 canonical UTE C 15-105 worked benchmark scenarios with 100% test pass rate | E2E / M5 | ORIGINAL_REQUEST §R3 |
| 24 | `F24_ADVERSARIAL_TIER5` | Adversarial coverage hardening with stress testing and white-box verification | M5 Phase 2 | Project Pattern |

---

## Milestones

### Implementation Track

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | `foundation` | Packaging (`pyproject.toml`), Pydantic models (`models.py`), and pure formulas (`formulas.py`) | none | IN_PROGRESS |
| M2 | `tables` | Normative tables (`tables.py`): $I_0$, $k_1$, $k_2$, $k_3$, standard sections & $I_n$ ratings | M1 | PLANNED |
| M3 | `engine` | Multi-constraint `SizingEngine` (`engine.py`) and public API exports (`__init__.py`) | M1, M2 | PLANNED |
| M4 | `cli` | Typer CLI (`cli/main.py`), Rich formatter (`cli/formatters.py`), YAML/JSON loader | M1, M2, M3 | PLANNED |
| M5 | `final_validation` | Pass 100% E2E test suite (Phase 1) + Adversarial Coverage Hardening Tier 5 (Phase 2) | M4, TEST_READY.md | PLANNED |

### E2E Testing Track (Parallel)

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | `test_track` | Test harness infra, Tiers 1-4 test cases, UTE C 15-105 benchmarks -> `TEST_READY.md` | M1 (models/formulas contracts) | IN_PROGRESS |

---

## Interface Contracts

### 1. `ampy.core.models` ↔ `ampy.core.formulas`
- `formulas.calculate_ib(system: PhaseSystem, voltage_v: float, power_w: float | None = None, apparent_power_va: float | None = None, current_a: float | None = None, cos_phi: float = 1.0) -> float`
- `formulas.calculate_voltage_drop(system: PhaseSystem, length_m: float, section_mm2: float, ib_a: float, cos_phi: float, material: ConductorMaterial, operating_temp_c: float | None = None) -> VoltageDropResult`
- `formulas.calculate_thermal_stress_min_section(ik_a: float, time_s: float, material: ConductorMaterial, insulation: InsulationType) -> float`

### 2. `ampy.core.tables` ↔ `ampy.core.engine`
- `tables.get_reference_current_i0(material: ConductorMaterial, insulation: InsulationType, loaded_conductors: int, method: InstallationMethod, section_mm2: float) -> float`
- `tables.get_k1_installation_method(method: InstallationMethod) -> float`
- `tables.get_k2_grouping(circuits_count: int, touching: bool = True) -> float`
- `tables.get_k3_temperature(insulation: InsulationType, temp_c: float, in_ground: bool = False) -> float`
- `tables.get_next_standard_section(current_section_mm2: float, material: ConductorMaterial) -> float | None`
- `tables.get_standard_protection_rating(ib_a: float) -> float`

### 3. `ampy.core.engine` ↔ `ampy.cli` & External Libraries
- `engine.SizingEngine.size_circuit(definition: CircuitDefinition) -> SizingResult`
- `SizingResult.is_compliant: bool`
- `SizingResult.selected_section_mm2: float`
- `SizingResult.iz_a: float`
- `SizingResult.voltage_drop: VoltageDropResult`
- `SizingResult.limiting_constraint: LimitingConstraint`
- `SizingResult.intermediate_factors: IntermediateFactors`

---

## Code Layout

```
ampy/
├── pyproject.toml
├── README.md
├── src/
│   └── ampy/
│       ├── __init__.py
│       ├── py.typed
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py       # Pydantic v2 schemas
│       │   ├── formulas.py     # Pure mathematical formulas
│       │   ├── tables.py       # Normative tables and lookups
│       │   └── engine.py       # SizingEngine orchestrator
│       └── cli/
│           ├── __init__.py
│           ├── main.py         # Typer CLI application
│           └── formatters.py   # Rich tables and panels
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/                   # Tier 1: Unit & formula tests
    │   ├── test_formulas.py
    │   ├── test_tables.py
    │   └── test_models.py
    ├── boundary/               # Tier 2: Corner & edge cases
    │   └── test_boundaries.py
    ├── combinatorial/          # Tier 3: 32-case pairwise matrix
    │   └── test_matrix.py
    └── e2e/                    # Tier 4: UTE C 15-105 worked benchmarks & CLI
        ├── test_ute_benchmarks.py
        └── test_cli.py
```
