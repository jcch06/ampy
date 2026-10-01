## 2026-09-30T13:45:40Z
You are teamwork_preview_explorer_m1_fix_1.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_1
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md
Project plan: c:\Users\cjose\antigravity project\ampy\PROJECT.md
Reviewer 2 feedback: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_reviewer_m1_2\handoff.md
Challenger 2 feedback: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_challenger_m1_2\handoff.md

You MUST first read ORIGINAL_REQUEST.md, PROJECT.md, and the feedback from Reviewer 2 and Challenger 2.

Task:
Formulate an exact, comprehensive remediation specification for `src/ampy/core/models.py`:
1. Fix Enum Hashability in `PhaseSystem` and `LimitingConstraint`:
   - Either remove the custom `__eq__` (letting `str, Enum` default to hashable exact equality), OR provide an explicit `__hash__(self) -> int: return hash(self.value)` and guard `isinstance(other, int) and not isinstance(other, bool)`. Verify that `hash(PhaseSystem.SINGLE_PHASE)` and `{PhaseSystem.SINGLE_PHASE: 1}` work without error.
2. Prevent non-finite numbers (Inf, "inf", "Infinity"):
   - Add `allow_inf_nan=False` to `model_config` across all input and output schemas (`ElectricalLoad`, `CableSpecs`, `InstallationConditions`, `ProtectionDevice`, `CircuitDefinition`, `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, `SizingResult`).
3. Ensure immutability on `CircuitDefinition`:
   - Add `frozen=True` to `CircuitDefinition.model_config` so in-place mutation post-validation is strictly forbidden.
4. Add `extra="forbid"` to output schemas:
   - In `IntermediateFactors`, `VoltageDropResult`, `ThermalStressResult`, and `SizingResult`.
5. Verify against `tests/adversarial_challenge_models.py` (which currently has 18 failures) to ensure the proposed fixes resolve all 18 failures.

Write your plan to `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_m1_fix_1\models_fix_plan.md` and deliver `handoff.md`. Communicate via send_message to parent when complete.
