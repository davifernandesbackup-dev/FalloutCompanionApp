import streamlit as st
import re
import uuid
from utils.data_manager import load_data, save_data
from tabs.character_logic import get_default_character, calculate_stats, SKILL_MAP
from constants import EQUIPMENT_FILE, PERKS_FILE

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
        .load-fill { background-color: #00b300; box-shadow: 0 0 10px #00ff00; }
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
def edit_item_dialog(item, item_id, all_items, callback):
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
        st.session_state[f"{dialog_id}_qty"] = item.get("quantity", 1)
        st.session_state[f"{dialog_id}_is_cont"] = item.get("is_container", False)
        st.session_state[f"{dialog_id}_loc"] = item.get("location", "carried")
        st.session_state[f"{dialog_id}_pid"] = item.get("parent_id", None)

    # UI Inputs
    c_name, c_qty = st.columns([3, 1])
    new_name = c_name.text_input("Name", key=f"{dialog_id}_name_input", value=st.session_state[f"{dialog_id}_name"])
    new_qty = c_qty.number_input("Qty", min_value=1, step=1, key=f"{dialog_id}_qty_input", value=st.session_state[f"{dialog_id}_qty"])
    
    # Show Weight input if the item has a weight key (Equipment)
    new_weight = st.number_input("Load (Per Unit)", min_value=0.0, step=0.1, key=f"{dialog_id}_weight_input", value=st.session_state[f"{dialog_id}_weight"])

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
    
    # Container & Location Logic
    c_cont, c_loc = st.columns(2)
    is_container = c_cont.checkbox("Is Container?", value=st.session_state[f"{dialog_id}_is_cont"], key=f"{dialog_id}_chk_cont")
    
    # Build Move To Options
    # Options: "Carried (Root)", "Stash (Root)", and any valid container
    # Prevent moving into itself or its children to avoid cycles
    
    def get_descendants(pid, items_list):
        desc = []
        children = [i for i in items_list if i.get("parent_id") == pid]
        for child in children:
            desc.append(child["id"])
            desc.extend(get_descendants(child["id"], items_list))
        return desc

    invalid_targets = [item["id"]] + get_descendants(item["id"], all_items)
    potential_containers = [i for i in all_items if i.get("is_container") and i["id"] not in invalid_targets]
    
    loc_options = ["Carried", "Stash"] + [f"Container: {i['name']}" for i in potential_containers]
    
    # Determine current selection index
    current_pid = st.session_state[f"{dialog_id}_pid"]
    current_loc = st.session_state[f"{dialog_id}_loc"]
    
    default_idx = 0
    if current_pid:
        # Find container name
        parent = next((i for i in all_items if i["id"] == current_pid), None)
        if parent:
            try:
                default_idx = loc_options.index(f"Container: {parent['name']}")
            except ValueError: pass
    elif current_loc == "stash":
        default_idx = 1
        
    move_selection = c_loc.selectbox("Location / Container", loc_options, index=default_idx, key=f"{dialog_id}_move_sel")

    st.divider()
    
    if st.button("💾 Save Changes", type="primary"):
        # Reconstruct description
        final_desc = new_desc
        if st.session_state[mods_key]:
            final_desc += " " + " ".join(st.session_state[mods_key])
        
        # Update item
        item["name"] = new_name
        item["description"] = final_desc.strip()
        item["weight"] = new_weight
        item["quantity"] = new_qty
        item["is_container"] = is_container
        
        # Update Location
        if move_selection == "Carried":
            item["parent_id"] = None
            item["location"] = "carried"
        elif move_selection == "Stash":
            item["parent_id"] = None
            item["location"] = "stash"
        else:
            # Extract container name and find ID
            cont_name = move_selection.replace("Container: ", "")
            parent = next((i for i in potential_containers if i["name"] == cont_name), None)
            if parent:
                item["parent_id"] = parent["id"]
                # Location is irrelevant if parent_id is set, but good to keep clean
                item["location"] = "carried" 

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

@st.dialog("Add Item")
def add_db_item_dialog(label, file_path, char, char_key, session_key, prefix, callback=None):
    """Dialog to add items from database or custom."""
    data_list = load_data(file_path)
    if not isinstance(data_list, list):
        data_list = []
    
    data_list.sort(key=lambda x: x.get("name", ""))
    names = [e.get("name", "Unknown") for e in data_list]
    
    st.markdown(f"**Add {label}**")
    
    # Database Selection
    selected_item = st.selectbox(f"Search Database:", [""] + names, key=f"{prefix}_select_dlg")
    
    if st.button(f"Add Selected to {label}", key=f"{prefix}_btn_add_dlg", use_container_width=True):
        if selected_item:
            entry = next((e for e in data_list if e["name"] == selected_item), None)
            
            new_item = {
                "name": selected_item,
                "description": entry.get("description", "") if entry else "",
                "weight": entry.get("weight", 0.0) if entry else 0.0,
                "equipped": False if label == "Equipment" else True,
                "active": True,
                "quantity": 1,
                "id": str(uuid.uuid4()),
                "parent_id": None,
                "location": "carried",
                "is_container": False
            }
            
            if char_key not in char or not isinstance(char[char_key], list):
                char[char_key] = []
            
            char[char_key].append(new_item)
            st.session_state[session_key] = char[char_key]
            if callback: callback()
            st.rerun()

    st.divider()
    st.caption(f"Or Create Custom {label}")
    
    c1, c2 = st.columns([2, 1])
    new_name = c1.text_input("Name", key=f"{prefix}_new_name_dlg")
    new_weight = 0.0
    if label == "Equipment":
        new_weight = c2.number_input("Weight", min_value=0.0, step=0.1, key=f"{prefix}_new_weight_dlg")
    
    new_desc = st.text_input("Description", key=f"{prefix}_new_desc_dlg")
    
    # Modifier Builder
    mod_key = f"{prefix}_modifiers_dlg"
    if mod_key not in st.session_state: st.session_state[mod_key] = []
    render_modifier_builder(prefix + "_dlg", mod_key)

    if st.session_state[mod_key]:
        st.markdown(" ".join([f"`{m}`" for m in st.session_state[mod_key]]))
        if st.button("Clear Modifiers", key=f"{prefix}_btn_clear_mods_dlg"):
            st.session_state[mod_key] = []
            st.rerun()
    
    if st.button("Create & Add", type="primary", use_container_width=True, key=f"{prefix}_btn_create_dlg"):
        if new_name:
            final_desc = new_desc + (" " + " ".join(st.session_state[mod_key]) if st.session_state[mod_key] else "")
            item_data = {
                "name": new_name,
                "description": final_desc.strip(),
                "weight": new_weight if label == "Equipment" else 0.0,
                "equipped": False if label == "Equipment" else True,
                "active": True,
                "quantity": 1,
                "id": str(uuid.uuid4()),
                "parent_id": None,
                "location": "carried",
                "is_container": False
            }
            if char_key not in char or not isinstance(char[char_key], list):
                char[char_key] = []
            char[char_key].append(item_data)
            st.session_state[mod_key] = []
            
            # Clear input fields to prevent data leaking to next item
            st.session_state[f"{prefix}_new_name_dlg"] = ""
            st.session_state[f"{prefix}_new_desc_dlg"] = ""
            if label == "Equipment":
                st.session_state[f"{prefix}_new_weight_dlg"] = 0.0

            if callback: callback()
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
                    "weight": entry.get("weight", 0.0) if entry else 0.0,
                    "equipped": False if label == "Equipment" else True,
                    "active": True,
                    "quantity": 1,
                    "id": str(uuid.uuid4()),
                    "parent_id": None,
                    "location": "carried",
                    "is_container": False
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
                "active": True,
                "quantity": 1,
                "id": str(uuid.uuid4()),
                "parent_id": None,
                "location": "carried",
                "is_container": False
            }

        if c_local.button("Add to Character Only", key=f"{prefix}_btn_add_local"):
            if new_name:
                item_data = get_new_item_data()
                if char_key not in char or not isinstance(char[char_key], list):
                    char[char_key] = []
                char[char_key].append(item_data)
                st.session_state[mod_key] = []
                st.success(f"Added {new_name} to Character")
                
                # Clear inputs
                st.session_state[f"{prefix}_new_name"] = ""
                st.session_state[f"{prefix}_new_desc"] = ""
                if label == "Equipment":
                    st.session_state[f"{prefix}_new_weight"] = 0.0
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
                # Clear inputs
                st.session_state[f"{prefix}_new_name"] = ""
                st.session_state[f"{prefix}_new_desc"] = ""
                if label == "Equipment":
                    st.session_state[f"{prefix}_new_weight"] = 0.0
                st.rerun()

def render_inventory_management(char, key, label, max_load=None, current_load=None):
    """Renders the inventory with Carried/Stash sections and nesting."""
    items = char.get(key, [])
    if not isinstance(items, list):
        items = []
        char[key] = items

    # Separate logic for Perks (simple list) vs Inventory (nested)
    if label == "Perk":
        # Simple list for perks
        for i, item in enumerate(items):
            c1, c2, c3 = st.columns([0.5, 4, 1.5], vertical_alignment="center")
            is_active = item.get("active", True)
            if c1.checkbox("##", value=is_active, key=f"{key}_act_{i}", label_visibility="collapsed"):
                item["active"] = True
            else:
                item["active"] = False
            
            with c2:
                st.markdown(f"**{item.get('name')}**")
                if item.get("description"): st.caption(item["description"])
            
            with c3:
                ca, cb = st.columns(2)
                if ca.button("✏️", key=f"{key}_edit_{i}"):
                    edit_item_dialog(item, item.get("id", str(i)), items, lambda: None)
                if cb.button("🗑️", key=f"{key}_del_{i}"):
                    items.pop(i)
                    st.rerun()
        return

    # --- INVENTORY TREE LOGIC ---
    
    # Build Tree
    tree = {}
    for item in items:
        pid = item.get("parent_id")
        if pid not in tree: tree[pid] = []
        tree[pid].append(item)

    def render_tree_node(item_list):
        for item in item_list:
            is_container = item.get("is_container", False)
            
            if is_container:
                # --- CONTAINER (EXPANDER) ---
                qty_str = f" (x{item.get('quantity', 1)})" if item.get('quantity', 1) > 1 else ""
                label = f"📦 {item.get('name')}{qty_str}"
                
                with st.expander(label):
                    # Container Actions & Details
                    c_desc, c_act = st.columns([3, 1])
                    with c_desc:
                        desc_parts = []
                        if float(item.get("weight", 0)) > 0: desc_parts.append(f"{float(item['weight'])} Load")
                        if item.get("description"): desc_parts.append(item["description"])
                        if desc_parts:
                            st.caption(" | ".join(desc_parts))

                    with c_act:
                        c_ed, c_del = st.columns(2)
                        if c_ed.button("✏️", key=f"inv_ed_{item['id']}"):
                            edit_item_dialog(item, item['id'], items, lambda: None)
                        if c_del.button("🗑️", key=f"inv_del_{item['id']}"):
                            items.remove(item)
                            st.rerun()
                    
                    # Render Children
                    if item["id"] in tree:
                        render_tree_node(tree[item["id"]])
            else:
                # --- ITEM (STANDARD ROW) ---
                c_chk, c_name, c_act = st.columns([0.5, 4, 1.5], vertical_alignment="top")
                
                # Checkbox
                is_caps = item.get("name") == "Caps"
                can_equip = (item.get("parent_id") is None and item.get("location") == "carried" and not is_caps)
                
                with c_chk:
                    if can_equip:
                        is_equipped = item.get("equipped", False)
                        if st.checkbox("Eq", value=is_equipped, key=f"inv_eq_{item['id']}", label_visibility="collapsed"):
                            item["equipped"] = True
                        else:
                            item["equipped"] = False
                
                # Name & Details
                with c_name:
                    qty_str = f" (x{item.get('quantity', 1)})" if item.get('quantity', 1) > 1 else ""
                    st.markdown(f"**{item.get('name')}{qty_str}**")
                    
                    desc_parts = []
                    if float(item.get("weight", 0)) > 0: desc_parts.append(f"{float(item['weight'])} Load")
                    if item.get("description"): desc_parts.append(item["description"])
                    if desc_parts:
                        st.caption(" | ".join(desc_parts))
                
                # Actions
                with c_act:
                    ca, cb = st.columns(2)
                    if ca.button("✏️", key=f"inv_ed_{item['id']}"):
                        edit_item_dialog(item, item['id'], items, lambda: None)
                    if cb.button("🗑️", key=f"inv_del_{item['id']}"):
                        items.remove(item)
                        st.rerun()
                    with st.popover("⚙️", use_container_width=True):
                        if st.button("Edit", key=f"inv_ed_{item['id']}", use_container_width=True):
                            edit_item_dialog(item, item['id'], items, lambda: None)
                        if st.button("Delete", key=f"inv_del_{item['id']}", type="primary", use_container_width=True):
                            items.remove(item)
                            st.rerun()

    # --- RENDER UI ---
    if label == "Equipment":
        # Header with Load Bar and Add Button
        c_load, c_add = st.columns([3, 1], vertical_alignment="bottom")
        with c_load:
            if max_load is not None and current_load is not None:
                pct = min(1.0, current_load / max_load) if max_load > 0 else 1.0
                st.markdown(f"**Load: {current_load} / {max_load}**")
                st.markdown(f"""
                <div class="custom-bar-bg" style="height: 12px; margin-bottom: 5px;">
                    <div class="custom-bar-fill load-fill" style="width: {pct*100}%;"></div>
                </div>
                """, unsafe_allow_html=True)
        with c_add:
            if st.button("➕ Add Item", use_container_width=True, key="btn_open_add_item"):
                add_db_item_dialog("Equipment", EQUIPMENT_FILE, char, key, "c_inv_db", "eq")

        # Tabs for Carried vs Stash
        tab_carried, tab_stash = st.tabs(["🎒 Carried", "📦 Stash"])
        
        with tab_carried:
            carried_roots = [i for i in items if i.get("parent_id") is None and i.get("location") == "carried"]
            if carried_roots:
                render_tree_node(carried_roots)
            else:
                st.caption("Nothing carried.")
                
        with tab_stash:
            stash_roots = [i for i in items if i.get("parent_id") is None and i.get("location") == "stash"]
            if stash_roots:
                render_tree_node(stash_roots)
            else:
                st.caption("Stash is empty.")
    else:
        # Fallback for non-equipment (if any) or legacy view
        st.markdown("### 🎒 Carried")
        carried_roots = [i for i in items if i.get("parent_id") is None and i.get("location") == "carried"]
        if carried_roots: render_tree_node(carried_roots)
        
        st.markdown("### 📦 Stash")
        stash_roots = [i for i in items if i.get("parent_id") is None and i.get("location") == "stash"]
        if stash_roots: render_tree_node(stash_roots)

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
        
        # Load Bar & Add Button
        c_load, c_add = st.columns([3, 1], vertical_alignment="bottom")
        with c_load:
            max_load = char.get("carry_load", 0)
            curr_load = char.get("current_weight", 0)
            pct = min(1.0, curr_load / max_load) if max_load > 0 else 1.0
            st.markdown(f"**Load: {curr_load} / {max_load}**")
            st.markdown(f"""
            <div class="custom-bar-bg" style="height: 12px; margin-bottom: 5px;">
                <div class="custom-bar-fill load-fill" style="width: {pct*100}%;"></div>
            </div>
            """, unsafe_allow_html=True)
        
        with c_add:
            if st.button("➕ Add Item", use_container_width=True, key=f"sb_btn_add_{unique_id}"):
                add_db_item_dialog("Equipment", EQUIPMENT_FILE, char, "inventory", f"sb_inv_sync_{unique_id}", f"sb_eq_{unique_id}", callback=save_callback)

        # Statblock Inventory View (Simplified Tree)
        # Only showing Carried items for statblock usually, but let's show all for management
        
        # We reuse the tree logic but simplified for statblock
        tree = {}
        for item in inventory:
            pid = item.get("parent_id")
            if pid not in tree: tree[pid] = []
            tree[pid].append(item)

        def render_sb_node(item_list):
            for item in item_list:
                is_container = item.get("is_container", False)
                
                if is_container:
                    # Container (Expander)
                    qty_str = f" (x{item.get('quantity', 1)})" if item.get('quantity', 1) > 1 else ""
                    weight_val = float(item.get('weight', 0))
                    weight_str = f" | {weight_val} Load" if weight_val > 0 else ""
                    desc_str = f" | {item.get('description')}" if item.get("description") else ""
                    label = f"📦 {item.get('name')}{qty_str}{weight_str}{desc_str}"
                    
                    c_exp, c_act = st.columns([0.9, 0.1], vertical_alignment="top")
                    
                    with c_act:
                        with st.popover("⚙️", use_container_width=True):
                            if st.button("Edit", key=f"sb_ed_{item['id']}", use_container_width=True):
                                edit_item_dialog(item, item['id'], inventory, save_callback)
                            if st.button("Delete", key=f"sb_del_{item['id']}", type="primary", use_container_width=True):
                                inventory.remove(item)
                                if save_callback: save_callback()
                                st.rerun()

                    with c_exp:
                        with st.expander(label, expanded=True):
                            if item["id"] in tree:
                                render_sb_node(tree[item["id"]])
                else:
                    # Item (Row)
                    c_chk, c_lbl, c_act = st.columns([0.05, 0.85, 0.1], vertical_alignment="top")
                    
                    # Equip Checkbox
                    is_caps = item.get("name") == "Caps"
                    can_equip = (item.get("parent_id") is None and item.get("location") == "carried" and not is_caps)
                    
                    with c_chk:
                        if can_equip:
                            is_equipped = item.get("equipped", False)
                            st.checkbox("Eq", value=is_equipped, key=f"sb_eq_{item['id']}", label_visibility="collapsed", on_change=update_stat_callback, args=(item, "equipped", f"sb_eq_{item['id']}", save_callback))
                    
                    with c_lbl:
                        style = "color: #00ff00; font-weight: bold;" if item.get("equipped") else "color: #e6fffa; opacity: 0.9;"
                        qty_str = f" (x{item.get('quantity', 1)})" if item.get('quantity', 1) > 1 else ""
                        
                        desc_parts = []
                        if float(item.get("weight", 0)) > 0: desc_parts.append(f"{float(item['weight'])} Load")
                        if item.get("description"): desc_parts.append(item["description"])
                        
                        desc_html = f"<br><span style='font-size:0.8em; color:#8b949e;'>{' | '.join(desc_parts)}</span>" if desc_parts else ""
                        
                        st.markdown(f"<span style='{style}'>{item.get('name')}{qty_str}</span>{desc_html}", unsafe_allow_html=True)
                    
                    with c_act:
                        with st.popover("⚙️", use_container_width=True):
                            if st.button("Edit", key=f"sb_ed_{item['id']}", use_container_width=True):
                                edit_item_dialog(item, item['id'], inventory, save_callback)
                            if st.button("Delete", key=f"sb_del_{item['id']}", type="primary", use_container_width=True):
                                inventory.remove(item)
                                if save_callback: save_callback()
                                st.rerun()

        # Tabs for Carried vs Stash
        tab_carried, tab_stash = st.tabs(["🎒 Carried", "📦 Stash"])
        
        with tab_carried:
            carried = [i for i in inventory if i.get("parent_id") is None and i.get("location") == "carried"]
            if carried:
                render_sb_node(carried)
            else:
                st.caption("Nothing carried.")
        
        with tab_stash:
            stash = [i for i in inventory if i.get("parent_id") is None and i.get("location") == "stash"]
            if stash:
                render_sb_node(stash)
            else:
                st.caption("Stash is empty.")