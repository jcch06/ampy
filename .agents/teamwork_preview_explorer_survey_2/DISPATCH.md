# DISPATCH

## 2026-09-30T13:08:08Z

You are teamwork_preview_explorer_survey_2.
Your working directory: c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2
Original request file: c:\Users\cjose\antigravity project\ampy\.agents\ORIGINAL_REQUEST.md

You MUST first read ORIGINAL_REQUEST.md.

Task:
Explore and design the software architecture, Python modular packaging, Pydantic schemas, and Typer/Rich CLI interface for the `ampy` electrical sizing calculation engine.

Investigate and document in `c:\Users\cjose\antigravity project\ampy\.agents\teamwork_preview_explorer_survey_2\architecture.md`:
1. Python project structure (modern src-layout `src/ampy/`, pyproject.toml):
   - Modular decomposition:
     - `ampy.core.models`: Pydantic v2 schemas for ElectricalLoad, CableSpecs, InstallationConditions, ProtectionDevice, SizingResult, VoltageDropResult, IntermediateFactors.
     - `ampy.core.formulas`: Pure, robust mathematical calculation functions (Ib, dU, thermal stress, cos/sin phi, power conversions).
     - `ampy.core.tables`: Normative lookup tables (I0, k1, k2, k3, standard sections) with structured Enums and typing.
     - `ampy.core.engine`: SizingEngine class orchestrating: calculate Ib -> determine derating factors k -> determine required I0 or Iz -> iterate through standard sections -> check Iz constraint -> calculate dU -> if dU > dU_max increment section until both constraints are satisfied -> check thermal stress limit -> return comprehensive SizingResult.
     - `ampy.cli.main`: Typer CLI application, CLI options/arguments, YAML/JSON config file reader, Rich terminal table formatter.
     - `ampy.__init__`: Clean top-level export API for library reuse.
2. CLI Ergonomics & User Experience:
   - Direct flags mode (e.g. `ampy size --power-kw 22 --voltage 400 --phases 3 --cos-phi 0.85 --length 60 --method C --insulation XLPE --conductor Cu --temp 35 --grouping 2 --du-max 5.0`)
   - File input mode (e.g. `ampy size --config circuit.yaml` or `circuit.json`)
   - Output styling: Rich terminal summary card and detailed intermediate calculation table.
3. Extensibility & Library Integration:
   - How `ampy` can easily be imported into future network graphs or web/desktop UIs.
   - Pydantic models serialization (to_dict, model_dump, model_dump_json).

Produce a complete, self-contained `architecture.md` and deliver your `handoff.md`. Communicate via send_message to parent when complete.
