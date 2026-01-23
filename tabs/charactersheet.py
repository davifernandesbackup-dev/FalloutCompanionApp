import streamlit as st
import re
import json
import copy
from utils.data_manager import load_data, save_data
from constants import CHARACTERS_FILE, EQUIPMENT_FILE, PERKS_FILE
from utils.character_logic import get_default_character, sync_char_widgets, calculate_stats, roll_skill, migrate_character, SKILL_MAP
from utils.character_components import render_css, render_bars, render_database_manager, render_inventory_management, render_character_statblock, caps_manager_dialog, crafting_manager_dialog, add_db_item_dialog

def update_skills_callback():
    """Callback to update skills immediately on edit to fix desync."""
    if "skill_editor" in st.session_state:
        ed = st.session_state["skill_editor"]
        rows = ed.get("edited_rows", {})
        if not rows: return
        
        if "char_sheet" in st.session_state:
            char = st.session_state.char_sheet
            sorted_skills = sorted(list(SKILL_MAP.keys()))
            
            for idx, changes in rows.items():
                if "Others" in changes:
                    skill_name = sorted_skills[int(idx)]
                    if "skills" in char:
                        char["skills"][skill_name] = changes["Others"]

def render_character_sheet() -> None:
    st.header("📝 Character Sheet")

    # --- DATA LOADING ---
    saved_chars = load_data(CHARACTERS_FILE)
    if not isinstance(saved_chars, list):
        saved_chars = []

    # --- STATE MANAGEMENT ---
    if "char_sheet_mode" not in st.session_state:
        st.session_state.char_sheet_mode = "SELECT" # Options: SELECT, EDIT
    if "active_char_idx" not in st.session_state:
        st.session_state.active_char_idx = None
    if "char_sheet" not in st.session_state:
        st.session_state.char_sheet = {}
    if "char_sheet_view" not in st.session_state:
        st.session_state.char_sheet_view = "Statblock"

    # Apply CSS based on view mode
    # Compact mode is only for the Statblock view when editing/viewing a character
    is_statblock = (st.session_state.char_sheet_mode == "EDIT" and st.session_state.char_sheet_view == "Statblock")
    render_css(compact=is_statblock)

    # Safety check: Ensure valid state for EDIT mode
    if st.session_state.char_sheet_mode == "EDIT":
        if st.session_state.active_char_idx is None or st.session_state.active_char_idx >= len(saved_chars):
            st.session_state.char_sheet_mode = "SELECT"
            st.session_state.active_char_idx = None

    # --- VIEW: SELECTION SCREEN ---
    if st.session_state.char_sheet_mode == "SELECT":
        st.subheader("Select Character")
        
        col_new, col_space = st.columns([1, 2])
        if col_new.button("➕ Create New Character", use_container_width=True):
            new_char = get_default_character()
            saved_chars.append(new_char)
            save_data(CHARACTERS_FILE, saved_chars)
            
            # Switch to Edit Mode
            st.session_state.char_sheet = new_char
            sync_char_widgets()
            st.session_state.active_char_idx = len(saved_chars) - 1
            st.session_state.char_sheet_mode = "EDIT"
            st.session_state.char_sheet_view = "Edit"
            st.rerun()

        st.divider()

        if not saved_chars:
            st.info("No saved characters found.")
        else:
            for index, char_entry in enumerate(saved_chars):
                col_char_info, col_char_load = st.columns([4, 1])
                name_display = char_entry.get("name", "Unnamed")
                lvl_display = char_entry.get("level", 1)
                col_char_info.markdown(f"**{name_display}** (Level {lvl_display})")
                
                if col_char_load.button("Load", key=f"load_char_{index}", use_container_width=True):
                    st.session_state.char_sheet = copy.deepcopy(char_entry)
                    sync_char_widgets()
                    st.session_state.active_char_idx = index
                    st.session_state.char_sheet_mode = "EDIT"
                    st.session_state.char_sheet_view = "Statblock"
                    st.rerun()
                st.markdown("---")

    # --- VIEW: EDIT SHEET ---
    elif st.session_state.char_sheet_mode == "EDIT":
        char = st.session_state.char_sheet
        
        # --- MIGRATION CHECK ---
        migrate_character(char)

        # --- STATBLOCK VIEW ---
        if st.session_state.char_sheet_view == "Statblock":
            col_back, col_edit, col_space = st.columns([0.8, 1.2, 3])
            if col_back.button("⬅️ Back"):
                st.session_state.char_sheet_mode = "SELECT"
                st.rerun()

            if col_edit.button("✏️ Edit Character"):
                sync_char_widgets()
                st.session_state.char_sheet_view = "Edit"
                st.rerun()

            def auto_save():
                if st.session_state.active_char_idx is not None:
                    saved_chars[st.session_state.active_char_idx] = char
                    save_data(CHARACTERS_FILE, saved_chars)
            
            render_character_statblock(char, save_callback=auto_save)
            return

        # --- EDIT VIEW TOOLBAR ---
        col_back, col_view, col_save, col_export, col_delete = st.columns([0.8, 1.5, 1.2, 1.2, 0.8])
        
        if col_back.button("⬅️ Back"):
            st.session_state.char_sheet_mode = "SELECT"
            st.rerun()
            
        if col_view.button("📝 Save & View Statblock", use_container_width=True):
            if st.session_state.active_char_idx is not None and 0 <= st.session_state.active_char_idx < len(saved_chars):
                saved_chars[st.session_state.active_char_idx] = st.session_state.char_sheet
                save_data(CHARACTERS_FILE, saved_chars)
                st.toast("Character Saved!")
            
            st.session_state.char_sheet_view = "Statblock"
            st.rerun()
        
        if col_save.button("💾 Save Changes", type="primary", use_container_width=True):
            if st.session_state.active_char_idx is not None and 0 <= st.session_state.active_char_idx < len(saved_chars):
                saved_chars[st.session_state.active_char_idx] = st.session_state.char_sheet
                save_data(CHARACTERS_FILE, saved_chars)
                st.toast("Character Saved!")
            else:
                st.error("Error saving character.")
        
        # Export Button
        json_str = json.dumps(char, indent=4)
        col_export.download_button("📤 Export JSON", json_str, file_name=f"{char.get('name','char')}.json", mime="application/json", use_container_width=True)

        if col_delete.button("🗑️ Delete", use_container_width=True):
            if st.session_state.active_char_idx is not None:
                saved_chars.pop(st.session_state.active_char_idx)
                save_data(CHARACTERS_FILE, saved_chars)
                st.session_state.char_sheet_mode = "SELECT"
                st.rerun()

        # --- MAIN LAYOUT ---
        with st.container():
            # --- AUTO-CALCULATIONS (PRE-RENDER) ---
            # Level = 1 + (XP // 1000)
            current_xp = st.session_state.get("c_xp", char.get("xp", 0))
            new_level = 1 + int(current_xp / 1000)
            char["level"] = new_level
            st.session_state["c_level"] = new_level

            # ROW 1: BASIC INFO
            col_name, col_background, col_level, col_experience = st.columns(4)
            char["name"] = col_name.text_input("Name", key="c_name")
            char["background"] = col_background.text_input("Background", key="c_background")
            # Level is derived from XP, so we disable manual input or just show it
            col_level.text_input("Level", value=str(char.get("level", 1)), disabled=True, help="Derived from XP (1000 XP per level)")
            char["xp"] = col_experience.number_input("XP", min_value=0, key="c_xp")

            # ROW 2: S.P.E.C.I.A.L.
            st.markdown('<div class="section-header">S.P.E.C.I.A.L.</div>', unsafe_allow_html=True)
            cols = st.columns(7)
            stats_keys = ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]
            
            if "stats" not in char: char["stats"] = {}
            
            # --- PRE-CALCULATE FOR DISPLAY ---
            # Update base stats from session state to ensure calculation reflects current inputs
            for key in stats_keys:
                widget_key = f"stat_{key}"
                if widget_key in st.session_state:
                    char["stats"][key] = st.session_state[widget_key]

            # --- LOGIC: CALCULATE STATS ---
            effective_health_max, effective_stamina_max, effective_armor_class, effective_stats, effective_skills = calculate_stats(char)
            
            for index, key in enumerate(stats_keys):
                with cols[index]:
                    base_val = char["stats"].get(key, 5)
                    eff_val = int(effective_stats.get(key, base_val))
                    label = f"{key} [{eff_val}]" if eff_val != base_val else key
                    char["stats"][key] = st.number_input(label, min_value=1, max_value=10, step=1, key=f"stat_{key}")
            
            # Cap HP
            if char.get("hp_current", 10) > effective_health_max:
                char["hp_current"] = effective_health_max
                if "c_hp_curr" in st.session_state:
                    st.session_state["c_hp_curr"] = effective_health_max
            
            elif char.get("hp_current", 10) < 0:
                char["hp_current"] = 0
                if "c_hp_curr" in st.session_state:
                    st.session_state["c_hp_curr"] = 0

            if char.get("stamina_current", 10) > effective_stamina_max:
                char["stamina_current"] = effective_stamina_max
                if "c_stamina_curr" in st.session_state:
                    st.session_state["c_stamina_curr"] = effective_stamina_max
            
            elif char.get("stamina_current", 10) < 0:
                char["stamina_current"] = 0
                if "c_stamina_curr" in st.session_state:
                    st.session_state["c_stamina_curr"] = 0

            # ROW 3: DERIVED STATS
            st.markdown('<div class="section-header">Status</div>', unsafe_allow_html=True)
            
            # Bars Row
            col_health_bar, col_stamina_bar = st.columns(2)
            
            with col_health_bar:
                st.markdown("**Health Points**")
                # Use session state value if available to prevent desync during editing
                health_current = st.session_state.get("c_hp_curr", char.get("hp_current", 10))
                # Use Effective Max for bar calculation
                health_percent = max(0.0, min(1.0, health_current / effective_health_max)) if effective_health_max > 0 else 0.0
                
                # Custom HP Bar (Red)
                st.markdown(f"""
                <div class="stat-bar-container">
                    <div class="stat-bar-fill hp-fill" style="width: {health_percent*100}%;"></div>
                    <div class="stat-bar-text">{health_current} / {effective_health_max}</div>
                </div>
                """, unsafe_allow_html=True)
                
                col_health_max, col_health_current = st.columns(2)
                col_health_max.text_input("Max HP", value=str(effective_health_max), disabled=True, label_visibility="collapsed")
                char["hp_current"] = col_health_current.number_input("Curr HP", max_value=effective_health_max, step=1, key="c_hp_curr", label_visibility="collapsed")

            with col_stamina_bar:
                st.markdown("**Stamina**")
                # Use session state value if available to prevent desync during editing
                stamina_current = st.session_state.get("c_stamina_curr", char.get("stamina_current", 10))
                # Use Effective Max for bar calculation
                stamina_percent = max(0.0, min(1.0, stamina_current / effective_stamina_max)) if effective_stamina_max > 0 else 0.0
                
                # Custom Stamina Bar (Yellow-Green)
                st.markdown(f"""
                <div class="stat-bar-container">
                    <div class="stat-bar-fill stamina-fill" style="width: {stamina_percent*100}%;"></div>
                    <div class="stat-bar-text">{stamina_current} / {effective_stamina_max}</div>
                </div>
                """, unsafe_allow_html=True)
                
                col_stamina_max, col_stamina_current = st.columns(2)
                col_stamina_max.text_input("Max SP", value=str(effective_stamina_max), disabled=True, label_visibility="collapsed")
                char["stamina_current"] = col_stamina_current.number_input("Curr SP", max_value=effective_stamina_max, step=1, key="c_stamina_curr", label_visibility="collapsed")

            st.divider()

            # Stats Row
            # Replaced inputs with Grid for cleaner UI
            grid_html = '<div class="special-grid">'
            grid_html += f'<div class="special-box" title="Base 10 + Modifiers"><div class="special-label">AC</div><div class="special-value">{effective_armor_class}</div></div>'
            grid_html += f'<div class="special-box" title="10 + Perception Modifier"><div class="special-label">SEQ</div><div class="special-value">{char.get("combat_sequence", 0)}</div></div>'
            grid_html += f'<div class="special-box" title="Derived: AGI + 5"><div class="special-label">AP</div><div class="special-value">{char.get("action_points", 10)}</div></div>'
            grid_html += f'<div class="special-box" title="Derived: STR * 10"><div class="special-label">LOAD</div><div class="special-value">{char.get("current_load", 0)}/{char.get("carry_load", 50)}</div></div>'
            grid_html += f'<div class="special-box" title="Endurance + Level"><div class="special-label">HEAL</div><div class="special-value">{char.get("healing_rate", 0)}</div></div>'
            grid_html += f'<div class="special-box" title="12 + Perception Mod"><div class="special-label">SENSE</div><div class="special-value">{char.get("passive_sense", 0)}</div></div>'
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)

            # Conditions & Tactical Row
            st.caption("Conditions & Tactical")
            c_cond1, c_cond2, c_cond3, c_cond4, c_tac1, c_tac2, c_tac3 = st.columns(7)
            
            with c_cond1: char["fatigue"] = st.number_input("Fatigue", min_value=0, step=1, key="c_fatigue", help="-1 penalty to d20 rolls per level.")
            with c_cond2: char["exhaustion"] = st.number_input("Exhaustion", min_value=0, step=1, key="c_exhaustion", help="-1 penalty to d20 rolls per level. Requires rest.")
            with c_cond3: char["hunger"] = st.number_input("Hunger", min_value=0, step=1, key="c_hunger", help="-1 penalty to d20 rolls per level. Requires food.")
            with c_cond4: char["dehydration"] = st.number_input("Dehydration", min_value=0, step=1, key="c_dehydration", help="-1 penalty to d20 rolls per level. Requires water.")
            
            with c_tac1: char["group_sneak"] = st.number_input("Grp Sneak", step=1, key="c_group_sneak", help="Average of all players sneak skill rounded down.")
            with c_tac2: char["party_nerve"] = st.number_input("Pty Nerve", step=1, key="c_party_nerve", help="Sum of all players CHA mod, halved, rounded down.")
            
            with c_tac3: 
                st.text_input("Rad DC", value=str(char.get("radiation_dc", 0)), disabled=True, help="12 - Endurance Mod")

            st.divider()
            
            # ROW 4: SKILLS & INVENTORY
            st.markdown('<div class="section-header">Data</div>', unsafe_allow_html=True)
            col_left, col_right = st.columns([1.2, 1.8])
            
            with col_left:
                st.markdown("**Skills**")
                if "skills" not in char: char["skills"] = {}
                
                # Ensure default skills exist if missing
                default_skills = get_default_character()["skills"]
                for skill in default_skills:
                    if skill not in char["skills"]:
                        char["skills"][skill] = 0
                
                # Prepare Data for Editor
                skill_table_data = []
                for skill, stats in SKILL_MAP.items():
                    base_val = char["skills"].get(skill, 0)
                    eff_val = effective_skills.get(skill, base_val)
                    stat_str = "/".join(stats)
                    
                    skill_table_data.append({
                        "Skill": skill,
                        "Stat": stat_str,
                        "Others": base_val,
                        "Total": eff_val
                    })
                
                # Sort by Skill Name
                skill_table_data.sort(key=lambda x: x["Skill"])
                
                # Render Data Editor
                edited_skills = st.data_editor(
                    skill_table_data,
                    column_config={
                        "Skill": st.column_config.TextColumn(disabled=True),
                        "Stat": st.column_config.TextColumn(disabled=True),
                        "Total": st.column_config.NumberColumn(disabled=True, help="Effective value including stats and perks"),
                        "Others": st.column_config.NumberColumn(step=1, help="Custom value added/subtracted from skill")
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="skill_editor",
                    on_change=update_skills_callback
                )
            
            with col_right:
                # --- TRAITS ---
                st.markdown("**Traits** (Max 2)")
                render_inventory_management(char, "traits", "Perk")
                
                if len(char.get("traits", [])) < 2:
                    if st.button("➕ Add Trait", key="btn_add_trait", use_container_width=True):
                        # Reusing PERKS_FILE as a placeholder, or allows custom creation
                        add_db_item_dialog("Trait", PERKS_FILE, char, "traits", "c_traits", "trait_dlg")
                else:
                    st.caption("Trait limit reached.")
                
                st.divider()

                # --- PERKS ---
                st.markdown("**Perks**")
                render_inventory_management(char, "perks", "Perk")
                
                render_database_manager(
                    label="Perk",
                    file_path=PERKS_FILE,
                    char=char,
                    char_key="perks",
                    session_key="c_perks",
                    prefix="pk"
                )
                
                st.divider()
                st.markdown("**Inventory**")
                c_inv_head, c_craft_btn = st.columns([3, 1])
                c_inv_head.caption("Manage your equipment and items.")
                if c_craft_btn.button("🛠️ Crafting", use_container_width=True):
                    crafting_manager_dialog(char, save_callback=lambda: save_data(CHARACTERS_FILE, saved_chars))

                render_inventory_management(
                    char, "inventory", "Equipment",
                    max_load=char.get("carry_load", 0),
                    current_load=char.get("current_load", 0)
                )
                
                st.markdown("**Caps**")
                # Caps are now derived from inventory items named "Caps"
                c_caps_disp, c_caps_btn = st.columns([3, 1])
                c_caps_disp.text_input("Caps (Carried)", value=str(char.get("caps", 0)), disabled=True, label_visibility="collapsed", help="Total quantity of 'Caps' items in carried inventory.")
                if c_caps_btn.button("🪙 Manage", key="edit_btn_caps", use_container_width=True):
                    caps_manager_dialog(char)

            st.divider()
            st.markdown('<div class="section-header">Notes</div>', unsafe_allow_html=True)
            char["notes"] = st.text_area("Character Notes", height=200, key="c_notes")
