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

## Completed (All completed entries should be in UTC Brasilia time and reflect the time it being written)
### Features
- [x] (2026-01-21 19:45) **Encounter Editor**: Allow manual editing (add/remove/quantity) of generated encounters and crafting from scratch.
- [x] (2026-01-21 20:30) **Statblock Popouts**: Added modal dialogs and detached window support for viewing creature stats.
- [x] (2026-01-21 21:30) **Character Sheet**: Added a dedicated player character sheet tab with S.P.E.C.I.A.L. stats, skills, and inventory management.
- [x] (2026-01-21 22:15) **Derived Stats**: Implemented automatic calculation for Level, Carry Weight, Combat Sequence, and Action Points in the Character Sheet.
- [x] (2026-01-22 11:15) **Equipment Manager**: Added a database-backed equipment selector to the Character Sheet for adding custom items to inventory.
- [x] (2026-01-22 11:15) **Dynamic Modifiers**: Implemented a parsing system for Perks/Inventory to modify stats (e.g., `{STR +1}`) with non-stacking logic applied to base values.
- [x] (2026-01-22 11:15) **Stat Updates**: Replaced Carry Weight with Carry Load (`STR * 10`) and updated the skill list to the new standard.
- [x] (2026-01-22 11:15) **Item Management**: Converted Inventory and Perks to interactive objects with Equip/Edit/Delete controls.
- [x] (2026-01-22 11:15) **Data Migration**: Added auto-migration for legacy character data to the new object structure.
- [x] (2026-01-22 11:15) **General Database Editor**: Created a unified, modular editor for Encounters, Bestiary, Items, and Characters.
- [x] (2026-01-22 11:15) **Character Statblock**: Implemented an interactive, CSS-styled statblock view for characters with `st.fragment` for smooth updates.
- [x] (2026-01-22 11:15) **Skill Logic & Grouping**: Implemented complex skill derivation (associated stats, Luck bonus) and grouped display by governing stat.
- [x] (2026-01-22 11:15) **Load System**: Updated weight to Load (1 decimal) and added Caps weight calculation.
- [x] (2026-01-22 11:15) **Modifier Builder**: Added a UI tool for generating stat modifiers (e.g., `{STR +1}`) in item/perk editors.

### Refactoring
- [x] (2026-01-21 19:27) **Centralize Data Loading**: `load_data` is defined in both `bestiary.py` and `encounters.py`. It should be moved to a shared utility (e.g., `tabs/utils/data_manager.py`) to avoid duplication and manage caching better.
- [x] (2026-01-21 19:27) **Split Encounters Module**: `tabs/encounters.py` is handling Scanner, Editor, and Logs. Split into separate sub-modules (e.g., `tabs/encounters/scanner.py`) to reduce file size and complexity.
- [x] (2026-01-21 19:27) **Shared Dice Utility**: Move `roll_dice` logic from `encounters.py` to a shared utility (e.g., `tabs/utils/dice.py`) to facilitate the "Dice Roller" feature.
- [x] (2026-01-21 19:27) **Constants**: Move file paths (`data/*.json`) to a central configuration file or constants module.
- [x] (2026-01-21 19:27) **File Hierarchy Refactor**: Moved `utils` package and `constants.py` out of `tabs/` to the root level for better project structure.
- [x] (2026-01-21 19:35) **Type Hinting**: Add Python type hints to functions (e.g., `def generate_pool(items: list, target_budget: int) -> dict:`) for better maintainability.
- [x] (2026-01-21 22:45) **Documentation**: Updated README.md with project structure and added requirements.txt for deployment.

### Bug Fixes / Robustness
- [x] (2026-01-21 19:27) **UI Fix**: Fixed `render_statblock` to correctly nest "Raw Data" and other elements inside the passed container.
- [x] (2026-01-21 22:00) **Character Sheet State**: Fixed an issue where the character sheet could get stuck in edit mode with a default character due to session state persistence.
- [x] (2026-01-21 22:40) **Input Sync**: Fixed synchronization issues with character sheet inputs and session state to ensure reliable updates.
- [x] (2026-01-22 00:00) **Character Sheet Polish**: Fixed widget warnings by removing redundant default values and enforced integer precision for HP/SP/AC inputs.
- [x] (2026-01-22 01:30) **Component Extraction**: Extracted character sheet logic and UI components into `tabs/character_logic.py` and `tabs/character_components.py`.

### UI/UX
- [x] (2026-01-21 19:27) **Navigation Refactor**: Switched from top-level tabs to a sidebar for better navigation hierarchy.
- [x] (2026-01-21 20:30) **Encounter Builder Overhaul**: Refactored Scanner to use a 5e.tools-style 2-column layout with library search and granular controls.
- [x] (2026-01-21 20:30) **Statblock Redesign**: Updated statblock visualization with custom HTML/CSS to match the Fallout terminal aesthetic.
- [x] (2026-01-21 20:45) **Library Mobile Layout**: Tuned column widths and removed full-width buttons in the Encounter Builder library for a more compact mobile view.
- [x] (2026-01-21 20:50) **Library Alignment**: Fixed vertical alignment of buttons in the Encounter Builder library to be centered with item names.
- [x] (2026-01-21 22:30) **Character Sheet UI**: Added custom styled HP/Stamina bars and optimized layout for compactness.
- [x] (2026-01-22 15:23) **Inventory Nesting UI**: Refactored inventory display to use nested expanders for containers.



## Notes
# Use this file to track progress.
# Format for completed items: - [x] (YYYY-MM-DD HH:MM) **Task Name**...
# Timezone: Brasilia Time (UTC-3)