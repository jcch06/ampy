# ampy — Software Architecture & Technical Specification

> **Electrical Sizing Calculation Engine conforming to NF C 15-100 & UTE C 15-105**  
> Modern, Simple, Robust Industrial Library & CLI Interface

---

## 1. Executive Architectural Overview

### 1.1 Mission & Design Philosophy
`ampy` is an open-source, modern, and mathematically rigorous electrical cable sizing calculation engine designed as an alternative to proprietary industrial tools such as Caneco BT. It strictly complies with the French electrical installation standard **NF C 15-100** (Part 5-52 / IEC 60364-5-52) and the practical calculation guide **UTE C 15-105**.

The architecture is built on five core principles:
1. **Mathematical Purity & Transparency**: Core electrical calculations (currents, voltage drops, thermal stresses) are pure functions with zero hidden state, no global variables, and deterministic outputs.
2. **Strict Normative Compliance**: Sizing rules, reference installation methods, correction factors ($k_1, k_2, k_3$), and reference current tables ($I_0$) reflect standard normative tables with zero hand-wavy heuristics.
3. **Pydantic v2 Type Safety & Validation**: All domain inputs and outputs are governed by strongly-typed Pydantic schemas providing rigorous validation, runtime coercion, and seamless JSON/YAML serialization.
4. **Dual Interface (CLI & Library)**: Fully functional as a standalone CLI tool (powered by Typer and Rich) for electrical engineers in the field, and as an importable, headless Python library for network graph modeling, web backends (FastAPI), or desktop applications.
5. **Decoupled Orchestration**: The sizing algorithm cleanly separates *parameter lookup*, *constraint evaluation*, *standard section selection*, and *presentation formatting*.

### 1.2 High-Level Architectural Flow

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACES                                  |
|   CLI Flags (Typer)  |  YAML / JSON Config  |  Python Library API  |  Web / API   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        ampy.core.models (Pydantic v2)                             |
|   - ElectricalLoad           - CableSpecs           - InstallationConditions      |
|   - ProtectionDevice         - CircuitDefinition    - SizingResult                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                               ampy.core.engine                                    |
|                             [ SizingEngine ]                                      |
|                                                                                   |
|  1. calculate_ib()                                                                |
|  2. select_standard_protection_in() (or validate provided In)                     |
|  3. lookup_derating_factors() (k1 * k2 * k3 * k_custom -> k_total)                |
|  4. determine required base current: I0_required = In / k_total                   |
|  5. iterate standard sections (1.5 -> 300 mm²):                                   |
|     - Check Iz >= In (ampacity constraint)                                        |
|     - Check dU% <= dU_max% (voltage drop constraint)                              |
|     - Check I²t <= k²S² (thermal stress constraint)                               |
|  6. compile SizingResult + IntermediateFactors + LimitingConstraint               |
+------------------------+----------------------------------+-----------------------+
                         |                                  |
                         v                                  v
+----------------------------------+      +-----------------------------------------+
|        ampy.core.formulas        |      |            ampy.core.tables             |
|  - calculate_ib()                |      |  - TABLE_52C_I0 (Ampacity matrix)       |
|  - calculate_voltage_drop()      |      |  - TABLE_K1_METHOD (Method factors)     |
|  - calculate_thermal_stress()    |      |  - TABLE_K2_GROUPING (Grouping factors) |
|  - calculate_sin_phi()           |      |  - TABLE_K3_TEMP (Ambient temp factors) |
|  - get_conductor_resistivity()   |      |  - STANDARD_SECTIONS_MM2                |
|  - get_linear_reactance()        |      |  - STANDARD_PROTECTION_RATINGS_A        |
+----------------------------------+      +-----------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                PRESENTATION / EXPORT                              |
|   - Rich Summary Panel & Calculation Cards                                        |
|   - Rich Detailed Intermediate Factors Table                                      |
|   - JSON / YAML machine output (model_dump_json)                                  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Python Modular Packaging & Project Structure

### 2.1 Directory Layout (Modern `src/` Layout)

The package strictly adheres to standard PEP 517/518/621 conventions using the `src/` layout. This prevents accidental imports of uninstalled in-tree packages and guarantees that tests run against the installed wheel or editable package.

```
ampy/
├── pyproject.toml                     # Modern declarative package metadata & build configuration
├── README.md                          # Project documentation and quickstart
├── LICENSE                            # Open-source license (MIT / Apache 2.0)
├── src/
│   └── ampy/
│       ├── __init__.py                # Clean public API facade
│       ├── py.typed                   # PEP 561 type marker file
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py              # Pydantic v2 schemas and validation models
│       │   ├── formulas.py            # Pure mathematical electrical equations
│       │   ├── tables.py              # Normative lookup matrices (NF C 15-100 / UTE C 15-105)
│       │   └── engine.py              # SizingEngine orchestrator & constraint solver
│       └── cli/
│           ├── __init__.py
│           ├── main.py                # Typer CLI commands, subcommands, and flags
│           ├── formatters.py          # Rich terminal rendering (tables, panels, colors)
│           └── parsers.py             # YAML and JSON configuration readers
└── tests/
    ├── __init__.py
    ├── conftest.py                    # Shared pytest fixtures and helper builders
    ├── tier1_formulas/                # Unit tests for pure mathematical functions
    │   ├── test_ib.py
    │   ├── test_voltage_drop.py
    │   ├── test_thermal_stress.py
    │   └── test_tables.py
    ├── tier2_boundaries/              # Edge cases, extreme values, and input validation
    │   ├── test_boundaries.py
    │   └── test_model_validation.py
    ├── tier3_combinations/            # Combinatorial matrix (methods x conductors x insulation)
    │   └── test_combinations.py
    └── tier4_benchmarks/              # Official UTE C 15-105 worked benchmark scenarios
        ├── test_ute_c15_105_motor.py
        ├── test_ute_c15_105_lighting.py
        └── test_ute_c15_105_distribution.py
```

### 2.2 `pyproject.toml` Specification

```toml
[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ampy"
version = "0.1.0"
description = "Industrial electrical cable sizing calculation engine conforming to NF C 15-100 & UTE C 15-105"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }
authors = [
    { name = "Ampy Developers" }
]
keywords = ["electrical", "nf-c-15-100", "ute-c-15-105", "cable-sizing", "engineering", "caneco-alternative"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Manufacturing",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]

dependencies = [
    "pydantic>=2.7.0,<3.0.0",
    "typer[all]>=0.12.0",
    "rich>=13.7.0",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
    "mypy>=1.9.0",
]

[project.scripts]
ampy = "ampy.cli.main:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
ampy = ["py.typed"]

[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]

[tool.mypy]
strict = true
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py310"
```

---

## 3. Core Domain Models (`ampy.core.models`)

All models are built using **Pydantic v2** (`BaseModel`, `Field`, `@model_validator`, `@field_validator`), providing data validation, frozen immutability where appropriate, explicit units in descriptions, and JSON Schema generation.

### 3.1 Standard Enums

```python
from enum import Enum

class ConductorMaterial(str, Enum):
    CU = "Cu"  # Copper
    AL = "Al"  # Aluminium

class InsulationType(str, Enum):
    PVC = "PVC"    # Polyvinyl Chloride (max operating temp 70°C)
    XLPE = "XLPE"  # Cross-linked Polyethylene / PR (max operating temp 90°C)

class InstallationMethod(str, Enum):
    B = "B"  # Conduits / trunking on a wall or embedded in a building structure
    C = "C"  # Single-core or multi-core cables on a wooden or masonry wall, unperforated tray
    E = "E"  # Multi-core cables in free air or on perforated cable tray
    F = "F"  # Single-core cables in free air or on perforated cable tray

class PhaseSystem(int, Enum):
    SINGLE = 1  # Single-phase (Phase + Neutral or Phase-Phase), 230V standard
    THREE = 3   # Three-phase (3 Phases or 3 Phases + Neutral), 400V standard

class LimitingConstraint(str, Enum):
    IZ = "Iz"                      # Ampacity / thermal overload constraint
    DU = "dU"                      # Maximum allowable voltage drop constraint
    THERMAL_STRESS = "thermal_stress"  # Adiabatic short-circuit withstand constraint
```

### 3.2 Input Schemas

```python
from typing import Optional, Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict

class ElectricalLoad(BaseModel):
    """
    Electrical load specifications.
    User may specify active power (kW), apparent power (kVA), or direct design current (A).
    At least one must be provided.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    voltage_v: float = Field(
        ...,
        gt=0.0,
        description="Nominal system voltage in Volts (e.g. 230.0 for 1P, 400.0 for 3P)"
    )
    phases: PhaseSystem = Field(
        default=PhaseSystem.THREE,
        description="Phase arrangement: 1 for single-phase, 3 for three-phase"
    )
    cos_phi: float = Field(
        default=0.85,
        gt=0.0,
        le=1.0,
        description="Displacement power factor (cos phi)"
    )
    power_kw: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Active power in kilowatts (kW)"
    )
    apparent_power_kva: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Apparent power in kilovolt-amperes (kVA)"
    )
    current_a: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Direct design current in Amperes (A)"
    )
    frequency_hz: float = Field(
        default=50.0,
        gt=0.0,
        description="AC system frequency in Hertz (Hz)"
    )

    @model_validator(mode="after")
    def validate_load_input(self) -> "ElectricalLoad":
        provided = [x is not None for x in (self.power_kw, self.apparent_power_kva, self.current_a)]
        if not any(provided):
            raise ValueError("Must provide at least one of: power_kw, apparent_power_kva, or current_a.")
        if sum(provided) > 1:
            raise ValueError("Please provide ONLY ONE of: power_kw, apparent_power_kva, or current_a to avoid ambiguity.")
        return self


class CableSpecs(BaseModel):
    """
    Cable physical attributes and route length.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    length_m: float = Field(
        ...,
        gt=0.0,
        description="Cable circuit route length in meters (m)"
    )
    conductor: ConductorMaterial = Field(
        default=ConductorMaterial.CU,
        description="Conductor core material: Cu (Copper) or Al (Aluminium)"
    )
    insulation: InsulationType = Field(
        default=InsulationType.XLPE,
        description="Insulation material: PVC (70°C) or XLPE/PR (90°C)"
    )
    multicore: bool = Field(
        default=True,
        description="True for multi-conductor cable, False for single-core cables"
    )


class InstallationConditions(BaseModel):
    """
    Installation environment and normative derating parameters (NF C 15-100 Table 52C/E/H).
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    method: InstallationMethod = Field(
        default=InstallationMethod.C,
        description="Normative reference installation method letter (B, C, E, F)"
    )
    ambient_temp_c: float = Field(
        default=30.0,
        ge=0.0,
        le=80.0,
        description="Ambient temperature in °C (reference: 30°C in air, 20°C in ground)"
    )
    grouping_circuits: int = Field(
        default=1,
        ge=1,
        le=30,
        description="Number of circuits or multi-core cables grouped together (factor k2)"
    )
    in_ground: bool = Field(
        default=False,
        description="True if cable is buried directly or in ducts in ground (reference temp 20°C)"
    )
    k_custom: float = Field(
        default=1.0,
        gt=0.0,
        le=2.0,
        description="User-defined additional derating multiplier (e.g. solar radiation, harmonics)"
    )


class ProtectionDevice(BaseModel):
    """
    Upstream protective device settings and fault characteristics.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    in_a: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Nominal protection rating In (A). If None, ampy selects standard In >= Ib."
    )
    ik_a: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Prospective short-circuit current at cable head in Amperes (A) for thermal stress check"
    )
    disconnection_time_s: Optional[float] = Field(
        default=None,
        gt=0.0,
        le=10.0,
        description="Disconnection / tripping time of protection in seconds (s)"
    )


class CircuitDefinition(BaseModel):
    """
    Complete circuit specification combining load, cable, installation, and protection.
    Used as input for calculation engine and YAML/JSON configurations.
    """
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        default="Circuit_1",
        description="Unique identifier or descriptive tag for the circuit"
    )
    load: ElectricalLoad
    cable: CableSpecs
    installation: InstallationConditions = Field(default_factory=InstallationConditions)
    protection: ProtectionDevice = Field(default_factory=ProtectionDevice)
    du_max_percent: float = Field(
        default=5.0,
        gt=0.0,
        le=20.0,
        description="Maximum permissible relative voltage drop in percentage (%)"
    )
```

### 3.3 Output & Intermediate Schemas

```python
class IntermediateFactors(BaseModel):
    """
    Detailed audit trail of all intermediate coefficients and derating factors.
    """
    model_config = ConfigDict(frozen=True)

    k1_method: float = Field(description="Installation method factor k1")
    k2_grouping: float = Field(description="Multi-circuit grouping factor k2")
    k3_temperature: float = Field(description="Ambient temperature factor k3")
    k_custom: float = Field(description="Custom derating multiplier")
    k_total: float = Field(description="Total derating factor = k1 * k2 * k3 * k_custom")
    rho_ohm_mm2_m: float = Field(description="Conductor operating resistivity in Ω·mm²/m")
    reactance_ohm_m: float = Field(description="Linear reactance in Ω/m")
    sin_phi: float = Field(description="Reactive factor sin(phi) = sqrt(1 - cos²(phi))")


class VoltageDropResult(BaseModel):
    """
    Calculated voltage drop metrics.
    """
    model_config = ConfigDict(frozen=True)

    du_volts: float = Field(description="Absolute voltage drop in Volts (V)")
    du_percent: float = Field(description="Relative voltage drop in percentage (%)")
    du_max_percent: float = Field(description="Maximum allowable voltage drop limit (%)")
    is_compliant: bool = Field(description="True if du_percent <= du_max_percent")
    margin_percent: float = Field(description="Remaining margin: du_max_percent - du_percent")


class ThermalStressResult(BaseModel):
    """
    Short-circuit thermal stress withstand assessment (I²t <= k²S²).
    """
    model_config = ConfigDict(frozen=True)

    ik_a: float = Field(description="Prospective short circuit current (A)")
    time_s: float = Field(description="Disconnection duration (s)")
    i2t: float = Field(description="Thermal stress energy integral I²t (A²·s)")
    k_factor: float = Field(description="Adiabatic material constant k (A·s^(1/2)/mm²)")
    s_min_mm2: float = Field(description="Minimum cross-section required for thermal stress (mm²)")
    is_compliant: bool = Field(description="True if selected section >= s_min_mm2")


class SizingResult(BaseModel):
    """
    Comprehensive sizing calculation result containing selected section, ampacity,
    voltage drop, thermal stress, and normative audit trail.
    """
    model_config = ConfigDict(frozen=True)

    circuit_name: str
    ib_a: float = Field(description="Calculated design operating current Ib (A)")
    in_a: float = Field(description="Selected or validated protection rating In (A)")
    iz_min_required_a: float = Field(description="Minimum required admissible current Iz_min = In / k_total (A)")
    selected_section_mm2: float = Field(description="Selected standard conductor cross-section (mm²)")
    i0_reference_a: float = Field(description="Reference base current I0 from standard table for selected section (A)")
    iz_effective_a: float = Field(description="Effective permissible current Iz = I0 * k_total (A)")
    ampacity_compliant: bool = Field(description="True if Ib <= In <= Iz")
    voltage_drop: VoltageDropResult
    thermal_stress: Optional[ThermalStressResult] = None
    intermediate_factors: IntermediateFactors
    limiting_constraint: LimitingConstraint = Field(
        description="The governing condition that determined the final section: Iz, dU, or thermal_stress"
    )
    is_compliant: bool = Field(
        description="Overall compliance: True if ampacity, voltage drop, and thermal stress are all satisfied"
    )
    notes: list[str] = Field(default_factory=list, description="Normative annotations and engineering remarks")
```

---

## 4. Mathematical Calculation Core (`ampy.core.formulas`)

The mathematical core contains pure, functional implementations of formulas from **NF C 15-100** and **UTE C 15-105 §5.3**. All functions are deterministic and accompanied by type hints.

### 4.1 Operating Current $I_b$

```python
import math
from ampy.core.models import ElectricalLoad, PhaseSystem

def calculate_ib(load: ElectricalLoad) -> float:
    """
    Calculates design operating current Ib in Amperes (A) according to NF C 15-100.
    
    Formulas:
    - If direct current given: Ib = current_a
    - Single-phase (P): Ib = (P_kW * 1000) / (V * cos_phi)
    - Single-phase (S): Ib = (S_kVA * 1000) / V
    - Three-phase (P):  Ib = (P_kW * 1000) / (sqrt(3) * U * cos_phi)
    - Three-phase (S):  Ib = (S_kVA * 1000) / (sqrt(3) * U)
    """
    if load.current_a is not None:
        return round(load.current_a, 3)

    if load.phases == PhaseSystem.SINGLE:
        if load.power_kw is not None:
            ib = (load.power_kw * 1000.0) / (load.voltage_v * load.cos_phi)
        elif load.apparent_power_kva is not None:
            ib = (load.apparent_power_kva * 1000.0) / load.voltage_v
        else:
            raise ValueError("Load power not specified")
    elif load.phases == PhaseSystem.THREE:
        sqrt3 = math.sqrt(3.0)
        if load.power_kw is not None:
            ib = (load.power_kw * 1000.0) / (sqrt3 * load.voltage_v * load.cos_phi)
        elif load.apparent_power_kva is not None:
            ib = (load.apparent_power_kva * 1000.0) / (sqrt3 * load.voltage_v)
        else:
            raise ValueError("Load power not specified")
    else:
        raise ValueError(f"Unsupported phase system: {load.phases}")

    return round(ib, 3)
```

### 4.2 Power Factor Conversions

```python
def calculate_sin_phi(cos_phi: float) -> float:
    """
    Computes sin(phi) from cos(phi): sin_phi = sqrt(1 - cos_phi^2).
    Enforces clamped domain [0.0, 1.0].
    """
    if not (0.0 <= cos_phi <= 1.0):
        raise ValueError(f"cos_phi must be between 0.0 and 1.0, got {cos_phi}")
    return round(math.sqrt(max(0.0, 1.0 - (cos_phi ** 2))), 5)
```

### 4.3 Physical Conductor Parameters (Resistivity & Linear Reactance)

```python
from ampy.core.models import ConductorMaterial, InsulationType

def get_conductor_resistivity(conductor: ConductorMaterial, insulation: InsulationType) -> float:
    """
    Returns conductor resistivity rho1 in Ω·mm²/m at operating temperature
    as specified by UTE C 15-105 §5.3:
    - Normal operating temp: 70°C for PVC, 90°C for XLPE/PR
    - Standard conventional values:
      - Copper (Cu): 0.023 Ω·mm²/m (rho1 = 1.25 * rho0 = 1.25 * 0.01851 = 0.02314 -> standard 0.023)
      - Aluminium (Al): 0.036 Ω·mm²/m (rho1 = 1.25 * 0.0294 = 0.036)
    """
    if conductor == ConductorMaterial.CU:
        return 0.023
    elif conductor == ConductorMaterial.AL:
        return 0.036
    raise ValueError(f"Unknown conductor material: {conductor}")

def get_linear_reactance(section_mm2: float, multicore: bool = True) -> float:
    """
    Returns linear reactance lambda in Ω/m according to UTE C 15-105 §5.3:
    - For S <= 16 mm²: reactance is negligible -> lambda = 0.0 Ω/m
    - For S > 16 mm²: standard conventional value -> lambda = 0.08 mΩ/m = 0.00008 Ω/m
    """
    if section_mm2 <= 16.0:
        return 0.0
    return 0.00008
```

### 4.4 Voltage Drop Calculation ($dU$)

```python
from ampy.core.models import VoltageDropResult

def calculate_voltage_drop(
    ib_a: float,
    length_m: float,
    section_mm2: float,
    phases: PhaseSystem,
    cos_phi: float,
    conductor: ConductorMaterial,
    insulation: InsulationType,
    voltage_v: float,
    du_max_percent: float,
    multicore: bool = True,
) -> VoltageDropResult:
    """
    Calculates exact voltage drop dU in Volts and % according to UTE C 15-105 §5.3 / NF C 15-100:
    
    Formula:
      dU = b * [ rho1 * (L / S) * cos_phi + lambda * L * sin_phi ] * Ib
    
    Where:
      b = 2 for single-phase (Phase-Neutral or Phase-Phase)
      b = 1 for three-phase balanced
      rho1 = operating resistivity (Ω·mm²/m)
      L = route length (m)
      S = cross section (mm²)
      lambda = linear reactance (Ω/m)
      Ib = design operating current (A)
    
    Relative voltage drop:
      dU% = 100 * dU / voltage_v
    """
    b = 2.0 if phases == PhaseSystem.SINGLE else 1.0
    sin_phi = calculate_sin_phi(cos_phi)
    rho = get_conductor_resistivity(conductor, insulation)
    lambda_val = get_linear_reactance(section_mm2, multicore)

    resistance_term = (rho * length_m / section_mm2) * cos_phi
    reactance_term = (lambda_val * length_m) * sin_phi

    du_volts = b * (resistance_term + reactance_term) * ib_a
    du_percent = (du_volts / voltage_v) * 100.0
    is_compliant = du_percent <= du_max_percent

    return VoltageDropResult(
        du_volts=round(du_volts, 3),
        du_percent=round(du_percent, 3),
        du_max_percent=round(du_max_percent, 2),
        is_compliant=is_compliant,
        margin_percent=round(du_max_percent - du_percent, 3),
    )
```

### 4.5 Thermal Stress Limit (Adiabatic Short-Circuit Withstand)

```python
from ampy.core.models import ThermalStressResult

def calculate_thermal_stress(
    ik_a: float,
    disconnection_time_s: float,
    conductor: ConductorMaterial,
    insulation: InsulationType,
    selected_section_mm2: float,
) -> ThermalStressResult:
    """
    Verifies conductor thermal stress under short-circuit according to NF C 15-100 §434.5.2:
      I²t <= k² * S²  =>  S_min = sqrt(I²t) / k
    
    Factor k values:
      - Cu / PVC:  k = 115
      - Cu / XLPE: k = 143
      - Al / PVC:  k = 76
      - Al / XLPE: k = 94
    """
    k_factors = {
        (ConductorMaterial.CU, InsulationType.PVC): 115.0,
        (ConductorMaterial.CU, InsulationType.XLPE): 143.0,
        (ConductorMaterial.AL, InsulationType.PVC): 76.0,
        (ConductorMaterial.AL, InsulationType.XLPE): 94.0,
    }
    k = k_factors[(conductor, insulation)]
    i2t = (ik_a ** 2) * disconnection_time_s
    s_min = math.sqrt(i2t) / k

    return ThermalStressResult(
        ik_a=round(ik_a, 1),
        time_s=disconnection_time_s,
        i2t=round(i2t, 1),
        k_factor=k,
        s_min_mm2=round(s_min, 2),
        is_compliant=selected_section_mm2 >= s_min,
    )
```

### 4.6 Standard Protection Rating Selection

```python
from ampy.core.tables import STANDARD_PROTECTION_RATINGS_A

def select_standard_protection_in(ib_a: float) -> float:
    """
    Selects the smallest standard protection rating In >= Ib according to NF C 15-100.
    Standard series: [1, 2, 4, 6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]
    """
    for rating in STANDARD_PROTECTION_RATINGS_A:
        if rating >= ib_a:
            return float(rating)
    raise ValueError(f"Operating current Ib={ib_a}A exceeds maximum standard rating in series ({STANDARD_PROTECTION_RATINGS_A[-1]}A)")
```

---

## 5. Normative Lookup Tables & Enums (`ampy.core.tables`)

Normative tables are modeled with clean typing and immutable dictionary structures representing **NF C 15-100 Part 5-52** and **UTE C 15-105**.

### 5.1 Standard Section and Protection Series

```python
STANDARD_SECTIONS_MM2: list[float] = [
    1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0, 300.0
]

STANDARD_PROTECTION_RATINGS_A: list[int] = [
    1, 2, 4, 6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630
]
```

### 5.2 Table $I_0$ (Reference Admissible Current Matrix)

Table $I_0$ (NF C 15-100 Table 52C / UTE C 15-105 Table BJ) defines permissible base currents at reference conditions ($30^\circ\text{C}$ in air, isolated circuit $k=1.0$).
Lookup key tuple: `(method: InstallationMethod, conductor: ConductorMaterial, insulation: InsulationType, loaded_conductors: int)` $\to$ `dict[float, float]` (section $\to I_0$).

```python
from typing import Dict, Tuple
from ampy.core.models import InstallationMethod, ConductorMaterial, InsulationType

# Lookup Key: (Method, Conductor, Insulation, LoadedConductors)
TableKey = Tuple[InstallationMethod, ConductorMaterial, InsulationType, int]

TABLE_52C_I0: Dict[TableKey, Dict[float, float]] = {
    # Method C - Multi-core / Single-core on wall/tray (most common industrial baseline)
    # Cu / XLPE / 3 loaded conductors (Three-phase)
    (InstallationMethod.C, ConductorMaterial.CU, InsulationType.XLPE, 3): {
        1.5: 23.0, 2.5: 31.0, 4.0: 42.0, 6.0: 54.0, 10.0: 75.0, 16.0: 100.0,
        25.0: 127.0, 35.0: 158.0, 50.0: 192.0, 70.0: 246.0, 95.0: 298.0,
        120.0: 346.0, 150.0: 395.0, 185.0: 450.0, 240.0: 538.0, 300.0: 621.0
    },
    # Cu / XLPE / 2 loaded conductors (Single-phase)
    (InstallationMethod.C, ConductorMaterial.CU, InsulationType.XLPE, 2): {
        1.5: 26.0, 2.5: 36.0, 4.0: 49.0, 6.0: 63.0, 10.0: 86.0, 16.0: 115.0,
        25.0: 149.0, 35.0: 185.0, 50.0: 225.0, 70.0: 289.0, 95.0: 352.0,
        120.0: 410.0, 150.0: 473.0, 185.0: 542.0, 240.0: 641.0, 300.0: 741.0
    },
    # Cu / PVC / 3 loaded conductors (Three-phase)
    (InstallationMethod.C, ConductorMaterial.CU, InsulationType.PVC, 3): {
        1.5: 17.5, 2.5: 24.0, 4.0: 32.0, 6.0: 41.0, 10.0: 57.0, 16.0: 76.0,
        25.0: 96.0, 35.0: 119.0, 50.0: 144.0, 70.0: 184.0, 95.0: 223.0,
        120.0: 259.0, 150.0: 299.0, 185.0: 341.0, 240.0: 403.0, 300.0: 464.0
    },
    # Cu / PVC / 2 loaded conductors (Single-phase)
    (InstallationMethod.C, ConductorMaterial.CU, InsulationType.PVC, 2): {
        1.5: 19.5, 2.5: 27.0, 4.0: 36.0, 6.0: 46.0, 10.0: 63.0, 16.0: 85.0,
        25.0: 112.0, 35.0: 138.0, 50.0: 168.0, 70.0: 213.0, 95.0: 258.0,
        120.0: 299.0, 150.0: 344.0, 185.0: 392.0, 240.0: 461.0, 300.0: 530.0
    },
    # Al / XLPE / 3 loaded conductors
    (InstallationMethod.C, ConductorMaterial.AL, InsulationType.XLPE, 3): {
        2.5: 24.0, 4.0: 32.0, 6.0: 42.0, 10.0: 58.0, 16.0: 77.0, 25.0: 97.0,
        35.0: 120.0, 50.0: 146.0, 70.0: 187.0, 95.0: 227.0, 120.0: 263.0,
        150.0: 304.0, 185.0: 351.0, 240.0: 422.0, 300.0: 491.0
    },
    # Method B, E, F definitions follow identical structured mapping
}
```

### 5.3 Correction Factors ($k_1, k_2, k_3$)

```python
# Table K1 - Reference installation method factor (UTE C 15-105 Table BD)
TABLE_K1_METHOD: dict[InstallationMethod, float] = {
    InstallationMethod.B: 0.90,  # Conduit in wall / trunking
    InstallationMethod.C: 1.00,  # Reference base: direct on wall or unperforated tray
    InstallationMethod.E: 1.00,  # Perforated cable tray / free air
    InstallationMethod.F: 1.00,  # Single-core in free air
}

# Table K2 - Multi-circuit grouping factor (NF C 15-100 Table 52E / UTE C 15-105 Table BE)
# Single layer on unperforated tray or touching in conduit
TABLE_K2_GROUPING: dict[int, float] = {
    1: 1.00,
    2: 0.80,
    3: 0.70,
    4: 0.65,
    5: 0.60,
    6: 0.57,
    7: 0.54,
    8: 0.52,
    9: 0.50,
    12: 0.45,
    16: 0.41,
    20: 0.38,
}

# Table K3 - Ambient temperature factor (NF C 15-100 Table 52H / UTE C 15-105 Table BF)
# Reference temp: 30°C in air
TABLE_K3_TEMP_AIR: dict[InsulationType, dict[int, float]] = {
    InsulationType.PVC: {
        10: 1.22, 15: 1.17, 20: 1.12, 25: 1.06, 30: 1.00,
        35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61, 60: 0.50
    },
    InsulationType.XLPE: {
        10: 1.15, 15: 1.12, 20: 1.08, 25: 1.04, 30: 1.00,
        35: 0.96, 40: 0.91, 45: 0.87, 50: 0.82, 55: 0.76, 60: 0.71
    }
}
```

---

## 6. Sizing Engine Orchestrator (`ampy.core.engine`)

The `SizingEngine` orchestrates calculations across formulas, tables, and constraints. It solves the simultaneous inequalities:
1. **Ampacity Constraint**: $I_b \le I_n \le I_z$ where $I_z = I_0(S) \times k_{\text{total}} \implies I_0(S) \ge \frac{I_n}{k_{\text{total}}}$.
2. **Voltage Drop Constraint**: $\Delta U\%(S) \le \Delta U_{\max}\%$.
3. **Thermal Stress Constraint**: $S \ge S_{\min,\text{thermal}} = \frac{\sqrt{I_k^2 \cdot t}}{k}$ (if $I_k$ and $t$ specified).

### 6.1 `SizingEngine` Class Implementation Blueprint

```python
from ampy.core.models import (
    CircuitDefinition,
    SizingResult,
    IntermediateFactors,
    VoltageDropResult,
    ThermalStressResult,
    LimitingConstraint,
    PhaseSystem,
)
from ampy.core.formulas import (
    calculate_ib,
    calculate_voltage_drop,
    calculate_thermal_stress,
    select_standard_protection_in,
    get_conductor_resistivity,
    get_linear_reactance,
    calculate_sin_phi,
)
from ampy.core.tables import (
    STANDARD_SECTIONS_MM2,
    TABLE_52C_I0,
    TABLE_K1_METHOD,
    TABLE_K2_GROUPING,
    TABLE_K3_TEMP_AIR,
)

class SizingEngine:
    """
    Main calculation engine for electrical cable sizing according to NF C 15-100 & UTE C 15-105.
    """

    def __init__(self) -> None:
        pass

    def resolve_derating_factors(self, circuit: CircuitDefinition) -> IntermediateFactors:
        inst = circuit.installation
        cable = circuit.cable

        # 1. k1 (Installation method)
        k1 = TABLE_K1_METHOD.get(inst.method, 1.00)

        # 2. k2 (Grouping)
        if inst.grouping_circuits in TABLE_K2_GROUPING:
            k2 = TABLE_K2_GROUPING[inst.grouping_circuits]
        else:
            # Nearest lower lookup or conservative bound
            applicable_keys = [k for k in TABLE_K2_GROUPING if k <= inst.grouping_circuits]
            k2 = TABLE_K2_GROUPING[max(applicable_keys)] if applicable_keys else 0.38

        # 3. k3 (Temperature)
        # Round ambient temp to nearest 5°C bracket between 10°C and 60°C
        temp_bracket = int(round(inst.ambient_temp_c / 5.0) * 5)
        temp_bracket = max(10, min(60, temp_bracket))
        k3 = TABLE_K3_TEMP_AIR[cable.insulation].get(temp_bracket, 1.00)

        # Total k
        k_total = round(k1 * k2 * k3 * inst.k_custom, 4)

        rho = get_conductor_resistivity(cable.conductor, cable.insulation)
        # Reactance placeholder based on arbitrary 25mm2 for reporting
        lambda_val = get_linear_reactance(25.0, cable.multicore)
        sin_phi = calculate_sin_phi(circuit.load.cos_phi)

        return IntermediateFactors(
            k1_method=k1,
            k2_grouping=k2,
            k3_temperature=k3,
            k_custom=inst.k_custom,
            k_total=k_total,
            rho_ohm_mm2_m=rho,
            reactance_ohm_m=lambda_val,
            sin_phi=sin_phi,
        )

    def size_circuit(self, circuit: CircuitDefinition) -> SizingResult:
        """
        Executes complete multi-constraint cable sizing loop.
        """
        # Step 1: Calculate Ib
        ib = calculate_ib(circuit.load)

        # Step 2: Resolve Protection In
        if circuit.protection.in_a is not None:
            in_rating = circuit.protection.in_a
            if in_rating < ib:
                raise ValueError(f"Specified In={in_rating}A is lower than operating current Ib={ib}A (NF C 15-100 violation)")
        else:
            in_rating = select_standard_protection_in(ib)

        # Step 3: Intermediate factors
        factors = self.resolve_derating_factors(circuit)
        k_total = factors.k_total

        # Step 4: Required admissible current
        iz_min_required = in_rating / k_total
        loaded_conductors = 2 if circuit.load.phases == PhaseSystem.SINGLE else 3

        # Step 5: Lookup table I0
        table_key = (
            circuit.installation.method,
            circuit.cable.conductor,
            circuit.cable.insulation,
            loaded_conductors,
        )
        if table_key not in TABLE_52C_I0:
            raise KeyError(f"No normative I0 table entry for combination: {table_key}")
        i0_table = TABLE_52C_I0[table_key]

        # Step 6: Find candidate section satisfying Iz (thermal ampacity)
        candidate_sections = [s for s in STANDARD_SECTIONS_MM2 if s in i0_table]
        selected_section_iz = None
        for s in candidate_sections:
            if i0_table[s] >= iz_min_required:
                selected_section_iz = s
                break

        if selected_section_iz is None:
            max_s = candidate_sections[-1]
            raise ValueError(
                f"Required Iz ({iz_min_required:.1f}A) exceeds maximum single cable capacity "
                f"for section {max_s}mm² ({i0_table[max_s] * k_total:.1f}A). Parallel conductors required."
            )

        # Step 7: Check Voltage Drop (dU) and increment section if necessary
        current_section = selected_section_iz
        governing_constraint = LimitingConstraint.IZ

        du_result = calculate_voltage_drop(
            ib_a=ib,
            length_m=circuit.cable.length_m,
            section_mm2=current_section,
            phases=circuit.load.phases,
            cos_phi=circuit.load.cos_phi,
            conductor=circuit.cable.conductor,
            insulation=circuit.cable.insulation,
            voltage_v=circuit.load.voltage_v,
            du_max_percent=circuit.du_max_percent,
            multicore=circuit.cable.multicore,
        )

        while not du_result.is_compliant:
            governing_constraint = LimitingConstraint.DU
            curr_idx = candidate_sections.index(current_section)
            if curr_idx + 1 >= len(candidate_sections):
                raise ValueError(
                    f"Voltage drop {du_result.du_percent:.2f}% exceeds limit {circuit.du_max_percent}% "
                    f"even at maximum section {current_section}mm²."
                )
            current_section = candidate_sections[curr_idx + 1]
            du_result = calculate_voltage_drop(
                ib_a=ib,
                length_m=circuit.cable.length_m,
                section_mm2=current_section,
                phases=circuit.load.phases,
                cos_phi=circuit.load.cos_phi,
                conductor=circuit.cable.conductor,
                insulation=circuit.cable.insulation,
                voltage_v=circuit.load.voltage_v,
                du_max_percent=circuit.du_max_percent,
                multicore=circuit.cable.multicore,
            )

        # Step 8: Check Thermal Stress (if Ik & t specified)
        thermal_result = None
        if circuit.protection.ik_a is not None and circuit.protection.disconnection_time_s is not None:
            thermal_result = calculate_thermal_stress(
                ik_a=circuit.protection.ik_a,
                disconnection_time_s=circuit.protection.disconnection_time_s,
                conductor=circuit.cable.conductor,
                insulation=circuit.cable.insulation,
                selected_section_mm2=current_section,
            )
            while not thermal_result.is_compliant:
                governing_constraint = LimitingConstraint.THERMAL_STRESS
                curr_idx = candidate_sections.index(current_section)
                if curr_idx + 1 >= len(candidate_sections):
                    raise ValueError(
                        f"Thermal stress requirement S_min={thermal_result.s_min_mm2}mm² "
                        f"exceeds maximum standard section {current_section}mm²."
                    )
                current_section = candidate_sections[curr_idx + 1]
                thermal_result = calculate_thermal_stress(
                    ik_a=circuit.protection.ik_a,
                    disconnection_time_s=circuit.protection.disconnection_time_s,
                    conductor=circuit.cable.conductor,
                    insulation=circuit.cable.insulation,
                    selected_section_mm2=current_section,
                )
                # Recalculate dU with the newly enlarged section
                du_result = calculate_voltage_drop(
                    ib_a=ib,
                    length_m=circuit.cable.length_m,
                    section_mm2=current_section,
                    phases=circuit.load.phases,
                    cos_phi=circuit.load.cos_phi,
                    conductor=circuit.cable.conductor,
                    insulation=circuit.cable.insulation,
                    voltage_v=circuit.load.voltage_v,
                    du_max_percent=circuit.du_max_percent,
                    multicore=circuit.cable.multicore,
                )

        # Step 9: Final effective permissible current Iz
        i0_selected = i0_table[current_section]
        iz_effective = round(i0_selected * k_total, 2)

        return SizingResult(
            circuit_name=circuit.name,
            ib_a=ib,
            in_a=in_rating,
            iz_min_required_a=round(iz_min_required, 2),
            selected_section_mm2=current_section,
            i0_reference_a=i0_selected,
            iz_effective_a=iz_effective,
            ampacity_compliant=ib <= in_rating <= iz_effective,
            voltage_drop=du_result,
            thermal_stress=thermal_result,
            intermediate_factors=factors,
            limiting_constraint=governing_constraint,
            is_compliant=True,
            notes=[
                f"Sizing governed by {governing_constraint.value} constraint.",
                f"Effective margin: Iz - In = {round(iz_effective - in_rating, 2)} A",
                f"Voltage drop margin: {du_result.margin_percent:.2f} %",
            ]
        )
```

---

## 7. CLI Ergonomics & Terminal User Experience (`ampy.cli`)

The CLI is built with **Typer** and **Rich** to deliver an intuitive, expressive command-line interface.

### 7.1 Command Modes & CLI Arguments

`ampy` supports two complementary execution modes:
1. **Direct Flags Mode**: Rapid sizing of a single circuit directly from terminal arguments.
2. **File Configuration Mode**: Batch or repeatable sizing from declarative YAML / JSON files.

#### Direct Flags Command Example:
```bash
ampy size \
  --power-kw 22.0 \
  --voltage 400.0 \
  --phases 3 \
  --cos-phi 0.85 \
  --length 60.0 \
  --method C \
  --insulation XLPE \
  --conductor Cu \
  --temp 35.0 \
  --grouping 2 \
  --du-max 5.0
```

#### File Input Command Example:
```bash
ampy size --config circuit.yaml
ampy size --config circuit.json --json  # Machine-readable output
```

### 7.2 Configuration File Schemas (YAML / JSON)

#### `circuit.yaml`
```yaml
name: "M1_Pump_Motor"
load:
  power_kw: 22.0
  voltage_v: 400.0
  phases: 3
  cos_phi: 0.85
cable:
  length_m: 60.0
  conductor: "Cu"
  insulation: "XLPE"
  multicore: true
installation:
  method: "C"
  ambient_temp_c: 35.0
  grouping_circuits: 2
protection:
  in_a: 50.0
  ik_a: 10000.0
  disconnection_time_s: 0.1
du_max_percent: 5.0
```

#### Batch File `circuits.yaml`
```yaml
circuits:
  - name: "Lighting_Floor1"
    load:
      power_kw: 3.5
      voltage_v: 230.0
      phases: 1
      cos_phi: 0.95
    cable:
      length_m: 45.0
      conductor: "Cu"
      insulation: "PVC"
    installation:
      method: "B"
      ambient_temp_c: 25.0
      grouping_circuits: 4
    du_max_percent: 3.0

  - name: "HVAC_Chiller"
    load:
      power_kw: 75.0
      voltage_v: 400.0
      phases: 3
      cos_phi: 0.82
    cable:
      length_m: 120.0
      conductor: "Al"
      insulation: "XLPE"
    installation:
      method: "E"
      ambient_temp_c: 40.0
      grouping_circuits: 1
    du_max_percent: 5.0
```

### 7.3 Rich Terminal Rendering (`ampy.cli.formatters`)

When executed, `ampy` renders an ANSI terminal presentation featuring:
- **Result Badge**: Prominent display of selected section (e.g. `35 mm² Cu/XLPE`) and overall compliance (`[green]✔ COMPLIANT[/green]`).
- **Circuit Summary Panel**: Key electrical parameters ($I_b$, $I_n$, $I_z$, margin).
- **Intermediate Factors Table**: Transparent listing of normative factors ($k_1, k_2, k_3, k_{\text{total}}, \rho, \lambda$).
- **Voltage Drop & Constraints Breakdown**: Voltage drop value, allowable limit, and the governing constraint.

#### Mockup of Rich Terminal Output:

```
╭──────────────────────────────── ampy v0.1.0 ────────────────────────────────╮
│ NF C 15-100 & UTE C 15-105 Electrical Cable Sizing Engine                  │
╰─────────────────────────────────────────────────────────────────────────────╯

  Circuit: M1_Pump_Motor
  Status:  [bold green]✔ COMPLIANT (NF C 15-100)[/bold green]
  Governed By: [bold cyan]Iz (Ampacity)[/bold cyan]

╭─────────────────────────── SIZING RECOMMENDATION ───────────────────────────╮
│                                                                             │
│   Recommended Conductor Section: [bold yellow]10.0 mm²[/bold yellow] Cu / XLPE                   │
│   Protection Rating (In):        [bold]50.0 A[/bold]                                    │
│   Effective Admissible Iz:       [bold green]57.6 A[/bold green] (Base I0 = 75.0 A)                  │
│   Calculated Operating Ib:       [bold]37.4 A[/bold]                                    │
│   Voltage Drop (dU):             [bold green]1.84 % (7.36 V)[/bold green] <= 5.0 % max                 │
│                                                                             │
╰─────────────────────────────────────────────────────────────────────────────╯

── Intermediate Normative Calculation Audit ───────────────────────────────────
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Factor / Parameter  ┃ Value    ┃ Standard Reference                         ┃
┣━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Method (k1)         ┃ 1.00     ┃ Table 52G (Method C - Unperforated tray)   ┃
┃ Grouping (k2)       ┃ 0.80     ┃ Table 52E (2 circuits touching)            ┃
┃ Temperature (k3)    ┃ 0.96     ┃ Table 52H (XLPE at 35°C ambient)           ┃
┃ Total Derating (k)  ┃ 0.768    ┃ k_total = k1 * k2 * k3                     ┃
┃ Required Iz_min     ┃ 65.1 A   ┃ In / k_total (50.0 / 0.768)                ┃
┃ Resistivity (rho1)  ┃ 0.023    ┃ UTE C 15-105 §5.3 (Cu at 90°C)             ┃
┃ Reactance (lambda)  ┃ 0.000    ┃ UTE C 15-105 §5.3 (negligible for <= 16mm²)┃
┃ cos phi / sin phi   ┃ 0.85 / 0.527                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 8. Extensibility & Library Integration

`ampy` is designed to be imported cleanly into broader software systems:
- Multi-tier distribution network graphs (switchboards, sub-distribution panels, busbars).
- FastAPI backend microservices.
- Interactive web dashboards (Streamlit, Dash) or desktop applications (PyQt).

### 8.1 Clean Public API Surface (`ampy/__init__.py`)

```python
"""
ampy: French Standard NF C 15-100 & UTE C 15-105 Cable Sizing Calculation Engine.
"""

from ampy.core.engine import SizingEngine
from ampy.core.models import (
    ElectricalLoad,
    CableSpecs,
    InstallationConditions,
    ProtectionDevice,
    CircuitDefinition,
    SizingResult,
    VoltageDropResult,
    ThermalStressResult,
    IntermediateFactors,
    ConductorMaterial,
    InsulationType,
    InstallationMethod,
    PhaseSystem,
    LimitingConstraint,
)
from ampy.core.formulas import (
    calculate_ib,
    calculate_voltage_drop,
    calculate_thermal_stress,
    select_standard_protection_in,
)

__version__ = "0.1.0"

__all__ = [
    "SizingEngine",
    "ElectricalLoad",
    "CableSpecs",
    "InstallationConditions",
    "ProtectionDevice",
    "CircuitDefinition",
    "SizingResult",
    "VoltageDropResult",
    "ThermalStressResult",
    "IntermediateFactors",
    "ConductorMaterial",
    "InsulationType",
    "InstallationMethod",
    "PhaseSystem",
    "LimitingConstraint",
    "calculate_ib",
    "calculate_voltage_drop",
    "calculate_thermal_stress",
    "select_standard_protection_in",
]
```

### 8.2 Network Graph Integration Architecture

In complex commercial and industrial electrical distribution systems, circuits are arranged in a tree or Directed Acyclic Graph (DAG) starting from the Medium/Low Voltage transformer down to final branch circuits.

```
       [ Transformer MV/LV 630 kVA ]
                     |
           ( Feeder Cable F1 )
                     v
             [ Main LV Switchboard ]
            /                       \
  ( Sub-Feeder SF1 )        ( Sub-Feeder SF2 )
          v                         v
   [ Panelboard TD1 ]        [ Panelboard TD2 ]
     /             \                |
( Branch B1 )  ( Branch B2 )   ( Branch B3 )
    v              v                v
 [ Motor ]    [ Lighting ]      [ HVAC Chiller ]
```

#### Cumulative Voltage Drop Calculation along Graph Paths:
Because voltage drop is cumulative from the source to the final load:
$$\Delta U_{\text{total}} = \sum_{e \in \text{path}(\text{Source} \to \text{Load})} \Delta U_e\%$$
`ampy` models allow graph nodes/edges to be represented with native dataclasses or `networkx`:

```python
import networkx as nx
from ampy import SizingEngine, CircuitDefinition

class DistributionNetwork:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self.engine = SizingEngine()

    def add_circuit(self, source_bus: str, target_bus: str, circuit: CircuitDefinition) -> None:
        result = self.engine.size_circuit(circuit)
        self.graph.add_edge(source_bus, target_bus, circuit=circuit, result=result)

    def calculate_total_voltage_drop(self, root_bus: str, target_bus: str) -> float:
        """Computes cumulative dU% from root bus down to destination load."""
        path = nx.shortest_path(self.graph, source=root_bus, target=target_bus)
        total_du = 0.0
        for u, v in zip(path[:-1], path[1:]):
            edge_data = self.graph[u][v]
            total_du += edge_data["result"].voltage_drop.du_percent
        return round(total_du, 3)
```

### 8.3 FastAPI Microservice Integration Blueprint

Because domain models are native Pydantic v2 classes, integrating `ampy` into a REST API requires zero translation glue code:

```python
from fastapi import FastAPI, HTTPException
from ampy import SizingEngine, CircuitDefinition, SizingResult

api = FastAPI(title="ampy Electrical Sizing API", version="0.1.0")
engine = SizingEngine()

@api.post("/api/v1/size", response_model=SizingResult)
def size_cable(circuit: CircuitDefinition) -> SizingResult:
    try:
        return engine.size_circuit(circuit)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
```

### 8.4 Pydantic Serialization & Round-Trip Fidelity

All models support standard Pydantic v2 export and import methods:
```python
# Convert to native Python dictionary
data_dict = result.model_dump()

# Export to JSON string with indentation
json_str = result.model_dump_json(indent=2)

# Export JSON Schema (for OpenAPI, web forms, or dynamic UI generation)
schema = CircuitDefinition.model_json_schema()

# Reconstruct from JSON or YAML
circuit_restored = CircuitDefinition.model_validate_json(json_str)
```

---

## 9. Implementation Roadmap & Quality Gates

| Milestone | Scope / Deliverables | Affected Modules | Verification |
|-----------|----------------------|------------------|--------------|
| **M1: Packaging & Models** | `pyproject.toml`, directory layout, `models.py`, `py.typed` | `ampy.core.models`, packaging | Pydantic validation tests, schema round-trip |
| **M2: Mathematical Core & Tables** | `formulas.py`, `tables.py` (NF C 15-100 tables) | `ampy.core.formulas`, `ampy.core.tables` | Tier 1 unit tests against theoretical manual calculations |
| **M3: Sizing Engine** | `engine.py` (Multi-constraint iterative solver) | `ampy.core.engine` | Tier 2 & 3 boundary and combinatorial tests |
| **M4: CLI & Formatters** | `cli/main.py`, `formatters.py`, `parsers.py` | `ampy.cli.*` | CLI execution tests (direct flags & YAML configs) |
| **M5: UTE C 15-105 Benchmarks** | Official worked examples (motor, distribution, lighting) | `tests/tier4_benchmarks/` | 100% test pass rate matching standard benchmarks |

---

## 10. Summary Assessment

The architecture proposed for `ampy` achieves:
1. **Mathematical correctness**: Direct alignment with NF C 15-100 Part 5-52 and UTE C 15-105 §5.3.
2. **Industrial maintainability**: Pure calculation functions separated from normative lookup data and iterative orchestration.
3. **Developer ergonomics**: Strongly-typed Pydantic v2 schemas, automated CLI parsing, and informative Rich terminal reporting.
4. **Future extensibility**: Headless library readiness for network graphs, web microservices, and interactive UI applications.
