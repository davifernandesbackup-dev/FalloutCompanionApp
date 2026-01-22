import streamlit as st
import re
from utils.data_manager import load_data, save_data
from tabs.character_logic import get_default_character, calculate_stats, SKILL_MAP
from constants import EQUIPMENT_FILE

def render_css():
    st.markdown("""
    <style>
        /* Global Font & Colors */
        .stApp {
            font-family: "Source Sans Pro", sans-serif;
            background-color: #0d1117;
            color: #00b300;
        }

        .section-header {
            border-bottom: 1px solid #00b300;
            margin-top: 12px;
            margin-bottom: 6px;
            font-size: 1.1em;
            font-weight: bold;
            text-transform: uppercase;
            color: #00ff00;
            text-shadow: 0 0 5px rgba(0, 255, 0, 0.7);
        }

        /* Input Styling to match Terminal */
        .stat-input input {
            text-align: center;
            font-weight: bold;
            color: #00ff00 !important;
        }
        
        div[data-testid="stNumberInput"] input, 
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            color: #00ff00 !important;
            background-color: rgba(13, 17, 23, 0.9) !important;
            border: 1px solid #00b300 !important;
            border-radius: 4px;
            box-shadow: 0 0 5px rgba(0, 255, 0, 0.2);
            -webkit-text-fill-color: #00ff00 !important;
        }
        
        div[data-testid="stSelectbox"] > div > div {
            background-color: rgba(13, 17, 23, 0.9) !important;
            color: #00ff00 !important;
            border: 1px solid #00b300 !important;
            box-shadow: 0 0 5px rgba(0, 255, 0, 0.2);
        }

        .custom-bar-bg {
            background-color: rgba(13, 17, 23, 0.9);
            border: 2px solid #00b300;
            border-radius: 6px;
            width: 100%;
            height: 25px;
            margin-bottom: 5px;
            overflow: hidden;
            box-shadow: 0 0 8px rgba(0, 255, 0, 0.3);
        }
        .custom-bar-fill {
            height: 100%;
            transition: width 0.5s ease-in-out;
        }
        .hp-fill { background-color: #ff3333; box-shadow: 0 0 10px #ff0000; }
        .stamina-fill { background-color: #ccff00; box-shadow: 0 0 10px #ccff00; }
        .roll-btn {
            padding: 0px 5px;
            font-size: 0.8em;
            margin-left: 5px;
        }
        .item-row {
            background-color: rgba(0, 179, 0, 0.1);
            border-left: 3px solid #00b300;
            border-radius: 0 4px 4px 0;
            padding: 8px;
            margin-bottom: 6px;
            color: #e6fffa;
        }

        /* Button Styling */
        .stButton > button {
            background-color: rgba(13, 17, 23, 0.9);
            color: #00b300;
            border: 1px solid #00b300;
            text-transform: uppercase;
            font-weight: bold;
            transition: all 0.2s;
        }
        .stButton > button:hover {
            background-color: #00b300;
            color: #0d1117;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
        }

        /* CRT SCANLINE EFFECT */
        .scanlines {
            background: linear-gradient(
                to bottom,
                rgba(255,255,255,0),
                rgba(255,255,255,0) 50%,
                rgba(0,0,0,0.2) 50%,
                rgba(0,0,0,0.2)
            );
            background-size: 100% 4px;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 9999;
            opacity: 0.3;
        }

        /* STATBLOCK STYLING */
        /* Target the st.container(border=True) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid #00b300 !important;
            border-radius: 8px;
            background-color: rgba(13, 17, 23, 0.9) !important;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.2) !important;
            padding: 15px !important;
        }
        .statblock-header {
            border-bottom: 2px solid #00b300;
            margin-bottom: 10px;
            padding-bottom: 5px;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }
        .statblock-title {
            font-size: 1.4em;
            font-weight: bold;
            color: #00ff00;
            text-transform: uppercase;
            text-shadow: 0 0 5px rgba(0, 255, 0, 0.7);
        }
        .statblock-meta {
            font-style: italic;
            color: #00cc00;
            font-size: 0.9em;
        }
        .special-grid {
            display: flex;
            width: 100%;
            border: 2px solid #00b300;
            border-radius: 6px;
            overflow: hidden;
            margin: 10px 0;
        }
        .special-box {
            text-align: center;
            flex: 1;
            border-right: 1px solid #00b300;
            background-color: #0d1117;
        }
        .special-box:last-child {
            border-right: none;
        }
        .special-label {
            background-color: #00b300;
            color: #0d1117;
            font-weight: bold;
            font-size: 0.75em;
            padding: 2px 0;
            text-shadow: none;
        }
        .special-value {
            font-size: 1.1em;
            font-weight: bold;
            padding: 4px 0;
            color: #00ff00;
        }
        .derived-row {
            display: flex;
            justify-content: space-around;
            background-color: rgba(0, 179, 0, 0.15);
            padding: 6px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-weight: bold;
            color: #e6fffa;
        }
        .attack-row {
            margin-bottom: 6px;
            padding-left: 8px;
            border-left: 3px solid #00b300;
            background-color: rgba(0, 179, 0, 0.05);
        }
    </style>
    <div class="scanlines"></div>
    """, unsafe_allow_html=True)

def render_bars(char, effective_health_max, effective_stamina_max):
    col_health_bar, col_stamina_bar = st.columns(2)
    
    with col_health_bar:
        st.markdown("**Health Points**")
        health_current = char.get("hp_current", 10)
        health_percent = max(0.0, min(1.0, health_current / effective_health_max)) if effective_health_max > 0 else 0.0
        
        st.markdown(f"""
        <div class="custom-bar-bg">
            <div class="custom-bar-fill hp-fill" style="width: {health_percent*100}%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        col_health_max, col_health_current = st.columns(2)
        col_health_max.text_input("Max HP", value=str(effective_health_max), disabled=True, label_visibility="collapsed")
        char["hp_current"] = col_health_current.number_input("Curr HP", min_value=0, max_value=effective_health_max, step=1, key="c_hp_curr", label_visibility="collapsed")

    with col_stamina_bar:
        st.markdown("**Stamina**")
        stamina_current = char.get("stamina_current", 10)
        stamina_percent = max(0.0, min(1.0, stamina_current / effective_stamina_max)) if effective_stamina_max > 0 else 0.0
        
        st.markdown(f"""
        <div class="custom-bar-bg">
            <div class="custom-bar-fill stamina-fill" style="width: {stamina_percent*100}%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        col_stamina_max, col_stamina_current = st.columns(2)
        col_stamina_max.text_input("Max SP", value=str(effective_stamina_max), disabled=True, label_visibility="collapsed")
        char["stamina_current"] = col_stamina_current.number_input("Curr SP", min_value=0, max_value=effective_stamina_max, step=1, key="c_stamina_curr", label_visibility="collapsed")

@st.dialog("Edit Item")
def edit_item_dialog(item, item_id, callback):
    """Dialog to edit an item's name, description, weight, and modifiers."""
    # Generate a unique key for this dialog session based on item ID
    dialog_id = f"edit_dialog_{item_id}"
    
    # Signature to detect item swaps on same ID (e.g. index reuse)
    current_sig = f"{item.get('name')}|{item.get('description')}|{item.get('weight', 0)}"
    sig_key = f"{dialog_id}_sig"
    
    # Initialize session state for this item if not already done
    if f"{dialog_id}_initialized" not in st.session_state or st.session_state.get(sig_key) != current_sig:
        desc = item.get("description", "")
        
        # Extract modifiers using regex
        pattern = r"\{([a-zA-Z0-9\s]+?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)\}"
        mods = re.findall(pattern, desc)
        mod_strings = [f"{{{m[0]} {m[1]}{m[2]}}}" for m in mods]
        
        # Clean description (remove modifiers)
        clean_desc = re.sub(pattern, "", desc).strip()
        clean_desc = re.sub(r"\s+", " ", clean_desc)
        
        st.session_state[f"{dialog_id}_name"] = item.get("name", "")
        st.session_state[f"{dialog_id}_desc"] = clean_desc
        st.session_state[f"{dialog_id}_weight"] = float(item.get("weight", 0.0))
        st.session_state[f"{dialog_id}_mods"] = mod_strings
        st.session_state[f"{dialog_id}_initialized"] = True
        st.session_state[sig_key] = current_sig

    # UI Inputs
    new_name = st.text_input("Name", key=f"{dialog_id}_name_input", value=st.session_state[f"{dialog_id}_name"])
    
    # Show Weight input if the item has a weight key (Equipment)
    if "weight" in item:
        new_weight = st.number_input("Load", min_value=0.0, step=0.1, key=f"{dialog_id}_weight_input", value=st.session_state[f"{dialog_id}_weight"])
    else:
        new_weight = 0.0

    new_desc = st.text_input("Description", key=f"{dialog_id}_desc_input", value=st.session_state[f"{dialog_id}_desc"])
    
    st.markdown("**Modifiers**")
    
    # Add new modifiers (Builder first to ensure list updates immediately)
    mods_key = f"{dialog_id}_mods"
    render_modifier_builder(dialog_id, mods_key)
    
    # List existing modifiers with delete option
    if st.session_state[mods_key]:
        for i, mod in enumerate(st.session_state[mods_key]):
            row = st.empty()
            with row.container():
                c1, c2 = st.columns([4, 1])
                c1.code(mod)
                if c2.button("🗑️", key=f"{dialog_id}_del_mod_{i}"):
                    st.session_state[mods_key].pop(i)
                    row.empty()
    else:
        st.caption("No modifiers.")

    st.divider()
    
    if st.button("💾 Save Changes", type="primary"):
        # Reconstruct description
        final_desc = new_desc
        if st.session_state[mods_key]:
            final_desc += " " + " ".join(st.session_state[mods_key])
        
        # Update item
        item["name"] = new_name
        item["description"] = final_desc.strip()
        if "weight" in item:
            item["weight"] = new_weight
            
        # Cleanup session state
        del st.session_state[f"{dialog_id}_initialized"]
        for key in list(st.session_state.keys()):
            if key.startswith(dialog_id):
                del st.session_state[key]
                
        if callback:
            callback()
        st.rerun()

def render_modifier_builder(key_prefix, mod_list_key):
    """Renders the UI for adding stat modifiers."""
    mod_categories = {
        "S.P.E.C.I.A.L.": ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"],
        "Skills": sorted(get_default_character()["skills"].keys()),
        "Derived Stats": ["Max HP", "Max SP", "Armor Class", "Carry Load", "Combat Sequence", "Action Points"]
    }
    operator_map = {"Add": "+", "Subtract": "-", "Multiply": "*", "Divide": "/"}

    c_cat, c_stat, c_op, c_val, c_btn = st.columns([1.5, 1.5, 1.2, 1, 0.8])
    cat_sel = c_cat.selectbox("Category", list(mod_categories.keys()), key=f"{key_prefix}_mod_cat")
    stat_sel = c_stat.selectbox("Stat", mod_categories[cat_sel], key=f"{key_prefix}_mod_target")
    op_sel = c_op.selectbox("Op", list(operator_map.keys()), key=f"{key_prefix}_mod_op")
    val_in = c_val.number_input("Val", value=1.0, step=0.5, key=f"{key_prefix}_mod_val")
    
    if c_btn.button("Add", key=f"{key_prefix}_btn_add_mod"):
        val_fmt = int(val_in) if val_in.is_integer() else val_in
        if mod_list_key not in st.session_state: st.session_state[mod_list_key] = []
        st.session_state[mod_list_key].append(f"{{{stat_sel} {operator_map[op_sel]}{val_fmt}}}")

def render_database_manager(label, file_path, char, char_key, session_key, prefix):
    with st.expander(f"➕ Add {label}"):
        data_list = load_data(file_path)
        if not isinstance(data_list, list):
            data_list = []
        
        data_list.sort(key=lambda x: x.get("name", ""))
        names = [e.get("name", "Unknown") for e in data_list]
        st.selectbox(f"Database {label}:", [""] + names, key=f"{prefix}_select")
        
        def add_db_item():
            selected_item = st.session_state.get(f"{prefix}_select")
            if selected_item:
                entry = next((e for e in data_list if e["name"] == selected_item), None)
                description = f" ({entry['description']})" if entry and entry.get("description") else ""
                
                new_item = {
                    "name": selected_item,
                    "description": entry.get("description", "") if entry else "",
                    "weight": entry.get("weight", 0.0) if entry else 0.0,
                    "equipped": False if label == "Equipment" else True,
                    "active": True
                }
                
                if char_key not in char or not isinstance(char[char_key], list):
                    char[char_key] = []
                
                char[char_key].append(new_item)
                st.session_state[session_key] = char[char_key]

        st.button(f"Add to {label}", key=f"{prefix}_btn_add", on_click=add_db_item)

        st.markdown("---")
        st.caption(f"Create New {label}")
        c1, c2 = st.columns([2, 1])
        new_name = c1.text_input("Name", key=f"{prefix}_new_name")
        new_weight = 0.0
        if label == "Equipment":
            new_weight = c2.number_input("Weight", min_value=0.0, step=0.1, key=f"{prefix}_new_weight")
        new_desc = st.text_input("Description", key=f"{prefix}_new_desc")
        
        # Modifier Builder
        mod_key = f"{prefix}_modifiers"
        if mod_key not in st.session_state: st.session_state[mod_key] = []
        render_modifier_builder(prefix, mod_key)

        if st.session_state[mod_key]:
            st.markdown(" ".join([f"`{m}`" for m in st.session_state[mod_key]]))
            if st.button("Clear Modifiers", key=f"{prefix}_btn_clear_mods"):
                st.session_state[mod_key] = []
                st.rerun()
        
        c_local, c_db = st.columns(2)
        
        def get_new_item_data():
            final_desc = new_desc + (" " + " ".join(st.session_state[mod_key]) if st.session_state[mod_key] else "")
            return {
                "name": new_name,
                "description": final_desc.strip(),
                "weight": new_weight if label == "Equipment" else 0.0,
                "equipped": False if label == "Equipment" else True,
                "active": True
            }

        if c_local.button("Add to Character Only", key=f"{prefix}_btn_add_local"):
            if new_name:
                item_data = get_new_item_data()
                if char_key not in char or not isinstance(char[char_key], list):
                    char[char_key] = []
                char[char_key].append(item_data)
                st.session_state[mod_key] = []
                st.success(f"Added {new_name} to Character")
                st.rerun()

        if c_db.button("Save to DB & Add", key=f"{prefix}_btn_save_db"):
            if new_name:
                item_data = get_new_item_data()
                
                # Add to Char
                if char_key not in char or not isinstance(char[char_key], list):
                    char[char_key] = []
                char[char_key].append(item_data)

                # Add to DB
                db_entry = {k: v for k, v in item_data.items() if k not in ["equipped", "active"]}
                if not any(e['name'] == new_name for e in data_list):
                    data_list.append(db_entry)
                    save_data(file_path, data_list)
                    st.success(f"Added {new_name} to Database & Character")
                else:
                    st.warning(f"Item {new_name} already in database (Added to Character only)")
                
                st.session_state[mod_key] = []
                st.rerun()

def render_item_manager(char, key, label):
    """Renders a list of items (Perks or Inventory) with Edit/Delete/Toggle controls."""
    items = char.get(key, [])
    if not isinstance(items, list):
        items = []
        char[key] = items

    # Column Headers
    h1, h2, h3 = st.columns([1, 4, 2])
    h1.caption("Active")
    h2.caption(f"{label} Details")
    h3.caption("Actions")
    
    for i, item in enumerate(items):
        c1, c2, c3 = st.columns([1, 4, 2], vertical_alignment="center")
        
        # Toggle (Equipped/Active)
        is_active = item.get("equipped", item.get("active", True))
        new_active = c1.checkbox("##", value=is_active, key=f"{key}_act_{i}", label_visibility="collapsed")
        
        if new_active != is_active:
            if "equipped" in item: item["equipped"] = new_active
            else: item["active"] = new_active
            st.rerun()

        # Details
        with c2:
            st.markdown(f"**{item.get('name', 'Unnamed')}**")
            if item.get("description"):
                st.caption(item["description"])
            if "weight" in item and item["weight"] > 0:
                st.caption(f"Load: {item['weight']}")
            
        # Actions
        with c3:
            ca, cb = st.columns(2)
            if ca.button("✏️", key=f"{key}_edit_{i}"):
                edit_item_dialog(item, f"{key}_{i}", lambda: None)
            if cb.button("🗑️", key=f"{key}_del_{i}"):
                items.pop(i)
                st.rerun()

def update_stat_callback(target_dict, key, widget_key, save_callback=None):
    """Callback to update character data without forcing a double rerun."""
    target_dict[key] = st.session_state[widget_key]
    if save_callback:
        save_callback()

@st.fragment
def render_character_statblock(char, save_callback=None):
    """Renders the character sheet as a visual statblock with interactive elements."""
    # Ensure stats are up to date within the fragment
    _, _, _, effective_stats, effective_skills = calculate_stats(char)
    
    # 1. SPECIAL Stats
    stat_keys = ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]
    
    special_html = '<div class="special-grid">'
    for key in stat_keys:
        val = int(effective_stats.get(key, 5))
        special_html += (
            f'<div class="special-box">'
            f'<div class="special-label">{key}</div>'
            f'<div class="special-value">{val}</div>'
            f'</div>'
        )
    special_html += '</div>'

    # 2. Derived Stats
    # We will render these using Streamlit columns to allow interactivity for HP/Stamina/XP
    
    # 3. Skills HTML
    skills_by_stat = {k: [] for k in ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]}
    
    for skill, stats in SKILL_MAP.items():
        if skill in effective_skills:
            # Determine governing stat (highest if multiple)
            best_stat = stats[0]
            if len(stats) > 1:
                best_val = -999
                for s in stats:
                    val = effective_stats.get(s, 5)
                    if val > best_val:
                        best_val = val
                        best_stat = s
            
            skills_by_stat[best_stat].append((skill, effective_skills[skill]))

    skills_html = '<div style="margin-bottom: 10px; font-size: 0.9em;">'
    for stat in ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]:
        skill_list = skills_by_stat.get(stat, [])
        if skill_list:
            skill_list.sort(key=lambda x: x[0]) # Sort alphabetically
            s_strs = [f"{name} {val}" for name, val in skill_list]
            skills_html += f'<div><strong style="color: #00cc00;">{stat}:</strong> {", ".join(s_strs)}</div>'
    skills_html += '</div>'

    # --- RENDER CONTAINER ---
    with st.container(border=True):
        # HEADER
        header_html = (
        f'<div class="statblock-header">'
        f'<span class="statblock-title">{char.get("name", "Unnamed")}</span>'
        f'<span class="statblock-meta">Lvl {char.get("level", 1)} {char.get("origin", "Wastelander")}</span>'
        f'</div>'
        )
        st.markdown(header_html + special_html, unsafe_allow_html=True)
        
        # INTERACTIVE STATS ROW
        st.markdown('<div class="derived-row" style="margin-bottom: 5px;">Status</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        
        unique_id = char.get("name", "char")
        
        with c1:
            st.caption(f"HP (Max {char.get('hp_max', 0)})")
            hp_key = f"sb_hp_{unique_id}"
            st.number_input(
                "HP", value=char.get("hp_current", 0), min_value=0, max_value=char.get("hp_max", 999), 
                key=hp_key, label_visibility="collapsed",
                on_change=update_stat_callback, args=(char, "hp_current", hp_key, save_callback)
            )
                
        with c2:
            st.caption(f"SP (Max {char.get('stamina_max', 0)})")
            sp_key = f"sb_sp_{unique_id}"
            st.number_input(
                "SP", value=char.get("stamina_current", 0), min_value=0, max_value=char.get("stamina_max", 999), 
                key=sp_key, label_visibility="collapsed",
                on_change=update_stat_callback, args=(char, "stamina_current", sp_key, save_callback)
            )

        with c3:
            st.caption("XP")
            xp_key = f"sb_xp_{unique_id}"
            st.number_input(
                "XP", value=char.get("xp", 0), min_value=0, step=10, 
                key=xp_key, label_visibility="collapsed",
                on_change=update_stat_callback, args=(char, "xp", xp_key, save_callback)
            )
        
        with c4:
            st.caption("Caps")
            caps_key = f"sb_caps_{unique_id}"
            st.number_input("Caps", value=char.get("caps", 0), min_value=0, step=10, key=caps_key, label_visibility="collapsed", on_change=update_stat_callback, args=(char, "caps", caps_key, save_callback))

        # DERIVED STATS (Read Only)
        derived_html = (
            f'<div class="derived-row" style="margin-top: 10px;">'
            f'<span>AC: {char.get("ac", 10)}</span>'
            f'<span>SEQ: {char.get("combat_sequence", 0)}</span>'
            f'<span>AP: {char.get("action_points", 0)}</span>'
            f'<span>Load: {char.get("current_weight", 0)} / {char.get("carry_load", 0)}</span>'
            f'</div>'
        )
        st.markdown(derived_html + skills_html, unsafe_allow_html=True)

        # INVENTORY / EQUIPMENT
        st.markdown('<div class="section-header">Inventory & Equipment</div>', unsafe_allow_html=True)
        if "inventory" not in char:
            char["inventory"] = []
        inventory = char["inventory"]
        
        if not inventory:
            st.caption("Inventory is empty.")
        
        for i, item in enumerate(inventory):
            c_chk, c_lbl, c_edit, c_del = st.columns([0.15, 0.65, 0.1, 0.1])
            is_equipped = item.get("equipped", False)
            eq_key = f"sb_eq_{unique_id}_{i}"
            
            # Use callback for checkbox
            new_equipped = c_chk.checkbox("Eq", value=is_equipped, key=eq_key, label_visibility="collapsed", on_change=update_stat_callback, args=(item, "equipped", eq_key, save_callback))
            
            style = "color: #00ff00; font-weight: bold;" if new_equipped else "color: #00b300; opacity: 0.8;"
            desc = f" <span style='font-size:0.8em; font-style:italic; opacity:0.7;'>({item.get('description', '')})</span>" if item.get('description') else ""
            weight_str = f" <span style='font-size:0.8em; color:#8b949e;'>[{item.get('weight', 0)} Load]</span>"
            c_lbl.markdown(f"<span style='{style}'>{item.get('name', 'Unknown')}</span>{weight_str}{desc}", unsafe_allow_html=True)
            
            if c_edit.button("✏️", key=f"sb_edit_{unique_id}_{i}"):
                edit_item_dialog(item, f"sb_{unique_id}_{i}", save_callback)
            
            if c_del.button("🗑️", key=f"sb_del_{unique_id}_{i}"):
                inventory.pop(i)
                if save_callback: save_callback()
                st.rerun()

        # Add Equipment Section
        with st.expander("➕ Add Equipment"):
            eq_data = load_data(EQUIPMENT_FILE)
            if not isinstance(eq_data, list): eq_data = []
            eq_names = sorted([e.get("name", "Unknown") for e in eq_data])
            
            tab_db, tab_cust = st.tabs(["Database", "Custom"])
            
            with tab_db:
                sel_item = st.selectbox("Select Item", [""] + eq_names, key=f"sb_eq_sel_{unique_id}")
                if st.button("Add Selected", key=f"sb_btn_add_db_{unique_id}"):
                    if sel_item:
                        entry = next((e for e in eq_data if e["name"] == sel_item), None)
                        new_entry = {"name": sel_item, "description": entry.get("description", "") if entry else "", "weight": entry.get("weight", 0.0) if entry else 0.0, "equipped": False}
                        inventory.append(new_entry)
                        if save_callback: save_callback()
                        st.rerun()
            
            with tab_cust:
                c1, c2 = st.columns([2, 1])
                c_name = c1.text_input("Name", key=f"sb_cust_name_{unique_id}")
                c_weight = c2.number_input("Weight", min_value=0.0, step=0.1, key=f"sb_cust_weight_{unique_id}")
                c_desc = st.text_input("Description", key=f"sb_cust_desc_{unique_id}")
                
                # Modifier Builder
                mod_key = f"sb_cust_mods_{unique_id}"
                render_modifier_builder(f"sb_cust_{unique_id}", mod_key)
                
                if mod_key in st.session_state and st.session_state[mod_key]:
                    st.markdown(" ".join([f"`{m}`" for m in st.session_state[mod_key]]))
                    if st.button("Clear Modifiers", key=f"sb_btn_clear_mods_{unique_id}"):
                        st.session_state[mod_key] = []
                        st.rerun()

                c_local, c_db = st.columns(2)
                
                def create_custom_item():
                    final_desc = c_desc + (" " + " ".join(st.session_state[mod_key]) if mod_key in st.session_state and st.session_state[mod_key] else "")
                    return {"name": c_name, "description": final_desc.strip(), "weight": c_weight, "equipped": False}

                if c_local.button("Add to Character", key=f"sb_btn_add_cust_local_{unique_id}"):
                    if c_name:
                        inventory.append(create_custom_item())
                        st.session_state[mod_key] = []
                        if save_callback: save_callback()
                        st.rerun()

                if c_db.button("Add to Character & DB", key=f"sb_btn_add_cust_db_{unique_id}"):
                    if c_name:
                        new_item = create_custom_item()
                        inventory.append(new_item)
                        
                        if not any(e['name'] == c_name for e in eq_data):
                            eq_data.append({"name": c_name, "description": new_item["description"], "weight": c_weight})
                            save_data(EQUIPMENT_FILE, eq_data)
                            st.toast(f"Added {c_name} to Database")
                        else:
                            st.toast(f"{c_name} already in Database (Added to Character only)")

                        st.session_state[mod_key] = []
                        if save_callback: save_callback()
                        st.rerun()