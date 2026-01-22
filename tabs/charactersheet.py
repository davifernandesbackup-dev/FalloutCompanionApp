import streamlit as st
import re
import copy
from utils.data_manager import load_data, save_data
from constants import CHARACTERS_FILE, EQUIPMENT_FILE, PERKS_FILE
from tabs.character_logic import get_default_character, sync_char_widgets, calculate_stats, roll_skill, migrate_character, SKILL_MAP
from tabs.character_components import render_css, render_bars, render_database_manager, render_inventory_management, render_character_statblock

def render_character_sheet() -> None:
    st.header("📝 Character Sheet")

    render_css()

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

    # Safety check: Ensure valid state for EDIT mode
    if st.session_state.char_sheet_mode == "EDIT":
        if st.session_state.active_char_idx is None or st.session_state.active_char_idx >= len(saved_chars):
            st.session_state.char_sheet_mode = "SELECT"
            st.session_state.active_char_idx = None
        if "char_sheet_view" not in st.session_state:
            st.session_state.char_sheet_view = "Statblock"

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
        col_back, col_view, col_save, col_delete = st.columns([0.8, 1.5, 1.2, 0.8])
        
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
            col_name, col_origin, col_level, col_experience = st.columns(4)
            char["name"] = col_name.text_input("Name", key="c_name")
            char["origin"] = col_origin.text_input("Origin", key="c_origin")
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
                    char["stats"][key] = st.number_input(label, min_value=1, max_value=10, key=f"stat_{key}")
            
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
                health_current = char.get("hp_current", 10)
                # Use Effective Max for bar calculation
                health_percent = max(0.0, min(1.0, health_current / effective_health_max)) if effective_health_max > 0 else 0.0
                
                # Custom HP Bar (Red)
                st.markdown(f"""
                <div class="custom-bar-bg">
                    <div class="custom-bar-fill hp-fill" style="width: {health_percent*100}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                col_health_max, col_health_current = st.columns(2)
                col_health_max.text_input("Max HP", value=str(effective_health_max), disabled=True, label_visibility="collapsed")
                char["hp_current"] = col_health_current.number_input("Curr HP", max_value=effective_health_max, step=1, key="c_hp_curr", label_visibility="collapsed")

            with col_stamina_bar:
                st.markdown("**Stamina**")
                stamina_current = char.get("stamina_current", 10)
                # Use Effective Max for bar calculation
                stamina_percent = max(0.0, min(1.0, stamina_current / effective_stamina_max)) if effective_stamina_max > 0 else 0.0
                
                # Custom Stamina Bar (Yellow-Green)
                st.markdown(f"""
                <div class="custom-bar-bg">
                    <div class="custom-bar-fill stamina-fill" style="width: {stamina_percent*100}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                col_stamina_max, col_stamina_current = st.columns(2)
                col_stamina_max.text_input("Max SP", value=str(effective_stamina_max), disabled=True, label_visibility="collapsed")
                char["stamina_current"] = col_stamina_current.number_input("Curr SP", max_value=effective_stamina_max, step=1, key="c_stamina_curr", label_visibility="collapsed")

            st.divider()

            # Stats Row
            col_armor_class, col_combat_sequence, col_action_points, col_carry_load = st.columns(4)
            with col_armor_class:
                st.text_input("Armor Class", value=str(effective_armor_class), disabled=True, help="Base 10 + Modifiers")
            with col_combat_sequence:
                st.text_input("Combat Seq.", value=str(char.get("combat_sequence", 0)), disabled=True, help="Derived: PER + AGI")
            with col_action_points:
                st.text_input("Action Points", value=str(char.get("action_points", 10)), disabled=True, help="Derived: AGI + 5")
            with col_carry_load:
                st.text_input("Carry Load", value=str(char.get("carry_load", 50)), disabled=True, help="Derived: STR * 10")
            
            # ROW 4: SKILLS & INVENTORY
            st.markdown('<div class="section-header">Data</div>', unsafe_allow_html=True)
            col_left, col_right = st.columns([1, 2])
            
            with col_left:
                st.markdown("**Skills**")
                if "skills" not in char: char["skills"] = {}
                # Ensure default skills exist if missing
                default_skills = get_default_character()["skills"]
                for skill in default_skills:
                    if skill not in char["skills"]:
                        char["skills"][skill] = 0
                
                # Group skills by stat
                skills_by_stat = {k: [] for k in ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]}
                for skill, stats in SKILL_MAP.items():
                    if skill in char["skills"]:
                        # Determine governing stat
                        best_stat = stats[0]
                        if len(stats) > 1:
                            best_val = -999
                            for s in stats:
                                val = effective_stats.get(s, 5)
                                if val > best_val:
                                    best_val = val
                                    best_stat = s
                        skills_by_stat[best_stat].append(skill)

                # Render grouped skills
                for stat in ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]:
                    s_list = skills_by_stat[stat]
                    if s_list:
                        st.caption(f"--- {stat} ---")
                        for skill in sorted(s_list):
                            base_val = char["skills"].get(skill, 0)
                            eff_val = effective_skills.get(skill, base_val)
                            label = f"{skill} [{eff_val}]" if eff_val != base_val else skill
                            
                            key = f"skill_{skill}"
                            if key in st.session_state:
                                char["skills"][skill] = st.number_input(label, step=1, key=key)
                            else:
                                char["skills"][skill] = st.number_input(label, value=base_val, step=1, key=key)
            
            with col_right:
                st.markdown("**Perks & Traits**")
                render_inventory_management(char, "perks", "Perk")
                
                # --- PERK MANAGER ---
                render_database_manager(
                    label="Perk",
                    file_path=PERKS_FILE,
                    char=char,
                    char_key="perks",
                    session_key="c_perks",
                    prefix="pk"
                )
                
                st.markdown("**Inventory**")
                render_inventory_management(
                    char, "inventory", "Equipment",
                    max_load=char.get("carry_load", 0),
                    current_load=char.get("current_weight", 0)
                )
                
                st.markdown("**Caps**")
                # Caps are now derived from inventory items named "Caps"
                st.text_input("Caps (Carried)", value=str(char.get("caps", 0)), disabled=True, help="Total quantity of 'Caps' items in carried inventory.")
