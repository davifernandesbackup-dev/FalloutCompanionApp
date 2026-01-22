import streamlit as st
from utils.data_manager import load_data, save_data
from tabs.character_logic import get_default_character

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
        .statblock-container {
            border: 2px solid #00b300;
            border-radius: 8px;
            padding: 15px;
            background-color: rgba(13, 17, 23, 0.9);
            font-family: "Source Sans Pro", sans-serif;
            box-shadow: 0 0 10px rgba(0, 255, 0, 0.2);
            margin-bottom: 10px;
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
        col_health_max.text_input("Max HP", value=str(effective_health_max), disabled=True, key="c_hp_max_disp", label_visibility="collapsed")
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
        col_stamina_max.text_input("Max SP", value=str(effective_stamina_max), disabled=True, key="c_stamina_max_disp", label_visibility="collapsed")
        char["stamina_current"] = col_stamina_current.number_input("Curr SP", min_value=0, max_value=effective_stamina_max, step=1, key="c_stamina_curr", label_visibility="collapsed")

@st.dialog("Edit Item")
def edit_item_dialog(item, callback):
    """Dialog to edit an item's name and description."""
    new_name = st.text_input("Name", value=item.get("name", ""))
    new_desc = st.text_input("Description", value=item.get("description", ""))
    
    if st.button("Save Changes"):
        item["name"] = new_name
        item["description"] = new_desc
        callback()
        st.rerun()

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
        new_name = st.text_input("Name", key=f"{prefix}_new_name")
        new_desc = st.text_input("Description", key=f"{prefix}_new_desc")
        
        # Modifier Builder
        mod_key = f"{prefix}_modifiers"
        if mod_key not in st.session_state: st.session_state[mod_key] = []
        
        mod_categories = {
            "S.P.E.C.I.A.L.": ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"],
            "Skills": sorted(get_default_character()["skills"].keys()),
            "Derived Stats": ["Max HP", "Max SP", "Armor Class", "Carry Load", "Combat Sequence", "Action Points"]
        }
        operator_map = {"Add": "+", "Subtract": "-", "Multiply": "*", "Divide": "/"}

        c_cat, c_stat, c_op, c_val, c_btn = st.columns([1.5, 1.5, 1.2, 1, 0.8])
        cat_sel = c_cat.selectbox("Category", list(mod_categories.keys()), key=f"{prefix}_mod_cat")
        stat_sel = c_stat.selectbox("Stat", mod_categories[cat_sel], key=f"{prefix}_mod_target")
        op_sel = c_op.selectbox("Op", list(operator_map.keys()), key=f"{prefix}_mod_op")
        val_in = c_val.number_input("Val", value=1.0, step=0.5, key=f"{prefix}_mod_val")
        
        if c_btn.button("Add", key=f"{prefix}_btn_add_mod"):
            val_fmt = int(val_in) if val_in.is_integer() else val_in
            st.session_state[mod_key].append(f"{{{stat_sel} {operator_map[op_sel]}{val_fmt}}}")

        if st.session_state[mod_key]:
            st.markdown(" ".join([f"`{m}`" for m in st.session_state[mod_key]]))
            if st.button("Clear Modifiers", key=f"{prefix}_btn_clear_mods"):
                st.session_state[mod_key] = []
                st.rerun()
        
        if st.button("Save to Database", key=f"{prefix}_btn_save_db"):
            if new_name:
                final_desc = new_desc + (" " + " ".join(st.session_state[mod_key]) if st.session_state[mod_key] else "")
                if not any(e['name'] == new_name for e in data_list):
                    data_list.append({"name": new_name, "description": final_desc.strip()})
                    save_data(file_path, data_list)
                    st.success(f"Created {new_name}")
                    st.session_state[mod_key] = []
                    st.rerun()
                else:
                    st.warning("Item already exists.")

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
            
        # Actions
        with c3:
            ca, cb = st.columns(2)
            if ca.button("✏️", key=f"{key}_edit_{i}"):
                edit_item_dialog(item, lambda: None)
            if cb.button("🗑️", key=f"{key}_del_{i}"):
                items.pop(i)
                st.rerun()

def render_character_statblock(char):
    """Renders the character sheet as a visual statblock."""
    
    # 1. SPECIAL Stats
    stats = char.get('stats', {})
    stat_keys = ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]
    
    special_html = '<div class="special-grid">'
    for key in stat_keys:
        val = stats.get(key, 5)
        special_html += (
            f'<div class="special-box">'
            f'<div class="special-label">{key}</div>'
            f'<div class="special-value">{val}</div>'
            f'</div>'
        )
    special_html += '</div>'

    # 2. Derived Stats
    derived_html = (
        f'<div class="derived-row">'
        f'<span>HP: {char.get("hp_current", 0)}/{char.get("hp_max", 0)}</span>'
        f'<span>AC: {char.get("ac", 10)}</span>'
        f'<span>SEQ: {char.get("combat_sequence", 0)}</span>'
        f'<span>AP: {char.get("action_points", 0)}</span>'
        f'</div>'
    )

    # 3. Skills
    # Format skills as "Name Rank"
    skills_list = [f"{k} {v}" for k, v in sorted(char.get('skills', {}).items())]
    skills_str = ", ".join(skills_list)
    skills_html = f'<div style="margin-bottom: 10px; font-size: 0.9em;"><strong>Skills:</strong> {skills_str}</div>' if skills_str else ""

    # 4. Attacks / Equipment
    attacks_html = ""
    inventory = char.get('inventory', [])
    equipped_items = [item for item in inventory if item.get('equipped', False)]
    
    if equipped_items:
        attacks_html += '<div class="section-header">Equipped Gear</div>'
        for item in equipped_items:
            name = item.get('name', 'Unknown')
            desc = item.get('description', '')
            attacks_html += (
                f'<div class="attack-row">'
                f'<div><strong>{name}</strong></div>'
                f'<div style="font-size: 0.9em; color: #ccffcc; font-style: italic;">{desc}</div>'
                f'</div>'
            )

    # Assemble Full HTML
    full_html = (
        f'<div class="statblock-container">'
        f'<div class="statblock-header">'
        f'<span class="statblock-title">{char.get("name", "Unnamed")}</span>'
        f'<span class="statblock-meta">Lvl {char.get("level", 1)} {char.get("origin", "Wastelander")}</span>'
        f'</div>'
        f'{special_html}'
        f'{derived_html}'
        f'{skills_html}'
        f'{attacks_html}'
        f'</div>'
    )

    st.markdown(full_html, unsafe_allow_html=True)