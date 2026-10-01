# DISPATCH LOG

## 2026-09-30T13:08:20Z
Source: Parent (teamwork_preview_orchestrator_1) / User request:
Explore, catalog, and document the automated test suite design, pytest structure, official UTE C 15-105 worked benchmark scenarios, and corner cases for verifying the `ampy` calculation engine.

Investigate and document in `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_3\benchmarks.md`:
1. UTE C 15-105 Worked Benchmark Scenarios:
   - Identify concrete, realistic industrial and commercial benchmark circuits directly from or conforming to UTE C 15-105 worked examples (e.g. standard three-phase motor circuit, single-phase sub-distribution lighting circuit, long-run feeder where voltage drop dominates, multi-cable tray grouping scenario, high ambient temperature industrial plant).
   - For each benchmark scenario, provide:
     - Input parameters (P/S/I, U, phases, length, installation method, insulation, conductor material, ambient temp, grouping count, cos phi, dU_max).
     - Expected intermediate values (Ib, k1, k2, k3, total k, minimum Iz required, standard protection In).
     - Expected final results (selected cross-section S mm², calculated dU in V and %, margin).
2. 4-Tier Test Suite Architecture:
   - Tier 1: Feature coverage (isolated tests for Ib formulas, table lookups for k1/k2/k3/I0, basic sizing).
   - Tier 2: Boundary and corner cases (extreme temperatures, boundary cos phi = 1.0, very small loads, maximum 300 mm² limit, exact dU threshold crossing, zero length).
   - Tier 3: Cross-feature combinations (pairwise combinations of methods B, C, E, F with Cu/Al and PVC/XLPE and single/three phase).
   - Tier 4: Real-world benchmark scenarios (the UTE C 15-105 end-to-end acceptance tests).
3. Test framework & tools:
   - Pytest setup, test parametrization, precision tolerances (e.g. math.isclose or pytest.approx with 0.5% tolerance on dU and exact match on section mm²).
