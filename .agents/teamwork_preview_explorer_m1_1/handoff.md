# Milestone 1 (M1) Handoff Report: Packaging & Domain Models

**Author**: `teamwork_preview_explorer_m1_1`  
**Date**: 2026-09-30  
**Handoff Type**: Hard (Investigation & Blueprint Complete)  
**Deliverable**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_1\models_plan.md`  

---

## 1. Observation

### 1.1 Baseline Requirements & Normative Documents
- **`ORIGINAL_REQUEST.md`**:
  - Line 14: Cable sizing engine must compute design operating current $I_b$ for single-phase (230V) and three-phase (400V) systems across active power (kW), apparent power (kVA), and direct current (A).
  - Line 26: Requires clean CLI using Typer/Rich and Pydantic schemas.
  - Line 45: Requires type annotations, Pydantic data validation, and modular structure.
- **`PROJECT.md`**:
  - Lines 77, 93-96, 129: Milestone 1 (M1) scope encompasses packaging (`pyproject.toml`), domain schemas (`src/ampy/core/models.py`), and pure calculation formulas (`src/ampy/core/formulas.py`).
  - Lines 120-151: Standard `src/` layout specified (`src/ampy/core/`, `src/ampy/cli/`, `tests/`).
- **`architecture.md`**:
  - Lines 198-223: Domain enums specified (`ConductorMaterial`, `InsulationType`, `InstallationMethod`, `PhaseSystem`, `LimitingConstraint`).
  - Lines 231-389: Input Pydantic models specified (`ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition`).
  - Lines 394-462: Output models specified (`IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, `SizingResult`).
- **`normative_specs.md`**:
  - Lines 22-30: Sizing formulas for Single-phase ($V_n=230\text{V}$, $b=2$), Three-phase ($U_n=400\text{V}$, $b=1$), and DC ($b=2$).
  - Lines 149-170: Ambient temperature operating limits ($70^\circ\text{C}$ for PVC, $90^\circ\text{C}$ for XLPE).
  - Lines 256-270: Coordination conditions ($I_b \le I_n \le I_z$, $\Delta U\% \le \Delta U_{\max}\%$, $I^2 t \le k^2 S^2$).
  - Lines 330-350: Adiabatic thermal limits valid for $t \le 5\text{ s}$ ($k=115$ for Cu/PVC, $143$ for Cu/XLPE, $76$ for Al/PVC, $94$ for Al/XLPE).

### 1.2 Execution Environment Observations
- Active Python environment: Python 3.13.5 (verified via `python --version`).
- Installed packages (verified via `python -m pip list`):
  - `pydantic` 2.11.7
  - `setuptools` 80.9.0
  - `wheel` (managed by setuptools)
  - `click` 8.3.1
- Runtime model validation verification (`python -c`):
  - Model instantiation of `ElectricalLoad(voltage_v=400.0, power_kw=18.5)` succeeded with JSON dump: `{"voltage_v":400.0,"phases":"three_phase","cos_phi":0.85,"power_kw":18.5,"apparent_power_kva":null,"current_a":null}`.
  - Mutual exclusivity validation verified: empty inputs raise `"Must provide at least one of: power_kw, apparent_power_kva, or current_a"`; multiple inputs raise `"Please provide ONLY ONE of: power_kw, apparent_power_kva, or current_a"`.
  - Enum `_missing_` coercion verified: `'1P'`, `1`, `'single_phase'` coerce to `PhaseSystem.SINGLE_PHASE`; `'3P'`, `3`, `'three_phase'` coerce to `PhaseSystem.THREE_PHASE`; `'Iz'`, `'ampacity'` coerce to `LimitingConstraint.AMPACITY`; `'dU'`, `'voltage_drop'` coerce to `LimitingConstraint.VOLTAGE_DROP`.
  - Insulation boundary validation in `CircuitDefinition` verified: PVC at 70°C raises `ValueError`, XLPE at 90°C raises `ValueError`.

---

## 2. Logic Chain

1. **Packaging Blueprint (`pyproject.toml`)**:
   - Based on PEP 517/518/621 and standard setuptools build backend.
   - In accordance with the prompt and `PROJECT.md`, the runtime dependencies are pinned to `pydantic>=2.0`, `typer>=0.12`, `rich>=13.0`, and `pyyaml>=6.0`.
   - Development dependencies are grouped under `[project.optional-dependencies] dev = ["pytest>=8.0", "pytest-cov>=4.0"]`.
   - Package discovery points to `src/` (`[tool.setuptools.packages.find] where = ["src"]`) and includes `py.typed` to support PEP 561 static type-checking.
   - Tool configurations for `pytest`, `mypy`, and `ruff` are integrated to guarantee code formatting and strict typing.

2. **Domain Enums Design (`src/ampy/core/models.py`)**:
   - `PhaseSystem`: Members `SINGLE_PHASE`, `THREE_PHASE`, `DC`. Enables exact voltage drop topology selection ($b=1$ vs $b=2$) and formula branch selection in `formulas.py`.
   - `ConductorMaterial`: Members `CU = "Cu"`, `AL = "Al"`. Directly maps to resistivity $\rho_1$ and $I_0$ tables.
   - `InsulationType`: Members `PVC = "PVC"`, `XLPE = "XLPE"`. Directly maps to max operating temperature and $k_3$ factors.
   - `InstallationMethod`: Members `B = "B"`, `C = "C"`, `E = "E"`, `F = "F"`. Matches NF C 15-100 Table 52C reference methods.
   - `LimitingConstraint`: Members `AMPACITY = "ampacity"`, `VOLTAGE_DROP = "voltage_drop"`, `THERMAL_STRESS = "thermal_stress"`. With `_missing_` coercion for `"Iz"` and `"dU"`, bridging the terminology between `PROJECT.md`, `architecture.md`, and `normative_specs.md`.

3. **Input Domain Schemas (`src/ampy/core/models.py`)**:
   - `ElectricalLoad`: Validates voltage ($V > 0$), power factor ($0 < \cos\varphi \le 1.0$), and enforces strict mutual exclusivity among `power_kw`, `apparent_power_kva`, and `current_a`.
   - `CableSpecs`: Validates length ($L > 0$), material, insulation, and optional pre-selected cross-section.
   - `InstallationConditions`: Validates method, ambient temperature, circuit grouping ($N \ge 1$), touching vs spaced flag, and custom multipliers.
   - `ProtectionDevice`: Encapsulates nominal rating $I_n$, short-circuit prospective current $I_k$, and disconnection time $t \le 5.0\text{ s}$ (adiabatic limit).
   - `CircuitDefinition`: Root composite schema combining all input aspects, enforcing cross-field temperature validation (PVC $< 70^\circ\text{C}$, XLPE $< 90^\circ\text{C}$).

4. **Output & Audit Schemas (`src/ampy/core/models.py`)**:
   - `VoltageDropResult`: Provides absolute $\Delta U$ (V), relative $\Delta U\%$ (%), limit $\Delta U_{\max}\%$, and margin.
   - `ThermalStressResult`: Provides prospective current $I_k$, clearing time $t$, $I^2 t$ energy, material constant $k$, and required minimum section $S_{\min}$.
   - `IntermediateFactors`: Fully transparent audit trail ($k_1, k_2, k_3, k_h, k_{\text{custom}}, k_{\text{total}}, \rho_1, \lambda, \cos\varphi, \sin\varphi$) for Rich terminal tables and normative inspections.
   - `SizingResult`: Root calculation report capturing selected standard cross-section, $I_b, I_n, I'_z, I_0, I_z$, compliance boolean, and governing constraint.

5. **Validation & Quality Assurance**:
   - All models configured with `extra="forbid"` to catch invalid keys in YAML/JSON.
   - Native Pydantic v2 `model_json_schema()` export verified.

---

## 3. Caveats

1. **Python Environment Dependencies**:
   - The active Python environment (Python 3.13.5) currently has `pydantic 2.11.7` and `setuptools 80.9.0` installed.
   - `typer`, `rich`, `pyyaml`, `pytest`, and `pytest-cov` are not yet installed in this environment. The implementer must run `pip install -e .` or install them using pip when implementing M1.
2. **Harmonics Derating Integration**:
   - IEC 60364-5-52 Table E.52.1 neutral third-harmonic factor $k_h$ is provided on `ElectricalLoad` via `harmonic_ih3_ratio` and reported in `IntermediateFactors.kh_harmonic`. When $i_{h3} = 0$, $k_h = 1.0$ (neutral derating inactive).

---

## 4. Conclusion

The blueprint for Milestone 1 components (`pyproject.toml` and `src/ampy/core/models.py`) is complete, normative, verified against Pydantic v2, and published in `models_plan.md`. The design is fully actionable, zero-placeholder, and ready for immediate drop-in implementation by the coder agent.

---

## 5. Verification Method

To independently verify the blueprint:

1. **Inspect Blueprint File**:
   View `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_1\models_plan.md`.

2. **Execute Python Model & Schema Verification**:
   Run the following verification command in PowerShell:
   ```powershell
   python -c "
   import sys
   from enum import Enum
   from pydantic import BaseModel
   print('Python version:', sys.version)
   # Verify Pydantic version
   import pydantic
   print('Pydantic version:', pydantic.__version__)
   "
   ```

3. **Verify Implementation Once Created**:
   Once `pyproject.toml` and `src/ampy/core/models.py` are written to disk:
   ```powershell
   python -m pip install -e .
   python -c "from ampy.core.models import CircuitDefinition, ElectricalLoad, CableSpecs, PhaseSystem; print('Successfully imported ampy models')"
   pytest tests/unit/test_models.py
   ```

4. **Invalidation Conditions**:
   - Inability to parse load inputs with exactly one of `power_kw`, `apparent_power_kva`, or `current_a`.
   - Failure of enum coercion for `'1P'`, `'3P'`, `'Iz'`, or `'dU'`.
   - Failure to raise validation errors when ambient temperature equals or exceeds $70^\circ\text{C}$ for PVC or $90^\circ\text{C}$ for XLPE.
