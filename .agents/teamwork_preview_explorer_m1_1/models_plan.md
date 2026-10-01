# Milestone 1 (M1) Implementation Blueprint: Packaging & Domain Models

**Target Files**:
- `pyproject.toml`
- `src/ampy/core/models.py`
- `src/ampy/py.typed`

**Author**: `teamwork_preview_explorer_m1_1`  
**Date**: 2026-09-30  
**Status**: APPROVED BLUEPRINT (Ready for Implementation)  
**Governing Standards**:
- **NF C 15-100** (Part 5-52: Wiring systems, permissible currents, voltage drop)
- **UTE C 15-105** (Practical calculation guide for conductor cross-sections and protective devices)
- **IEC 60364-5-52** (Electrical installations of buildings — Part 5-52)
- **IEC 60364-4-43** (Protection against overcurrent)

---

## 1. Executive Blueprint Summary

This document specifies the complete, authoritative implementation blueprint for the foundational components of Milestone 1 (M1) of `ampy`:
1. `pyproject.toml`: Modern PEP 517/518/621 declarative packaging configuration utilizing the standard `src/` layout, specifying dependencies (`pydantic>=2.0`, `typer>=0.12`, `rich>=13.0`, `pyyaml>=6.0`), development dependencies (`pytest>=8.0`, `pytest-cov>=4.0`), CLI console entry point (`ampy = ampy.cli.main:app`), and tooling configurations (`pytest`, `mypy`, `ruff`).
2. `src/ampy/core/models.py`: Strongly-typed **Pydantic v2** domain models, enums, field-level validators, cross-model thermal consistency checks, and serialization mechanisms strictly modeled after NF C 15-100 and UTE C 15-105.

### Key Architectural Guarantees
- **Type Safety & Strict Validation**: All schemas use Pydantic v2 with `extra="forbid"` to prevent erroneous or unrecognized parameters in YAML/CLI inputs.
- **Mutual Exclusivity Enforcement**: Load input allows specifying active power ($P$ in kW), apparent power ($S$ in kVA), or direct operating current ($I$ in A), strictly requiring exactly one of the three to prevent calculation ambiguities.
- **Bi-directional Tolerant Enum Coercion**: Enums feature class-level `_missing_` hooks enabling flexible string parsing from CLI arguments, YAML configs, and legacy survey conventions (e.g. `'1P'`, `'3P'`, `'single_phase'`, `'Iz'`, `'dU'`, etc.) without breaking strict canonical typing.
- **Normative Thermal Boundaries**: Model-level validation prevents defining circuits where ambient temperature reaches or exceeds conductor insulation limits (70°C for PVC, 90°C for XLPE).
- **Seamless Serialization**: Built-in support for `model_dump()`, `model_dump_json()`, and OpenAPI / JSON Schema generation via `model_json_schema()`.

---

## 2. Component 1: `pyproject.toml` Blueprint

### 2.1 Complete File Specification

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
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
keywords = [
    "electrical",
    "cable-sizing",
    "nf-c-15-100",
    "ute-c-15-105",
    "iec-60364",
    "caneco-alternative",
    "engineering"
]
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
    "pydantic>=2.0",
    "typer>=0.12",
    "rich>=13.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
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
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py310"
```

### 2.2 Rationale & Dependency Verification
- **Build System**: `setuptools>=68.0` is already present in the active Python 3.13.5 environment (setuptools 80.9.0 is installed). The `src` package discovery directive ensures clean separation of source code and test code.
- **Runtime Dependencies**:
  - `pydantic>=2.0`: Core validation and data modeling (verified active version: 2.11.7).
  - `typer>=0.12`: Modern, type-annotated CLI engine.
  - `rich>=13.0`: Terminal formatting, calculation summary panels, and audit tables.
  - `pyyaml>=6.0`: Declarative YAML circuit configuration loading.
- **Optional Dependencies (`[project.optional-dependencies] dev`)**:
  - `pytest>=8.0` and `pytest-cov>=4.0` for automated unit, boundary, combinatorial, and benchmark testing.
- **CLI Script**: Declares the `ampy` executable pointing directly to `ampy.cli.main:app`.
- **PEP 561 Type Marker**: `package-data` includes `py.typed` to signal downstream consumers that `ampy` is a fully typed library.

---

## 3. Component 2: `src/ampy/core/models.py` Blueprint

### 3.1 Standard Normative Enums

All enums inherit from `(str, Enum)` for direct JSON/YAML serialization, human-readable CLI representation, and immutable comparison.

#### 1. `PhaseSystem`
Represents the electrical system topology:
```python
class PhaseSystem(str, Enum):
    SINGLE_PHASE = "single_phase"
    THREE_PHASE = "three_phase"
    DC = "dc"
```
- **Values & Semantics**:
  - `SINGLE_PHASE` ("single_phase"): Single-phase AC distribution ($V_n = 230\text{ V}$ standard, $b = 2$ for voltage drop, 2 loaded conductors).
  - `THREE_PHASE` ("three_phase"): Three-phase AC distribution with or without neutral ($U_n = 400\text{ V}$ standard, $b = 1$ for voltage drop, 3 loaded conductors).
  - `DC` ("dc"): Two-wire Direct Current distribution ($b = 2$ for voltage drop, 2 loaded conductors).
- **Flexible Ingestion (`_missing_`)**:
  Coerces input strings and integers:
  - `1`, `'1'`, `'1P'`, `'single'`, `'single_phase'` $\to$ `PhaseSystem.SINGLE_PHASE`
  - `3`, `'3'`, `'3P'`, `'three'`, `'three_phase'` $\to$ `PhaseSystem.THREE_PHASE`
  - `'DC'`, `'dc'`, `'direct'` $\to$ `PhaseSystem.DC`

#### 2. `ConductorMaterial`
Conductor physical metal core according to NF C 15-100 Table 52C:
```python
class ConductorMaterial(str, Enum):
    CU = "Cu"
    AL = "Al"
```
- **Values & Semantics**:
  - `CU` ("Cu"): Pure Copper ($\rho_1 = 0.023\ \Omega\cdot\text{mm}^2/\text{m}$).
  - `AL` ("Al"): Pure Aluminium ($\rho_1 = 0.037\ \Omega\cdot\text{mm}^2/\text{m}$ per UTE C 15-105 §5.3, permitted for $S \ge 16\text{ mm}^2$).
- **Flexible Ingestion (`_missing_`)**:
  - `'cu'`, `'CU'`, `'copper'`, `'cuivre'` $\to$ `ConductorMaterial.CU`
  - `'al'`, `'AL'`, `'aluminium'`, `'aluminum'` $\to$ `ConductorMaterial.AL`

#### 3. `InsulationType`
Cable dielectric insulation material defining maximum permissible operating temperatures:
```python
class InsulationType(str, Enum):
    PVC = "PVC"
    XLPE = "XLPE"
```
- **Values & Semantics**:
  - `PVC` ("PVC"): Polyvinyl chloride (maximum continuous operating temperature $\theta_{\max} = 70^\circ\text{C}$, short-circuit limit $160^\circ\text{C}$).
  - `XLPE` ("XLPE"): Cross-linked polyethylene / PR / EPR (maximum continuous operating temperature $\theta_{\max} = 90^\circ\text{C}$, short-circuit limit $250^\circ\text{C}$).
- **Flexible Ingestion (`_missing_`)**:
  - `'pvc'`, `'PVC'` $\to$ `InsulationType.PVC`
  - `'xlpe'`, `'XLPE'`, `'pr'`, `'PR'`, `'epr'`, `'EPR'` $\to$ `InsulationType.XLPE`

#### 4. `InstallationMethod`
Standard Reference Installation Method Letters per NF C 15-100 Table 52C & UTE C 15-105 Table BB/BC:
```python
class InstallationMethod(str, Enum):
    B = "B"
    C = "C"
    E = "E"
    F = "F"
```
- **Values & Semantics**:
  - `B` ("B"): Conduit or trunking on a wall or embedded in building structures ($k_1 = 1.00$).
  - `C` ("C"): Single-core or multi-core cables affixed directly to a wooden/masonry wall or on unperforated cable tray ($k_1 = 1.00$).
  - `E` ("E"): Multi-core cable in free air or on perforated cable tray/ladder ($k_1 = 1.00$).
  - `F` ("F"): Single-core cables in free air or on perforated cable tray touching in trefoil or flat ($k_1 = 1.00$).
- **Flexible Ingestion (`_missing_`)**:
  - `'b'`, `'B'`, `'b1'`, `'B1'`, `'b2'`, `'B2'` $\to$ `InstallationMethod.B`
  - `'c'`, `'C'` $\to$ `InstallationMethod.C`
  - `'e'`, `'E'` $\to$ `InstallationMethod.E`
  - `'f'`, `'F'` $\to$ `InstallationMethod.F`

#### 5. `LimitingConstraint`
Governing criterion that determined the selected conductor cross-section:
```python
class LimitingConstraint(str, Enum):
    AMPACITY = "ampacity"
    VOLTAGE_DROP = "voltage_drop"
    THERMAL_STRESS = "thermal_stress"
```
- **Values & Semantics**:
  - `AMPACITY` ("ampacity"): Conductor sized to carry continuous thermal current ($I_b \le I_n \le I_z$).
  - `VOLTAGE_DROP` ("voltage_drop"): Conductor upsized to satisfy the permissible voltage drop limit ($\Delta U\% \le \Delta U_{\max}\%$).
  - `THERMAL_STRESS` ("thermal_stress"): Conductor upsized to withstand prospective short-circuit adiabatic Joule integral ($I^2 t \le k^2 S^2$).
- **Dual Survey & Standard Compatibility (`_missing_`)**:
  - `'iz'`, `'Iz'`, `'ampacity'`, `'thermal_ampacity'` $\to$ `LimitingConstraint.AMPACITY`
  - `'du'`, `'dU'`, `'voltage_drop'`, `'voltage-drop'`, `'drop'` $\to$ `LimitingConstraint.VOLTAGE_DROP`
  - `'thermal_stress'`, `'thermal'`, `'i2t'`, `'short_circuit'` $\to$ `LimitingConstraint.THERMAL_STRESS`

---

### 3.2 Input Pydantic Domain Schemas

#### 1. `ElectricalLoad`
Defines operating characteristics and electrical power demand.
- **Fields**:
  - `voltage_v: float`: Nominal voltage in Volts (V). Must be `gt=0.0`.
  - `phases: PhaseSystem`: System topology (default `PhaseSystem.THREE_PHASE`).
  - `cos_phi: float`: Operating displacement power factor $\cos\varphi$ (default `0.85`). Valid range: `gt=0.0, le=1.0`.
  - `power_kw: Optional[float]`: Active power demand in kilowatts (kW). Must be `gt=0.0`.
  - `apparent_power_kva: Optional[float]`: Apparent power demand in kilovolt-amperes (kVA). Must be `gt=0.0`.
  - `current_a: Optional[float]`: Direct design operating current in Amperes (A). Must be `gt=0.0`.
  - `frequency_hz: float`: System operating frequency in Hertz (Hz) (default `50.0`, `ge=0.0`).
  - `harmonic_ih3_ratio: float`: Ratio of 3rd harmonic current to fundamental $i_{h3} = I_{h3}/I_b$ (default `0.0`, range `ge=0.0, le=1.0`).
- **Validation Rules (`@model_validator(mode="after")`)**:
  - **Mutual Exclusivity**: Exactly ONE of `power_kw`, `apparent_power_kva`, or `current_a` must be non-null.
    - If all three are `None`: raises `ValueError("Must provide at least one of: power_kw, apparent_power_kva, or current_a.")`.
    - If more than one is provided: raises `ValueError("Please provide ONLY ONE of: power_kw, apparent_power_kva, or current_a to avoid ambiguity.")`.
  - **DC Power Factor Compatibility**: If `phases == PhaseSystem.DC`, `cos_phi` is conventionally fixed to `1.0`.

#### 2. `CableSpecs`
Defines physical attributes of the conductor route.
- **Fields**:
  - `length_m: float`: One-way circuit route length in meters (m). Must be `gt=0.0`.
  - `conductor: ConductorMaterial`: Conductor core metal (default `ConductorMaterial.CU`).
  - `insulation: InsulationType`: Cable dielectric insulation (default `InsulationType.XLPE`).
  - `multicore: bool`: Cable geometry (default `True` for multi-core, `False` for single-core).
  - `section_custom_mm2: Optional[float]`: Pre-defined cross-section in mm² if user wishes to evaluate a specific cable rather than auto-sizing (default `None`, `gt=0.0`).

#### 3. `InstallationConditions`
Environmental and installation conditions governing NF C 15-100 derating factors.
- **Fields**:
  - `method: InstallationMethod`: Standard reference method letter (default `InstallationMethod.C`).
  - `ambient_temp_c: float`: Ambient temperature in °C (default `30.0`, range `ge=-20.0, le=80.0`).
  - `grouping_circuits: int`: Number of adjacent circuits or multicore cables grouped together (default `1`, range `ge=1, le=40`).
  - `touching: bool`: True if cables are touching in a single layer ($k_2 < 1.0$), False if spaced with clearance $d \ge D$ ($k_2 = 1.0$) (default `True`).
  - `in_ground: bool`: True if cable is installed underground or buried in soil (reference temp 20°C) (default `False`).
  - `k_custom: float`: User-specified additional derating multiplier (default `1.0`, range `gt=0.0, le=2.0`).

#### 4. `ProtectionDevice`
Upstream overcurrent protection characteristics.
- **Fields**:
  - `in_a: Optional[float]`: Nominal rated current $I_n$ in Amperes (A). If `None`, the engine automatically selects the smallest standard rating $I_n \ge I_b$. Must be `gt=0.0`.
  - `ik_a: Optional[float]`: Prospective short-circuit current at cable origin in Amperes (A) for adiabatic thermal stress verification. Must be `gt=0.0`.
  - `disconnection_time_s: Optional[float]`: Fault clearing duration in seconds (s). Must be `gt=0.0, le=5.0` (NF C 15-100 §434.5.2 adiabatic formula is valid for $t \le 5\text{ s}$).
  - `device_type: str`: Device protection standard (default `"circuit_breaker"`, options `"circuit_breaker"` or `"fuse_gG"`).

#### 5. `CircuitDefinition`
Top-level circuit specification combining load, cable, installation, and protection settings.
- **Fields**:
  - `name: str`: Descriptive circuit identifier (default `"Circuit_1"`).
  - `load: ElectricalLoad`: Load requirements.
  - `cable: CableSpecs`: Cable specifications.
  - `installation: InstallationConditions`: Installation conditions (default factory).
  - `protection: ProtectionDevice`: Protection specifications (default factory).
  - `du_max_percent: float`: Maximum allowable relative voltage drop $\Delta U_{\max}\%$ (default `5.0%`, range `gt=0.0, le=20.0%`).
- **Validation Rules (`@model_validator(mode="after")`)**:
  - **Insulation Thermal Limit Enforcement**:
    - If `cable.insulation == InsulationType.PVC` and `installation.ambient_temp_c >= 70.0`: raises `ValueError("Ambient temperature (>= 70°C) reaches or exceeds maximum operating temperature of PVC insulation (70°C). Use XLPE or reduce ambient temperature.")`.
    - If `cable.insulation == InsulationType.XLPE` and `installation.ambient_temp_c >= 90.0`: raises `ValueError("Ambient temperature (>= 90°C) reaches or exceeds maximum operating temperature of XLPE insulation (90°C).")`.

---

### 3.3 Output & Audit Domain Schemas

#### 1. `VoltageDropResult`
Calculated line voltage drop metrics.
- **Fields**:
  - `du_volts: float`: Absolute voltage drop in Volts (V).
  - `du_percent: float`: Relative voltage drop in percentage (%).
  - `du_max_percent: float`: Maximum allowable voltage drop threshold (%).
  - `is_compliant: bool`: `True` if `du_percent <= du_max_percent`.
  - `margin_percent: float`: Remaining margin `du_max_percent - du_percent` (%).
  - `b_factor: float`: Circuit topology coefficient (1.0 for three-phase, 2.0 for single-phase/DC).

#### 2. `ThermalStressResult`
Short-circuit adiabatic thermal withstand assessment ($I^2 t \le k^2 S^2$).
- **Fields**:
  - `ik_a: float`: Prospective fault current in Amperes (A).
  - `time_s: float`: Disconnection duration in seconds (s).
  - `i2t: float`: Joule energy let-through $I^2 t$ in $\text{A}^2\cdot\text{s}$.
  - `k_factor: float`: Normative material constant $k$ in $\text{A}\cdot\text{s}^{1/2}/\text{mm}^2$.
  - `s_min_mm2: float`: Minimum required cross-section $S_{\min} = \sqrt{I^2 t}/k$ in mm².
  - `is_compliant: bool`: `True` if `selected_section_mm2 >= s_min_mm2`.

#### 3. `IntermediateFactors`
Full audit trail of all intermediate derating coefficients and physical constants.
- **Fields**:
  - `k1_method: float`: Installation method correction factor $k_1$.
  - `k2_grouping: float`: Multi-circuit grouping reduction factor $k_2$.
  - `k3_temperature: float`: Ambient temperature correction factor $k_3$.
  - `k_custom: float`: Custom derating multiplier.
  - `kh_harmonic: float`: Harmonic derating factor $k_h$ per IEC 60364-5-52 Table E.52.1.
  - `k_total: float`: Cumulative derating factor product $\prod k_i = k_1 \times k_2 \times k_3 \times k_h \times k_{\text{custom}}$.
  - `rho_ohm_mm2_m: float`: Operating electrical resistivity $\rho_1$ in $\Omega\cdot\text{mm}^2/\text{m}$.
  - `reactance_ohm_m: float`: Linear reactance $\lambda$ in $\Omega/\text{m}$.
  - `cos_phi: float`: Operating power factor $\cos\varphi$.
  - `sin_phi: float`: Operating reactive factor $\sin\varphi = \sqrt{1 - \cos^2\varphi}$.

#### 4. `SizingResult`
Comprehensive calculation report produced by `SizingEngine`.
- **Fields**:
  - `circuit_name: str`: Circuit identifier.
  - `ib_a: float`: Calculated design operating current $I_b$ (A).
  - `in_a: float`: Nominal rated current of protective device $I_n$ (A).
  - `iz_min_required_a: float`: Required admissible current $I'_z = I_n / k_{\text{total}}$ (A).
  - `selected_section_mm2: float`: Selected standard cross-section $S$ (mm²).
  - `i0_reference_a: float`: Reference base current $I_0$ for the selected section (A).
  - `iz_effective_a: float`: Effective permissible current $I_z = I_0 \times k_{\text{total}}$ (A).
  - `ampacity_compliant: bool`: `True` if coordination condition $I_b \le I_n \le I_z$ holds.
  - `voltage_drop: VoltageDropResult`: Voltage drop calculation details.
  - `thermal_stress: Optional[ThermalStressResult]`: Short-circuit thermal withstand check (if $I_k$ specified).
  - `intermediate_factors: IntermediateFactors`: Complete derating audit trail.
  - `limiting_constraint: LimitingConstraint`: Governing sizing constraint (`AMPACITY`, `VOLTAGE_DROP`, or `THERMAL_STRESS`).
  - `is_compliant: bool`: Overall compliance status.
  - `notes: list[str]`: Engineering annotations and normative references.

---

## 4. Complete Drop-In Source Code: `src/ampy/core/models.py`

Below is the complete, self-contained implementation code to be created at `src/ampy/core/models.py`:

```python
"""
ampy.core.models
================
Strongly-typed Pydantic v2 schemas and standard enums for electrical cable sizing
in strict compliance with NF C 15-100 (Part 5-52) and UTE C 15-105.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==============================================================================
# Standard Normative Enums
# ==============================================================================

class PhaseSystem(str, Enum):
    """
    Electrical phase arrangement.
    - SINGLE_PHASE: 1-phase AC (Phase + Neutral or Phase-Phase, standard 230V, b=2)
    - THREE_PHASE: 3-phase AC (3-Phase balanced, standard 400V, b=1)
    - DC: Direct Current 2-wire system (b=2)
    """
    SINGLE_PHASE = "single_phase"
    THREE_PHASE = "three_phase"
    DC = "dc"

    @classmethod
    def _missing_(cls, value: object) -> Optional[PhaseSystem]:
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("1", "1p", "single", "single_phase", "single-phase"):
                return cls.SINGLE_PHASE
            if v in ("3", "3p", "three", "three_phase", "three-phase"):
                return cls.THREE_PHASE
            if v in ("dc", "direct", "direct_current"):
                return cls.DC
        elif isinstance(value, int):
            if value == 1:
                return cls.SINGLE_PHASE
            if value == 3:
                return cls.THREE_PHASE
        return None


class ConductorMaterial(str, Enum):
    """
    Conductor core metal according to NF C 15-100 Part 5-52:
    - CU: Pure Copper (rho1 = 0.023 ohm.mm2/m)
    - AL: Pure Aluminium (rho1 = 0.037 ohm.mm2/m, standard min section >= 16 mm2)
    """
    CU = "Cu"
    AL = "Al"

    @classmethod
    def _missing_(cls, value: object) -> Optional[ConductorMaterial]:
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("cu", "copper", "cuivre"):
                return cls.CU
            if v in ("al", "aluminum", "aluminium"):
                return cls.AL
        return None


class InsulationType(str, Enum):
    """
    Dielectric insulation material and maximum continuous operating temperature:
    - PVC: Polyvinyl Chloride (max continuous operating temp 70°C)
    - XLPE: Cross-linked Polyethylene / PR / EPR (max continuous operating temp 90°C)
    """
    PVC = "PVC"
    XLPE = "XLPE"

    @classmethod
    def _missing_(cls, value: object) -> Optional[InsulationType]:
        if isinstance(value, str):
            v = value.strip().upper()
            if v in ("PVC",):
                return cls.PVC
            if v in ("XLPE", "PR", "EPR"):
                return cls.XLPE
        return None


class InstallationMethod(str, Enum):
    """
    Reference Installation Method Letter according to NF C 15-100 Table 52C:
    - B: Conduit or trunking on a wall or embedded in building structures
    - C: Single-core or multi-core cables on wall, wooden surface, or unperforated tray
    - E: Multi-core cable in free air or on perforated cable tray/ladder
    - F: Single-core cables in free air or on perforated cable tray touching
    """
    B = "B"
    C = "C"
    E = "E"
    F = "F"

    @classmethod
    def _missing_(cls, value: object) -> Optional[InstallationMethod]:
        if isinstance(value, str):
            v = value.strip().upper()
            if v in ("B", "B1", "B2"):
                return cls.B
            if v in ("C",):
                return cls.C
            if v in ("E",):
                return cls.E
            if v in ("F",):
                return cls.F
        return None


class LimitingConstraint(str, Enum):
    """
    Governing constraint that dictated the final conductor cross-section:
    - AMPACITY: Continuous current thermal carrying capacity (Ib <= In <= Iz)
    - VOLTAGE_DROP: Permissible relative voltage drop limit (dU% <= dU_max%)
    - THERMAL_STRESS: Adiabatic short-circuit withstand limit (I2t <= k2S2)
    """
    AMPACITY = "ampacity"
    VOLTAGE_DROP = "voltage_drop"
    THERMAL_STRESS = "thermal_stress"

    @classmethod
    def _missing_(cls, value: object) -> Optional[LimitingConstraint]:
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("iz", "ampacity", "thermal_ampacity"):
                return cls.AMPACITY
            if v in ("du", "voltage_drop", "voltage-drop", "drop"):
                return cls.VOLTAGE_DROP
            if v in ("thermal_stress", "thermal", "i2t", "short_circuit"):
                return cls.THERMAL_STRESS
        return None


# ==============================================================================
# Input Domain Schemas
# ==============================================================================

class ElectricalLoad(BaseModel):
    """
    Electrical load specifications.
    User must specify exactly one of: active power (kW), apparent power (kVA),
    or direct design current (A).
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    voltage_v: float = Field(
        ...,
        gt=0.0,
        description="Nominal system voltage in Volts (V) (e.g. 230V for 1P, 400V for 3P)"
    )
    phases: PhaseSystem = Field(
        default=PhaseSystem.THREE_PHASE,
        description="Electrical phase system topology (SINGLE_PHASE, THREE_PHASE, DC)"
    )
    cos_phi: float = Field(
        default=0.85,
        gt=0.0,
        le=1.0,
        description="Displacement operating power factor cos(phi) (0.0 < cos_phi <= 1.0)"
    )
    power_kw: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Active power demand in kilowatts (kW)"
    )
    apparent_power_kva: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Apparent power demand in kilovolt-amperes (kVA)"
    )
    current_a: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Direct design operating current in Amperes (A)"
    )
    frequency_hz: float = Field(
        default=50.0,
        ge=0.0,
        description="AC system frequency in Hertz (Hz) (default 50.0 Hz, 0.0 for DC)"
    )
    harmonic_ih3_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of 3rd harmonic current to fundamental Ih3 / Ib (0.0 to 1.0)"
    )

    @model_validator(mode="after")
    def validate_load_input(self) -> ElectricalLoad:
        """Enforces mutual exclusivity: exactly one load input parameter must be given."""
        provided = [
            self.power_kw is not None,
            self.apparent_power_kva is not None,
            self.current_a is not None,
        ]
        if not any(provided):
            raise ValueError(
                "Must provide at least one of: power_kw, apparent_power_kva, or current_a."
            )
        if sum(provided) > 1:
            raise ValueError(
                "Please provide ONLY ONE of: power_kw, apparent_power_kva, or current_a "
                "to avoid ambiguity."
            )
        return self


class CableSpecs(BaseModel):
    """
    Cable physical attributes and circuit route configuration.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)

    length_m: float = Field(
        ...,
        gt=0.0,
        description="One-way circuit route length in meters (m)"
    )
    conductor: ConductorMaterial = Field(
        default=ConductorMaterial.CU,
        description="Conductor metal core: Cu (Copper) or Al (Aluminium)"
    )
    insulation: InsulationType = Field(
        default=InsulationType.XLPE,
        description="Insulation material: PVC (max 70°C) or XLPE (max 90°C)"
    )
    multicore: bool = Field(
        default=True,
        description="True for multi-conductor cable, False for single-core cables"
    )
    section_custom_mm2: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Optional pre-selected cross-section in mm² (enforces section evaluation)"
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
        ge=-20.0,
        le=80.0,
        description="Ambient temperature in °C (reference: 30°C in air, 20°C in ground)"
    )
    grouping_circuits: int = Field(
        default=1,
        ge=1,
        le=40,
        description="Number of circuits or multi-core cables grouped together (factor k2)"
    )
    touching: bool = Field(
        default=True,
        description="True if grouped cables are touching (jointifs), False if spaced (d >= D)"
    )
    in_ground: bool = Field(
        default=False,
        description="True if cable is installed underground or buried in soil"
    )
    k_custom: float = Field(
        default=1.0,
        gt=0.0,
        le=2.0,
        description="User-defined additional derating multiplier (e.g. solar radiation, safety margin)"
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
        description="Prospective short-circuit current at cable head in Amperes (A)"
    )
    disconnection_time_s: Optional[float] = Field(
        default=None,
        gt=0.0,
        le=5.0,
        description="Disconnection / tripping time in seconds (s). Must be <= 5.0s for adiabatic regime."
    )
    device_type: str = Field(
        default="circuit_breaker",
        description="Protective device type: 'circuit_breaker' (NF EN 60898/60947-2) or 'fuse_gG' (NF EN 60269)"
    )


class CircuitDefinition(BaseModel):
    """
    Complete circuit definition combining load, cable, installation, and protection settings.
    Serves as input to SizingEngine and serialization root for YAML/JSON configurations.
    """
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        default="Circuit_1",
        description="Unique identifier or descriptive name for the circuit"
    )
    load: ElectricalLoad = Field(
        ...,
        description="Electrical load demand and voltage specifications"
    )
    cable: CableSpecs = Field(
        ...,
        description="Cable physical attributes and route length"
    )
    installation: InstallationConditions = Field(
        default_factory=InstallationConditions,
        description="Installation environmental and grouping conditions"
    )
    protection: ProtectionDevice = Field(
        default_factory=ProtectionDevice,
        description="Upstream protective device ratings and fault data"
    )
    du_max_percent: float = Field(
        default=5.0,
        gt=0.0,
        le=20.0,
        description="Maximum allowable relative voltage drop in percentage (%)"
    )

    @model_validator(mode="after")
    def validate_insulation_temperature(self) -> CircuitDefinition:
        """Validates that ambient temperature does not reach or exceed insulation maximum limits."""
        temp = self.installation.ambient_temp_c
        insulation = self.cable.insulation
        if insulation == InsulationType.PVC and temp >= 70.0:
            raise ValueError(
                f"Ambient temperature ({temp}°C) reaches or exceeds maximum operating "
                f"temperature of PVC insulation (70°C). Use XLPE or reduce ambient temperature."
            )
        if insulation == InsulationType.XLPE and temp >= 90.0:
            raise ValueError(
                f"Ambient temperature ({temp}°C) reaches or exceeds maximum operating "
                f"temperature of XLPE insulation (90°C)."
            )
        return self


# ==============================================================================
# Output & Audit Domain Schemas
# ==============================================================================

class IntermediateFactors(BaseModel):
    """
    Detailed audit trail of all intermediate derating coefficients and physical parameters.
    """
    model_config = ConfigDict(frozen=True)

    k1_method: float = Field(description="Installation method factor k1 (UTE C 15-105 Table BD)")
    k2_grouping: float = Field(description="Multi-circuit grouping factor k2 (NF C 15-100 Table 52N)")
    k3_temperature: float = Field(description="Ambient temperature factor k3 (NF C 15-100 Table 52K)")
    k_custom: float = Field(default=1.0, description="Custom user-defined derating multiplier")
    kh_harmonic: float = Field(default=1.0, description="Harmonic derating factor kh (IEC 60364-5-52 Table E.52.1)")
    k_total: float = Field(description="Total cumulative derating factor product prod(ki)")
    rho_ohm_mm2_m: float = Field(description="Conductor operating resistivity rho1 in ohm.mm2/m")
    reactance_ohm_m: float = Field(description="Linear conductor reactance lambda in ohm/m")
    cos_phi: float = Field(description="Operating displacement power factor cos(phi)")
    sin_phi: float = Field(description="Operating reactive factor sin(phi) = sqrt(1 - cos2(phi))")


class VoltageDropResult(BaseModel):
    """
    Detailed voltage drop calculation results and normative compliance status.
    """
    model_config = ConfigDict(frozen=True)

    du_volts: float = Field(description="Absolute line voltage drop in Volts (V)")
    du_percent: float = Field(description="Relative voltage drop in percentage (%)")
    du_max_percent: float = Field(description="Maximum permissible relative voltage drop threshold (%)")
    is_compliant: bool = Field(description="True if du_percent <= du_max_percent")
    margin_percent: float = Field(description="Remaining margin: du_max_percent - du_percent (%)")
    b_factor: float = Field(default=1.0, description="Circuit topology factor: 1.0 for three-phase, 2.0 for single-phase/DC")


class ThermalStressResult(BaseModel):
    """
    Short-circuit thermal stress withstand assessment (I2t <= k2S2 per NF C 15-100 §434.5.2).
    """
    model_config = ConfigDict(frozen=True)

    ik_a: float = Field(description="Prospective short-circuit current in Amperes (A)")
    time_s: float = Field(description="Disconnection duration in seconds (s)")
    i2t: float = Field(description="Joule integral thermal energy let-through I2t in A2.s")
    k_factor: float = Field(description="Adiabatic material constant k in A.s^(1/2)/mm2")
    s_min_mm2: float = Field(description="Minimum required cross-section for thermal withstand in mm2")
    is_compliant: bool = Field(description="True if selected section >= s_min_mm2")


class SizingResult(BaseModel):
    """
    Comprehensive cable sizing calculation output conforming to NF C 15-100 & UTE C 15-105.
    """
    model_config = ConfigDict(frozen=True)

    circuit_name: str = Field(description="Identifier of the sized circuit")
    ib_a: float = Field(description="Calculated design operating current Ib (A)")
    in_a: float = Field(description="Selected or validated nominal protection rating In (A)")
    iz_min_required_a: float = Field(description="Minimum required base current I'z = In / k_total (A)")
    selected_section_mm2: float = Field(description="Selected standard conductor cross-section (mm2)")
    i0_reference_a: float = Field(description="Normative reference admissible current I0 from standard table (A)")
    iz_effective_a: float = Field(description="Effective permissible current in actual conditions Iz = I0 * k_total (A)")
    ampacity_compliant: bool = Field(description="True if continuous current coordination Ib <= In <= Iz is satisfied")
    voltage_drop: VoltageDropResult = Field(description="Calculated voltage drop metrics and compliance")
    thermal_stress: Optional[ThermalStressResult] = Field(
        default=None,
        description="Thermal stress withstand result if short-circuit parameters were provided"
    )
    intermediate_factors: IntermediateFactors = Field(description="Audit trail of all derating factors and constants")
    limiting_constraint: LimitingConstraint = Field(
        description="The governing condition that determined final cross-section: AMPACITY, VOLTAGE_DROP, or THERMAL_STRESS"
    )
    is_compliant: bool = Field(
        description="Overall compliance: True if ampacity, voltage drop, and thermal stress are all satisfied"
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Normative annotations, design margins, and engineering remarks"
    )
```

---

## 5. Serialization & JSON Schema Export Specifications

### 5.1 JSON Schema Generation
Because models are built using standard Pydantic v2, exporting JSON Schema for frontend UI generation or REST API documentation (FastAPI/OpenAPI) is supported directly:
```python
# Export full JSON Schema as Python dictionary
schema = CircuitDefinition.model_json_schema()

# Export SizingResult schema
result_schema = SizingResult.model_json_schema()
```
The resulting schemas contain:
- Explicit field titles, descriptions, units, and default values.
- Normative constraints (`gt=0.0`, `ge=0.0, le=1.0`, etc.).
- Enum allowed values (`$defs` references for `PhaseSystem`, `ConductorMaterial`, `InsulationType`, `InstallationMethod`, `LimitingConstraint`).

### 5.2 YAML & JSON Round-Trip Fidelity
```python
import yaml
from ampy.core.models import CircuitDefinition, SizingResult

# 1. Parsing from YAML string / file
yaml_data = """
name: "Compressor_Line_1"
load:
  voltage_v: 400.0
  phases: "3P"
  power_kw: 30.0
  cos_phi: 0.85
cable:
  length_m: 75.0
  conductor: "Cu"
  insulation: "XLPE"
installation:
  method: "C"
  ambient_temp_c: 35.0
  grouping_circuits: 2
protection:
  in_a: 63.0
du_max_percent: 5.0
"""
parsed_dict = yaml.safe_load(yaml_data)
circuit = CircuitDefinition.model_validate(parsed_dict)

# 2. Exporting to JSON
json_output = circuit.model_dump_json(indent=2)

# 3. Restoring from JSON
restored_circuit = CircuitDefinition.model_validate_json(json_output)
assert restored_circuit.load.power_kw == 30.0
```

---

## 6. Interface Contracts with Other Ampy Modules

### 6.1 Contract: `models` ↔ `formulas` (`ampy.core.formulas`)
- `formulas.calculate_ib(load: ElectricalLoad) -> float`
  - Consumes `load.phases`, `load.voltage_v`, `load.cos_phi`, `load.power_kw`, `load.apparent_power_kva`, `load.current_a`.
  - Returns calculated $I_b$ in Amperes rounded to 3 decimal places.
- `formulas.calculate_voltage_drop(...) -> VoltageDropResult`
  - Consumes $I_b$, route length, section, power factor, system phase, voltage, and maximum allowable percentage.
  - Returns an immutable `VoltageDropResult` instance.
- `formulas.calculate_thermal_stress(...) -> ThermalStressResult`
  - Consumes $I_k$, disconnection time, conductor metal, insulation, and candidate cross-section.
  - Returns an immutable `ThermalStressResult` instance.

### 6.2 Contract: `models` ↔ `tables` (`ampy.core.tables`)
- Table lookups use enum keys directly:
  `table_key = (installation.method, cable.conductor, cable.insulation, loaded_conductors)`
- Factor lookups:
  - `get_k1_installation_method(method: InstallationMethod) -> float`
  - `get_k2_grouping(circuits_count: int, touching: bool) -> float`
  - `get_k3_temperature(insulation: InsulationType, temp_c: float, in_ground: bool) -> float`

### 6.3 Contract: `models` ↔ `engine` (`ampy.core.engine`)
- Sizing method signature:
  `SizingEngine.size_circuit(circuit: CircuitDefinition) -> SizingResult`
- SizingResult attributes:
  - `result.selected_section_mm2: float`
  - `result.limiting_constraint: LimitingConstraint`
  - `result.is_compliant: bool`
  - `result.intermediate_factors: IntermediateFactors`

### 6.4 Contract: `models` ↔ `cli` (`ampy.cli`)
- The CLI parser converts Typer options directly into `CircuitDefinition`:
  `circuit = CircuitDefinition(load=ElectricalLoad(...), cable=CableSpecs(...), ...)`
- The Rich formatter extracts `result.intermediate_factors` and `result.voltage_drop` to render terminal audit tables and status panels.

---

## 7. Milestone 1 Unit Test Design (`tests/unit/test_models.py`)

The coder and test-writer agents should implement the following test suites in `tests/unit/test_models.py`:

### 7.1 Test Case Matrix

| Test Function | Target Feature | Description & Input Conditions | Expected Outcome |
| :--- | :--- | :--- | :--- |
| `test_electrical_load_valid_kw()` | F06 | 3P, 400V, `power_kw=15.0`, `cos_phi=0.85` | Valid instantiation, `load.power_kw == 15.0` |
| `test_electrical_load_valid_kva()` | F06 | 1P, 230V, `apparent_power_kva=5.0` | Valid instantiation, `load.apparent_power_kva == 5.0` |
| `test_electrical_load_valid_current()` | F06 | 3P, 400V, `current_a=32.0` | Valid instantiation, `load.current_a == 32.0` |
| `test_electrical_load_missing_power()` | F06 | All of `power_kw`, `apparent_power_kva`, `current_a` are `None` | Raises `ValidationError` ("Must provide at least one") |
| `test_electrical_load_multiple_power()` | F06 | Both `power_kw=10.0` and `current_a=20.0` provided | Raises `ValidationError` ("Please provide ONLY ONE") |
| `test_electrical_load_invalid_cos_phi()` | F06 | `cos_phi=0.0` or `cos_phi=1.1` or `cos_phi=-0.5` | Raises `ValidationError` |
| `test_electrical_load_invalid_voltage()` | F06 | `voltage_v=0.0` or `voltage_v=-230.0` | Raises `ValidationError` |
| `test_cable_specs_valid()` | F06 | `length_m=50.0`, `conductor='Cu'`, `insulation='XLPE'` | Valid instantiation, `cable.length_m == 50.0` |
| `test_cable_specs_invalid_length()` | F06 | `length_m=0.0` or `length_m=-10.0` | Raises `ValidationError` |
| `test_installation_conditions_defaults()` | F06 | Empty constructor `InstallationConditions()` | `method == InstallationMethod.C`, `ambient_temp_c == 30.0` |
| `test_installation_conditions_invalid_temp()` | F06 | `ambient_temp_c=100.0` | Raises `ValidationError` |
| `test_protection_device_defaults()` | F06 | Empty constructor `ProtectionDevice()` | `in_a is None`, `device_type == 'circuit_breaker'` |
| `test_protection_device_invalid_time()` | F06 | `disconnection_time_s=6.0` (> 5.0s adiabatic limit) | Raises `ValidationError` |
| `test_circuit_definition_pvc_temp_limit()` | F06 | `insulation=PVC`, `ambient_temp_c=70.0` | Raises `ValidationError` ("reaches or exceeds PVC max limit") |
| `test_circuit_definition_xlpe_temp_limit()` | F06 | `insulation=XLPE`, `ambient_temp_c=90.0` | Raises `ValidationError` ("reaches or exceeds XLPE max limit") |
| `test_enum_coercion_phase_system()` | F06 | Pass `'1P'`, `1`, `'3P'`, `3`, `'DC'` | Correctly coerced to `PhaseSystem` enum members |
| `test_enum_coercion_limiting_constraint()` | F06 | Pass `'Iz'`, `'ampacity'`, `'dU'`, `'voltage_drop'` | Correctly coerced to `LimitingConstraint` enum members |
| `test_extra_fields_forbidden()` | F06 | Pass `unknown_arg=123` to any model | Raises `ValidationError` (extra fields forbidden) |
| `test_json_serialization_roundtrip()` | F06 | Model dump to JSON string and validate back | Complete object fidelity with exact matching attributes |
| `test_json_schema_export()` | F06 | Call `CircuitDefinition.model_json_schema()` | Returns valid schema dict containing properties and defs |

---

## 8. Step-by-Step Implementation Instructions for Implementer

When implementing Milestone 1:

1. **Create Package Layout**:
   - Create root file `pyproject.toml` using the exact configuration in §2.1.
   - Create `src/ampy/__init__.py`.
   - Create `src/ampy/py.typed` (empty file).
   - Create `src/ampy/core/__init__.py`.
   - Create `src/ampy/core/models.py` using the exact code in §4.
2. **Install in Editable Mode**:
   - Run `pip install -e .` (or test import directly via `PYTHONPATH=src`).
3. **Verify Schemas**:
   - Run verification script:
     `python -c "from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs; print('Import OK')"`
4. **Implement Unit Tests**:
   - Create `tests/unit/test_models.py` implementing the 20 test cases in §7.1.
   - Run `pytest tests/unit/test_models.py` to confirm 100% pass rate.
