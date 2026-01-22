# FalloutApp To-Do List

## Refactoring

## Features
- [ ] **Dice Roller**: Add a generic dice roller utility tab for ad-hoc rolls.
- [ ] **Export**: Allow exporting saved encounters to a text or Markdown file for printing.
- [ ] **Fuzzy Search**: Improve the Bestiary search to handle typos or partial matches better.

## Bug Fixes / Robustness
- [ ] **JSON Error Handling**: Add `try-except` blocks around `json.load` to handle corrupted files gracefully.
- [ ] **Input Validation**: Validate dice notation regex in the Editor before saving to prevent crashes during generation.

## UI/UX
- [ ] **Persistent State**: Ensure scanner results persist when switching tabs without saving (currently relies on `st.session_state` but could be more robust).
- [ ] **Mobile Layout**: Tune column widths for better mobile viewing.

## Completed
### Features
- [x] (2026-01-21 19:45) **Encounter Editor**: Allow manual editing (add/remove/quantity) of generated encounters and crafting from scratch.
- [x] (2026-01-21 20:30) **Statblock Popouts**: Added modal dialogs and detached window support for viewing creature stats.
- [x] (2026-01-21 21:30) **Character Sheet**: Added a dedicated player character sheet tab with S.P.E.C.I.A.L. stats, skills, and inventory management.

### Refactoring
- [x] (2026-01-21 19:27) **Centralize Data Loading**: `load_data` is defined in both `bestiary.py` and `encounters.py`. It should be moved to a shared utility (e.g., `tabs/utils/data_manager.py`) to avoid duplication and manage caching better.
- [x] (2026-01-21 19:27) **Split Encounters Module**: `tabs/encounters.py` is handling Scanner, Editor, and Logs. Split into separate sub-modules (e.g., `tabs/encounters/scanner.py`) to reduce file size and complexity.
- [x] (2026-01-21 19:27) **Shared Dice Utility**: Move `roll_dice` logic from `encounters.py` to a shared utility (e.g., `tabs/utils/dice.py`) to facilitate the "Dice Roller" feature.
- [x] (2026-01-21 19:27) **Constants**: Move file paths (`data/*.json`) to a central configuration file or constants module.
- [x] (2026-01-21 19:27) **File Hierarchy Refactor**: Moved `utils` package and `constants.py` out of `tabs/` to the root level for better project structure.
- [x] (2026-01-21 19:35) **Type Hinting**: Add Python type hints to functions (e.g., `def generate_pool(items: list, target_budget: int) -> dict:`) for better maintainability.

### Bug Fixes / Robustness
- [x] (2026-01-21 19:27) **UI Fix**: Fixed `render_statblock` to correctly nest "Raw Data" and other elements inside the passed container.
- [x] (2026-01-21 22:00) **Character Sheet State**: Fixed an issue where the character sheet could get stuck in edit mode with a default character due to session state persistence.

### UI/UX
- [x] (2026-01-21 19:27) **Navigation Refactor**: Switched from top-level tabs to a sidebar for better navigation hierarchy.
- [x] (2026-01-21 20:30) **Encounter Builder Overhaul**: Refactored Scanner to use a 5e.tools-style 2-column layout with library search and granular controls.
- [x] (2026-01-21 20:30) **Statblock Redesign**: Updated statblock visualization with custom HTML/CSS to match the Fallout terminal aesthetic.
- [x] (2026-01-21 20:45) **Library Mobile Layout**: Tuned column widths and removed full-width buttons in the Encounter Builder library for a more compact mobile view.
- [x] (2026-01-21 20:50) **Library Alignment**: Fixed vertical alignment of buttons in the Encounter Builder library to be centered with item names.



## Notes
# Use this file to track progress.
# Format for completed items: - [x] (YYYY-MM-DD HH:MM) **Task Name**...
# Timezone: Brasilia Time (UTC-3)