# Handoff Report — Software Architecture & CLI Design for `ampy`

**Agent ID**: teamwork_preview_explorer_survey_2  
**Recipient**: teamwork_preview_orchestrator_1 (`776386d9-70f0-46fd-896e-befc19ccbade`)  
**Scope**: Software architecture, Python modular packaging, Pydantic schemas, SizingEngine orchestrator, and Typer/Rich CLI interface for `ampy`.  
**Artifact**: `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md`

---

## 1. Observation

1. **Original User Request Requirements** (`c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md`):
   - Lines 12-24 (R1): Cable sizing engine strictly complying with NF C 15-100 & UTE C 15-105; calculating $I_b$ for 1-phase ($230\text{V}$) and 3-phase ($400\text{V}$); applying correction factors $k_1, k_2, k_3$; $I_b \le I_n \le I_z$; standard sections $1.5$ to $300\text{ mm}^2$ for $\text{Cu}$ and $\text{Al}$; exact relative $\Delta U$ accounting for $\rho_1$ and $\lambda$; thermal stress limit $I^2t \le k^2 S^2$.
   - Lines 25-30 (R2): CLI and modularity; Typer/Rich with Pydantic schemas; one-shot CLI flags and YAML/JSON config file mode; clear terminal reports with intermediate factors; reusable Python library.
   - Lines 31-34 (R3): Automated test suite with pytest covering formulas, tables, and UTE C 15-105 worked benchmark scenarios.

2. **Host Python Environment Inspection**:
   - Tool command: `python --version; pip list` (Background task `task-24`):
     - Python version: `Python 3.13.5`
     - Pydantic: `pydantic 2.11.7` (Pydantic v2 is natively installed)
     - Setuptools: `setuptools 80.9.0` (present in environment)
   - Tool command: `python -c "import typer; import rich; import yaml; import pytest"`:
     - `ModuleNotFoundError: No module named 'typer'`
     - `ModuleNotFoundError: No module named 'rich'`
     - `ModuleNotFoundError: No module named 'yaml'`
     - `ModuleNotFoundError: No module named 'pytest'`
     - Observation: `typer`, `rich`, `pyyaml`, and `pytest` are project dependencies that must be declared in `pyproject.toml` and installed during the implementation phase.

3. **Normative Constraints & Peer Survey Context**:
   - `teamwork_preview_spec_miner_survey_1\DISPATCH.md` lines 15-42: specifies formulas for $I_b$ (single-phase $P / (V \cos\phi)$, three-phase $P / (\sqrt{3} U \cos\phi)$), voltage drop $\Delta U = b \cdot (\rho_1 \frac{L}{S}\cos\phi + \lambda L \sin\phi) I_b$ with $b=2$ (1-phase) and $b=1$ (3-phase), $\rho_1 = 0.023\ \Omega\cdot\text{mm}^2/\text{m}$ ($\text{Cu}$) and $0.036\ \Omega\cdot\text{mm}^2/\text{m}$ ($\text{Al}$), $\lambda = 0.08\ \text{m}\Omega/\text{m}$ for $S > 16\text{ mm}^2$ (0 for $\le 16\text{ mm}^2$), and thermal stress $k$-factors ($115, 143, 76, 94$).

---

## 2. Logic Chain

1. **Packaging & Modular Separation**:
   - *Premise*: `ampy` needs to be both a reusable library for future network graphs/APIs and a standalone CLI tool (Observation 1, R2).
   - *Deduction*: A modern `src/` layout (`src/ampy/`) with declarative `pyproject.toml` (PEP 517/518/621) ensures clean isolation. The architecture splits code into:
     - `ampy.core.models`: Pydantic v2 domain schemas (`ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition`, `SizingResult`, etc.).
     - `ampy.core.formulas`: Pure, functional mathematical functions (`calculate_ib`, `calculate_voltage_drop`, `calculate_thermal_stress`, etc.) with zero side effects.
     - `ampy.core.tables`: Immutable normative lookup matrices for $I_0, k_1, k_2, k_3$.
     - `ampy.core.engine`: `SizingEngine` orchestrator coordinating derating, table lookups, and multi-constraint section selection.
     - `ampy.cli`: Typer CLI application, Rich terminal formatters, and YAML/JSON configuration parsers.
     - `ampy.__init__`: Clean public facade exposing core classes and functions directly.

2. **Iterative Multi-Constraint Sizing Engine**:
   - *Premise*: Conductor cross-section must simultaneously satisfy ampacity ($I_b \le I_n \le I_z$), voltage drop ($\Delta U\% \le \Delta U_{\max}\%$), and short-circuit thermal stress ($S \ge S_{\min,\text{thermal}}$) (Observation 1, R1; Observation 3).
   - *Deduction*: The `SizingEngine` executes an iterative constraint pipeline:
     1. Calculate $I_b$ from load parameters.
     2. Resolve protection rating $I_n$ (validated from user input or selected from standard ratings series $[1 \dots 630\text{ A}]$ such that $I_n \ge I_b$).
     3. Resolve derating factors $k_1, k_2, k_3, k_{\text{custom}} \implies k_{\text{total}}$.
     4. Calculate minimum required base current $I_{0,\text{required}} = I_n / k_{\text{total}}$.
     5. Scan standard sections series $[1.5, 2.5, 4 \dots 300\text{ mm}^2]$ to find candidate section where $I_0(S) \ge I_{0,\text{required}}$.
     6. Evaluate voltage drop $\Delta U$ on candidate section. If $\Delta U\% > \Delta U_{\max}\%$, increment to next standard section until compliant.
     7. If $I_k$ and $t$ are specified, evaluate thermal stress $S_{\min} = \sqrt{I_k^2 t} / k$. If candidate section $< S_{\min}$, increment section.
     8. Tag governing constraint (`Iz`, `dU`, or `thermal_stress`) and return immutable `SizingResult`.

3. **Ergonomic CLI & Serialization**:
   - *Premise*: Users require one-shot terminal commands, YAML/JSON file inputs, and formatted audit reports (Observation 1, R2).
   - *Deduction*: Typer provides dual-mode execution (direct flags vs `--config file.yaml/json`). Rich formatters generate styled summary panels, compliance badges, and detailed intermediate calculation audit tables. Pydantic v2's native `model_dump()` and `model_dump_json()` allow instant machine output (`--json` flag) and integration with external pipelines.

---

## 3. Caveats

1. **Parallel Conductor Sizing ($n \times S$)**:
   - The design specifies single-conductor circuits up to $300\text{ mm}^2$. For high-current industrial feeders requiring parallel runs (e.g. $2 \times 240\text{ mm}^2$), the engine architecture provides clear extension points, but the primary baseline focuses on single cables per phase as requested.
2. **Environment Dependencies**:
   - Host Python 3.13 has `pydantic` installed, but `typer`, `rich`, `pyyaml`, and `pytest` are absent and must be installed via `pip install -e ".[dev]"` once `pyproject.toml` is written by the implementation worker.

---

## 4. Conclusion

The software architecture and technical specification for `ampy` has been fully formulated and documented in:
`c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md`

Key deliverables designed and specified:
- Modern Python packaging (`src/ampy/`, `pyproject.toml`, PEP 561 `py.typed`).
- Strongly typed Pydantic v2 domain schemas (`ampy.core.models`).
- Pure functional mathematical core (`ampy.core.formulas`).
- Normative tables for $I_0$ and derating factors $k_1, k_2, k_3$ (`ampy.core.tables`).
- Multi-constraint `SizingEngine` orchestrator (`ampy.core.engine`).
- Rich terminal presentation and Typer CLI application (`ampy.cli`).
- Extensibility patterns for electrical network graphs and FastAPI microservices.

---

## 5. Verification Method

1. **Document Inspection**:
   - Open and inspect `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md`.
   - Verify that all 10 architectural sections are complete, code snippets are valid Python 3.10+ syntax, and mathematical equations match NF C 15-100 / UTE C 15-105.
2. **Invalidation Conditions**:
   - If voltage drop formula deviates from UTE C 15-105 §5.3 ($b \cdot (\rho_1 \frac{L}{S}\cos\phi + \lambda L \sin\phi) I_b$).
   - If protection coordination violates $I_b \le I_n \le I_z$.
   - If Pydantic schemas do not enforce exclusive load inputs (`power_kw`, `apparent_power_kva`, `current_a`).
