import streamlit as st
import copy
from utils.data_manager import load_data, save_data
from constants import CHARACTERS_FILE

def get_default_character():
    return {
        "name": "New Character",
        "level": 1,
        "origin": "Vault Dweller",
        "xp": 0,
        "caps": 0,
        "stats": {
            "STR": 5, "PER": 5, "END": 5, "CHA": 5, "INT": 5, "AGI": 5, "LUC": 5
        },
        "skills": {
            "Athletics": 0, "Barter": 0, "Big Guns": 0, "Energy Weapons": 0, 
            "Explosives": 0, "Lockpick": 0, "Medicine": 0, "Melee Weapons": 0, 
            "Pilot": 0, "Repair": 0, "Science": 0, "Small Guns": 0, 
            "Sneak": 0, "Speech": 0, "Survival": 0, "Throwing": 0, "Unarmed": 0
        },
        "hp_max": 10, "hp_current": 10, "stamina_max": 10, "stamina_current": 10,
        "ac": 10, "combat_sequence": 0, "action_points": 10,
        "carry_weight": 150, "perks": "", "inventory": ""
    }

def sync_char_widgets():
    """Syncs session state widgets with the current character sheet data."""
    if "char_sheet" not in st.session_state:
        return
    char = st.session_state.char_sheet
    
    # Basic Info
    st.session_state["c_name"] = char.get("name", "")
    st.session_state["c_origin"] = char.get("origin", "")
    st.session_state["c_level"] = char.get("level", 1)
    st.session_state["c_xp"] = char.get("xp", 0)
    st.session_state["c_hp_curr"] = char.get("hp_current", 10)
    st.session_state["c_hp_max"] = char.get("hp_max", 10)
    st.session_state["c_stamina_curr"] = char.get("stamina_current", 10)
    st.session_state["c_stamina_max"] = char.get("stamina_max", 10)
    st.session_state["c_ac"] = char.get("ac", 10)
    st.session_state["c_caps"] = char.get("caps", 0)
    st.session_state["c_perks"] = char.get("perks", "")
    st.session_state["c_inv"] = char.get("inventory", "")
    
    for k, v in char.get("stats", {}).items():
        st.session_state[f"stat_{k}"] = v
    for k, v in char.get("skills", {}).items():
        st.session_state[f"skill_{k}"] = v

def render_character_sheet() -> None:
    st.header("📝 Character Sheet")

    # --- CSS STYLING ---
    st.markdown("""
    <style>
        .section-header {
            border-bottom: 2px solid #00b300;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 1.2em;
            font-weight: bold;
            text-transform: uppercase;
            color: #00ff00;
            text-shadow: 0 0 5px rgba(0, 255, 0, 0.5);
        }
        .stat-input input {
            text-align: center;
            font-weight: bold;
            color: #00ff00 !important;
        }
        /* Compact Inputs */
        div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input {
            padding-top: 0px;
            padding-bottom: 0px;
            height: 2.2rem;
        }
        /* Custom Progress Bar */
        .custom-bar-bg {
            background-color: #161b22;
            border: 2px solid #00b300;
            border-radius: 5px;
            width: 100%;
            height: 25px; /* Thicker */
            margin-bottom: 5px;
            overflow: hidden;
        }
        .custom-bar-fill {
            height: 100%;
            transition: width 0.5s ease-in-out;
        }
        .hp-fill { background-color: #ff3333; box-shadow: 0 0 10px #ff0000; }
        .stamina-fill { background-color: #ccff00; box-shadow: 0 0 10px #ccff00; }
    </style>
    """, unsafe_allow_html=True)

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
            for idx, char in enumerate(saved_chars):
                c1, c2 = st.columns([4, 1])
                name_display = char.get("name", "Unnamed")
                lvl_display = char.get("level", 1)
                c1.markdown(f"**{name_display}** (Level {lvl_display})")
                
                if c2.button("Load", key=f"load_char_{idx}", use_container_width=True):
                    st.session_state.char_sheet = copy.deepcopy(char)
                    sync_char_widgets()
                    st.session_state.active_char_idx = idx
                    st.session_state.char_sheet_mode = "EDIT"
                    st.rerun()
                st.markdown("---")

    # --- VIEW: EDIT SHEET ---
    elif st.session_state.char_sheet_mode == "EDIT":
        # Toolbar
        c_back, c_save, c_del = st.columns([1, 2, 1])
        
        if c_back.button("⬅️ Back"):
            st.session_state.char_sheet_mode = "SELECT"
            st.rerun()
            
        if c_save.button("💾 Save Changes", type="primary", use_container_width=True):
            if st.session_state.active_char_idx is not None and 0 <= st.session_state.active_char_idx < len(saved_chars):
                saved_chars[st.session_state.active_char_idx] = st.session_state.char_sheet
                save_data(CHARACTERS_FILE, saved_chars)
                st.toast("Character Saved!")
            else:
                st.error("Error saving character.")

        if c_del.button("🗑️ Delete"):
            if st.session_state.active_char_idx is not None:
                saved_chars.pop(st.session_state.active_char_idx)
                save_data(CHARACTERS_FILE, saved_chars)
                st.session_state.char_sheet_mode = "SELECT"
                st.rerun()
    
        char = st.session_state.char_sheet

        # --- MAIN LAYOUT ---
        with st.container():
            # --- AUTO-CALCULATIONS (PRE-RENDER) ---
            # Level = 1 + (XP // 1000)
            curr_xp = st.session_state.get("c_xp", char.get("xp", 0))
            new_level = 1 + int(curr_xp / 1000)
            char["level"] = new_level
            st.session_state["c_level"] = new_level

            # ROW 1: BASIC INFO
            c1, c2, c3, c4 = st.columns(4)
            char["name"] = c1.text_input("Name", value=char.get("name", ""), key="c_name")
            char["origin"] = c2.text_input("Origin", value=char.get("origin", ""), key="c_origin")
            # Level is derived from XP, so we disable manual input or just show it
            char["level"] = c3.number_input("Level", min_value=1, value=char.get("level", 1), key="c_level", disabled=True, help="Derived from XP (1000 XP per level)")
            char["xp"] = c4.number_input("XP", min_value=0, value=char.get("xp", 0), key="c_xp")

            # ROW 2: S.P.E.C.I.A.L.
            st.markdown('<div class="section-header">S.P.E.C.I.A.L.</div>', unsafe_allow_html=True)
            cols = st.columns(7)
            stats_keys = ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]
            
            if "stats" not in char: char["stats"] = {}
            for i, key in enumerate(stats_keys):
                with cols[i]:
                    char["stats"][key] = st.number_input(key, min_value=1, max_value=10, value=char["stats"].get(key, 5), key=f"stat_{key}")

            # --- AUTO-CALCULATIONS ---
            # Carry Weight = 150 + (STR * 10)
            char["carry_weight"] = 150 + (char["stats"].get("STR", 5) * 10)
            # Combat Sequence = PER + AGI
            char["combat_sequence"] = char["stats"].get("PER", 5) + char["stats"].get("AGI", 5)
            # Action Points = AGI + 5 (Derived from (AGI-5) + 10)
            char["action_points"] = char["stats"].get("AGI", 5) + 5

            # ROW 3: DERIVED STATS
            st.markdown('<div class="section-header">Status</div>', unsafe_allow_html=True)
            
            # Bars Row
            bar_col1, bar_col2 = st.columns(2)
            
            with bar_col1:
                st.markdown("**Health Points**")
                hp_curr = char.get("hp_current", 10)
                hp_max = char.get("hp_max", 10)
                hp_pct = max(0.0, min(1.0, hp_curr / hp_max)) if hp_max > 0 else 0.0
                
                # Custom HP Bar (Red)
                st.markdown(f"""
                <div class="custom-bar-bg">
                    <div class="custom-bar-fill hp-fill" style="width: {hp_pct*100}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                bc1, bc2 = st.columns(2)
                char["hp_current"] = bc1.number_input("Curr HP", value=hp_curr, key="c_hp_curr", label_visibility="collapsed")
                char["hp_max"] = bc2.number_input("Max HP", value=hp_max, key="c_hp_max", label_visibility="collapsed")

            with bar_col2:
                st.markdown("**Stamina**")
                stam_curr = char.get("stamina_current", 10)
                stam_max = char.get("stamina_max", 10)
                stam_pct = max(0.0, min(1.0, stam_curr / stam_max)) if stam_max > 0 else 0.0
                
                # Custom Stamina Bar (Yellow-Green)
                st.markdown(f"""
                <div class="custom-bar-bg">
                    <div class="custom-bar-fill stamina-fill" style="width: {stam_pct*100}%;"></div>
                </div>
                """, unsafe_allow_html=True)
                
                bc3, bc4 = st.columns(2)
                char["stamina_current"] = bc3.number_input("Curr SP", value=stam_curr, key="c_stamina_curr", label_visibility="collapsed")
                char["stamina_max"] = bc4.number_input("Max SP", value=stam_max, key="c_stamina_max", label_visibility="collapsed")

            st.divider()

            # Stats Row
            dc1, dc2, dc3, dc4 = st.columns(4)
            with dc1:
                char["ac"] = st.number_input("Armor Class", value=char.get("ac", 10), key="c_ac")
            with dc2:
                st.number_input("Combat Seq.", value=char.get("combat_sequence", 0), disabled=True, help="Derived: PER + AGI")
            with dc3:
                st.number_input("Action Points", value=char.get("action_points", 10), disabled=True, help="Derived: AGI + 5")
            with dc4:
                st.number_input("Carry Wgt.", value=char.get("carry_weight", 200), disabled=True, help="Derived: 150 + (STR * 10)")

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
                        
                for skill, val in char["skills"].items():
                    char["skills"][skill] = st.number_input(skill, value=val, step=1, key=f"skill_{skill}")
            
            with col_right:
                st.markdown("**Perks & Traits**")
                char["perks"] = st.text_area("Perks", value=char.get("perks", ""), height=200, key="c_perks")
                
                st.markdown("**Inventory**")
                char["inventory"] = st.text_area("Inventory", value=char.get("inventory", ""), height=300, key="c_inv")
                
                st.markdown("**Caps**")
                char["caps"] = st.number_input("Caps", min_value=0, value=char.get("caps", 0), key="c_caps")
