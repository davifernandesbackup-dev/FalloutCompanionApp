import streamlit as st
import re
import copy
from utils.data_manager import load_data, save_data
from constants import CHARACTERS_FILE, EQUIPMENT_FILE, PERKS_FILE
from tabs.character_logic import get_default_character, sync_char_widgets, calculate_stats, roll_skill, migrate_character
from tabs.character_components import render_css, render_bars, render_database_manager, render_item_manager, render_character_statblock

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
                    st.rerun()
                st.markdown("---")

    # --- VIEW: EDIT SHEET ---
    elif st.session_state.char_sheet_mode == "EDIT":
        # Toolbar
        col_back, col_mode, col_save, col_delete = st.columns([1, 1, 1.5, 1])
        
        if col_back.button("⬅️ Back"):
            st.session_state.char_sheet_mode = "SELECT"
            st.rerun()
        
        # View Mode Toggle
        view_mode = col_mode.radio("View Mode", ["Edit", "Statblock"], horizontal=True, label_visibility="collapsed")
        
        if col_save.button("💾 Save Changes", type="primary", use_container_width=True):
            if st.session_state.active_char_idx is not None and 0 <= st.session_state.active_char_idx < len(saved_chars):
                saved_chars[st.session_state.active_char_idx] = st.session_state.char_sheet
                save_data(CHARACTERS_FILE, saved_chars)
                st.toast("Character Saved!")
            else:
                st.error("Error saving character.")

        if col_delete.button("🗑️ Delete"):
            if st.session_state.active_char_idx is not None:
                saved_chars.pop(st.session_state.active_char_idx)
                save_data(CHARACTERS_FILE, saved_chars)
                st.session_state.char_sheet_mode = "SELECT"
                st.rerun()
    
        char = st.session_state.char_sheet
        
        # --- MIGRATION CHECK ---
        migrate_character(char)

        # --- STATBLOCK VIEW ---
        if view_mode == "Statblock":
            calculate_stats(char) # Ensure stats are up to date
            render_character_statblock(char)
            return

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
            for index, key in enumerate(stats_keys):
                with cols[index]:
                    char["stats"][key] = st.number_input(key, min_value=1, max_value=10, key=f"stat_{key}")

            # --- LOGIC: CALCULATE STATS ---
            effective_health_max, effective_stamina_max, effective_armor_class, effective_stats = calculate_stats(char)
            
            # Sync Current HP/SP from Session State to Char (to handle lag before widget render)
            if "c_hp_curr" in st.session_state:
                char["hp_current"] = st.session_state["c_hp_curr"]
            if "c_stamina_curr" in st.session_state:
                char["stamina_current"] = st.session_state["c_stamina_curr"]

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
                col_health_max.text_input("Max HP", value=str(effective_health_max), disabled=True, key="c_hp_max_disp", label_visibility="collapsed")
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
                col_stamina_max.text_input("Max SP", value=str(effective_stamina_max), disabled=True, key="c_stamina_max_disp", label_visibility="collapsed")
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
                
                # Iterate over sorted default keys to ensure only valid skills are shown
                for skill in sorted(default_skills.keys()):
                    skill_value = char["skills"].get(skill, 0)
                    char["skills"][skill] = st.number_input(skill, step=1, key=f"skill_{skill}")
            
            # Prepare target options for modifiers (used in Perk/Equipment creators)
            mod_categories = {
                "S.P.E.C.I.A.L.": ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"],
                "Skills": sorted(get_default_character()["skills"].keys()),
                "Derived Stats": ["Max HP", "Max SP", "Armor Class", "Carry Load", "Combat Sequence", "Action Points"]
            }
            operator_map = {"Add": "+", "Subtract": "-", "Multiply": "*", "Divide": "/"}

            with col_right:
                st.markdown("**Perks & Traits**")
                render_item_manager(char, "perks", "Perk")
                
                # --- PERK MANAGER ---
                with st.expander("➕ Add Perk"):
                    perk_data = load_data(PERKS_FILE)
                    if not isinstance(perk_data, list):
                        perk_data = []
                    
                    # Sort by name
                    perk_data.sort(key=lambda x: x.get("name", ""))
                    
                    perk_names = [p.get("name", "Unknown") for p in perk_data]
                    selected_perk = st.selectbox("Database Perk:", [""] + perk_names, key="perk_select")
                    
                    if st.button("Add to Perks", key="btn_add_perk"):
                        if selected_perk:
                            # Find perk data
                            perk_entry = next((p for p in perk_data if p["name"] == selected_perk), None)
                            description = f" ({perk_entry['description']})" if perk_entry and perk_entry.get("description") else ""
                            line_item = f"- {selected_perk}{description}"
                            
                            current_perks = st.session_state.get("c_perks", "")
                            if current_perks:
                                new_perks = current_perks + "\n" + line_item
                            else:
                                new_perks = line_item
                            
                            st.session_state["c_perks"] = new_perks
                            char["perks"] = new_perks 
                            st.rerun()

                    st.markdown("---")
                    st.caption("Create New Perk")
                    new_perk_name = st.text_input("Name", key="new_pk_name")
                    new_perk_description = st.text_input("Description", key="new_pk_desc")
                    
                    # Modifier Builder
                    if "new_perk_modifiers" not in st.session_state: st.session_state.new_perk_modifiers = []
                    
                    col_perk_category, col_perk_stat, col_perk_operator, col_perk_value, col_perk_button = st.columns([1.5, 1.5, 1.2, 1, 0.8])
                    
                    perk_category_selected = col_perk_category.selectbox("Category", list(mod_categories.keys()), key="pk_mod_cat")
                    perk_modifier_target = col_perk_stat.selectbox("Stat", mod_categories[perk_category_selected], key="pk_mod_target")
                    perk_operator_selected = col_perk_operator.selectbox("Op", list(operator_map.keys()), key="pk_mod_op")
                    perk_modifier_value = col_perk_value.number_input("Val", value=1.0, step=0.5, key="pk_mod_val")
                    
                    if col_perk_button.button("Add", key="btn_add_pk_mod"):
                        value_formatted = int(perk_modifier_value) if perk_modifier_value.is_integer() else perk_modifier_value
                        st.session_state.new_perk_modifiers.append(f"{{{perk_modifier_target} {operator_map[perk_operator_selected]}{value_formatted}}}")
                    
                    if st.session_state.new_perk_modifiers:
                        st.markdown(" ".join([f"`{m}`" for m in st.session_state.new_perk_modifiers]))
                        if st.button("Clear Modifiers", key="btn_clear_pk_mods"):
                            st.session_state.new_perk_modifiers = []
                            st.rerun()
                    
                    if st.button("Save to Database", key="btn_save_perk"):
                        if new_perk_name:
                            final_description = new_perk_description + (" " + " ".join(st.session_state.new_perk_modifiers) if st.session_state.new_perk_modifiers else "")
                            if not any(p['name'] == new_perk_name for p in perk_data):
                                perk_data.append({"name": new_perk_name, "description": final_description.strip()})
                                save_data(PERKS_FILE, perk_data)
                                st.success(f"Created {new_perk_name}")
                                st.session_state.new_perk_modifiers = []
                                st.rerun()
                            else:
                                st.warning("Perk already exists.")
                
                st.markdown("**Inventory**")
                render_item_manager(char, "inventory", "Equipment")
                
                # --- EQUIPMENT MANAGER ---
                render_database_manager(
                    label="Equipment",
                    file_path=EQUIPMENT_FILE,
                    char=char,
                    char_key="inventory",
                    session_key="c_inv_db",
                    prefix="eq"
                )
                
                st.markdown("**Caps**")
                char["caps"] = st.number_input("Caps", min_value=0, key="c_caps")
