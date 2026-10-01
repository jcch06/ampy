# E2E Test Infra: ampy

## Test Philosophy
- Opaque-box, requirement-driven derived strictly from NF C 15-100, UTE C 15-105, and user requirements.
- Independent of internal implementation design; validates inputs -> outputs and intermediate normative factors.
- Methodology: Category-Partition + Boundary Value Analysis (BVA) + Pairwise Combinatorial + Canonical UTE C 15-105 Workload Testing.

## Feature Inventory & Test Coverage Goals
| # | Feature | Requirement Source | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|-------------------|:------:|:------:|:------:|:------:|
| 1 | `F01_IB_1P` | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 2 | `F02_IB_3P` | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 3 | `F03_HARMONICS` | Normative Specs §1.3 | 5 | 3 | ✓ | - |
| 4 | `F04_VOLTAGE_DROP` | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 5 | `F05_THERMAL_STRESS` | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 6 | `F06_PYDANTIC_SCHEMAS` | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 7 | `F07_PACKAGING` | ORIGINAL_REQUEST §R2 | 3 | 2 | - | ✓ |
| 8 | `F08_INSTALL_METHODS` | ORIGINAL_REQUEST §R1 | 4 | 4 | ✓ | ✓ |
| 9 | `F09_I0_TABLES` | ORIGINAL_REQUEST §R1 | 8 | 4 | ✓ | ✓ |
| 10 | `F10_K1_FACTORS` | ORIGINAL_REQUEST §R1 | 4 | 3 | ✓ | ✓ |
| 11 | `F11_K2_FACTORS` | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 12 | `F12_K3_FACTORS` | ORIGINAL_REQUEST §R1 | 6 | 6 | ✓ | ✓ |
| 13 | `F13_IN_SERIES` | Normative Specs §5.2 | 5 | 3 | ✓ | ✓ |
| 14 | `F14_SIZING_ENGINE` | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 15 | `F15_SECTION_SELECTOR`| ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 16 | `F16_CONSTRAINTS_TAGGING` | Architecture §5 | 3 | 3 | ✓ | ✓ |
| 17 | `F17_PUBLIC_API` | ORIGINAL_REQUEST §R2 | 3 | 2 | - | ✓ |
| 18 | `F18_CLI_FLAGS` | ORIGINAL_REQUEST §R2 | 5 | 3 | - | ✓ |
| 19 | `F19_CLI_CONFIG` | ORIGINAL_REQUEST §R2 | 4 | 3 | - | ✓ |
| 20 | `F20_RICH_REPORTS` | ORIGINAL_REQUEST §R2 | 3 | 2 | - | ✓ |
| 21 | `F21_JSON_EXPORT` | ORIGINAL_REQUEST §R2 | 3 | 2 | - | ✓ |

## Test Architecture
- **Framework**: `pytest`, `pytest-cov`
- **Location**: `tests/`
  - `tests/unit/`: Isolated unit tests for pure formulas, schema validation, table lookups.
  - `tests/boundary/`: Boundary and corner cases (extreme temperatures, max sections, limit crossing).
  - `tests/combinatorial/`: 32-case pairwise matrix across all methods, materials, insulations, phases.
  - `tests/e2e/`: End-to-end integration tests, UTE C 15-105 worked benchmark scenarios, CLI tests.
- **Pass/Fail Semantics**:
  - Discrete results ($S$ mm², $I_n$ A, constraint enum, compliance bool) must match **exactly**.
  - Continuous physical variables ($\Delta U$ in V and %, $I_b$, $I_z$) must match within $\le 0.5\%$ relative tolerance.
  - Exit code 0 on all test commands.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Governing Constraint | Expected Result |
|---|----------|--------------------|---------------------|-----------------|
| `BENCH-01` | Standard 3P Motor 18.5kW (Method E, XLPE, Cu, 45m) | F02, F08, F09, F14, F15 | Ampacity ($I_z$) | $S = 4.0\text{ mm}^2$, $I_n = 32\text{ A}$, $\Delta U = 3.03\%$ |
| `BENCH-02` | 1P Commercial Lighting 3.68kW (Method B, PVC, Cu, 35m) | F01, F04, F08, F14, F15 | Voltage Drop ($\Delta U \le 3\%$) | $S = 4.0\text{ mm}^2$, $I_n = 16\text{ A}$, $\Delta U = 2.80\%$ |
| `BENCH-03` | Long-Run Feeder Pumping 37kW (Method C, XLPE, Cu, 220m) | F02, F04, F08, F14, F15 | Voltage Drop ($\Delta U \le 5\%$) | $S = 25.0\text{ mm}^2$, $I_n = 63\text{ A}$, $\Delta U = 4.95\%$ |
| `BENCH-04` | Multi-Cable Grouping N=6 touching (Method E, XLPE, Cu, 30m) | F02, F11, F09, F14, F15 | Grouping derating ($k_2=0.73$) | $S = 10.0\text{ mm}^2$, $I_n = 40\text{ A}$, $\Delta U = 0.97\%$ |
| `BENCH-05` | High Ambient Temp 50°C Plant (Method C, XLPE, Cu, 40m) | F02, F12, F09, F14, F15 | Temp derating ($k_3=0.82$) | $S = 16.0\text{ mm}^2$, $I_n = 63\text{ A}$, $\Delta U = 1.12\%$ |

## Coverage Thresholds
- **Tier 1**: ≥ 5 test cases per feature (Isolated unit tests)
- **Tier 2**: ≥ 5 test cases per feature where boundaries exist (Boundaries & edge conditions)
- **Tier 3**: ≥ 32 pairwise combination test cases
- **Tier 4**: ≥ 5 realistic UTE C 15-105 worked benchmark scenarios
- **Total Minimum**: ≥ 150 test cases with 100% pass rate
