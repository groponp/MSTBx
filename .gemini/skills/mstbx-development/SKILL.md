---
name: mstbx-development
description: >-
  Provides development standards and architecture guidelines for MSTBx,
  enforcing the Waiter/Chef pattern, click commands, logging, and changelog/documentation requirements.
---

# MSTBx Development Skill

This skill enforces development standards and architecture guidelines for the Molecular Simulation ToolBox (MSTBx). It lives inside the repository at `.gemini/skills/mstbx-development/` and must be referred to whenever adding, modifying, or refactoring commands and core modules.

## 1. Waiter/Chef Architecture
*   **Waiter (CLI Wrapper)**:
    *   Located in `mstbx/commands/`.
    *   Uses the `click` library to parse command-line arguments and options.
    *   Responsible only for argument validation, user interface feedback, and delegating the main execution to the Chef.
    *   Prints standard logs using `UnixMessage` or `MSTBxLogger`.
*   **Chef (Core Logic)**:
    *   Located in `mstbx/core/`.
    *   Contains the actual computational, file parsing, molecular structure processing, and engine-specific execution logic.
    *   Should NOT contain `click` dependencies or interact directly with standard input.

## 2. Console Logging Standards
*   All terminal messages must follow the exact format:
    `[LEVEL HH:MM:SS DD/MM/YYYY] Message`
    Where `LEVEL` is one of `INFO`, `WARNING`, `ERROR`, or `SUCCESS`.
*   Use `UnixMessage` or `MSTBxLogger` to format these logs.
*   All user-facing logs and console messages MUST be written in **English**.

## 3. Geometry and Symmetries
*   Always enforce strict box symmetry (Square XY or Cubic) based on the maximum dimension of the molecule to prevent periodic boundary condition (PBC) artifacts.
*   Default padding rules:
    *   **Solution**: 18.0 Å cubic padding.
    *   **Membrane**: 25.0 Å Z-padding with square XY box.

## 4. Documentation and Examples Standard
Whenever a new command or tool is added to MSTBx:
1.  **Usage Instructions**: Add a section in the main `README.md` detailing all command-line flags and parameters.
2.  **Minitutorial**: Include a step-by-step tutorial in the `README.md` showing how to prepare the system from raw inputs to simulation configs.
3.  **Real Examples**: Use realistic validation files/scenarios (e.g. Ubiquitin, Aquaporin) with concrete command examples.
4.  **Local Scripts**: Provide template files/scripts (like `RunTest.sh`) for users to easily reproduce.

## 5. Version Releases and Changelog Rule
*   Every time a new version is released/updated:
    *   Ensure a `CHANGELOG.md` file exists in the repository root.
    *   Create a dedicated section/release entry inside `CHANGELOG.md` detailing the version number, date, and lists of "Added", "Changed", "Deprecated", "Removed", "Fixed", and "Security" changes.

## 6. Testing and Command Order Validation
*   Before committing code, finalizing workflows, or updating tutorials, you MUST execute a validation test inside the `testing/` directory.
*   Use the corresponding testing subdirectories (e.g., `testing/ubiquitin/`, `testing/1oan-pH7-resetpsf/`, `testing/aqp/`, `testing/baat/`, `testing/openmm-runner/`) and the PDBs/PSFs provided there to run the command sequences and verify they function correctly.
*   Always check the exact command order to verify that files are correctly produced and read (for example, verifying that `resetpsf` is executed prior to `topopsfgen` for glycosylated systems).
