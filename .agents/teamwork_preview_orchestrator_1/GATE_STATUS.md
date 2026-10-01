# Gate Status — teamwork_preview_orchestrator_1

## Gate — Milestone 1 (Foundation: Models & Formulas) — Iteration 1

| Agent | Role | Verdict | Source |
|-------|------|---------|--------|
| `teamwork_preview_worker_m1_1` | Packaging Models Formulas Worker | DONE (182 passed, 97% cov) | handoff.md |
| `teamwork_preview_auditor_m1_1` | Forensic Integrity Auditor | CLEAN | handoff.md |
| `teamwork_preview_reviewer_m1_1` | M1 Code & Normative Reviewer | APPROVE | handoff.md |
| `teamwork_preview_reviewer_m1_2` | M1 Architecture Quality Reviewer | REQUEST_CHANGES | handoff.md |
| `teamwork_preview_challenger_m1_1` | Formulas Precision Challenger | APPROVE | handoff.md |
| `teamwork_preview_challenger_m1_2` | Models Invalidation Challenger | CHALLENGE_FAILED | handoff.md |

Gate Result: **FAIL** (reviewer_m1_2 REQUEST_CHANGES; challenger_m1_2 CHALLENGE_FAILED)

### Issues to Remediate:
1. **Enum Hashability**: In `src/ampy/core/models.py`, `PhaseSystem` and `LimitingConstraint` defined custom `__eq__` without `__hash__`, setting `__hash__ = None`. Must add `__hash__ = lambda self: hash(self.value)` and prevent `bool` matching in `isinstance(other, int)` (`and not isinstance(other, bool)`).
2. **Infinite Float Ingress**: Add `allow_inf_nan=False` to `model_config` across all Pydantic models to prevent `float('inf')` from entering, crashing JSON roundtrip deserialization, and generating `NaN`s in formulas.
3. **Model Mutability**: Add `frozen=True` to `CircuitDefinition.model_config` to prevent post-instantiation attribute mutation.
4. **Output Schema Protection**: Add `extra="forbid"` and `allow_inf_nan=False` to `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, and `SizingResult`.
5. **String Shorthand Coercion**: Ensure `calculate_ib` and `calculate_voltage_drop` accept standard string values (`"1P"`, `"3P"`, `"DC"`) by running `PhaseSystem(system)` coercion.
6. **Material Alias**: In `calculate_thermal_stress_min_section`, ensure material strings like `"copper"`, `"aluminium"`, `"Cu"`, `"Al"` normalize smoothly.
