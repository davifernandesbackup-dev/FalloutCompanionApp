import streamlit as st
import re
from utils.character_logic import get_default_character

def parse_modifiers(description):
    """Extracts modifier strings from a description."""
    if not description:
        return "", []
    pattern = r"\{([a-zA-Z0-9\s]+?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)\}"
    mods = re.findall(pattern, description)
    mod_strings = [f"{{{m[0]} {m[1]}{m[2]}}}" for m in mods]
    clean_desc = re.sub(pattern, "", description).strip()
    clean_desc = re.sub(r"\s+", " ", clean_desc)
    return clean_desc, mod_strings

def join_modifiers(description, mod_list):
    """Combines description and modifiers into a single string."""
    if mod_list:
        return (description + " " + " ".join(mod_list)).strip()
    return description.strip()

def render_modifier_builder(key_prefix, mod_list_key):
    """Renders the UI for adding stat modifiers."""
    mod_categories = {
        "S.P.E.C.I.A.L.": ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"],
        "Skills": sorted(get_default_character()["skills"].keys()),
        "Derived Stats": ["Max HP", "Max SP", "Armor Class", "Carry Load", "Combat Sequence", "Action Points", "Radiation DC", "Passive Sense", "Healing Rate"]
    }
    operator_map = {"Add": "+", "Subtract": "-", "Multiply": "*", "Divide": "/"}

    c_cat, c_stat, c_op = st.columns([1.5, 1.5, 1])
    cat_sel = c_cat.selectbox("Category", list(mod_categories.keys()), key=f"{key_prefix}_mod_cat")
    stat_sel = c_stat.selectbox("Stat", mod_categories[cat_sel], key=f"{key_prefix}_mod_target")
    op_sel = c_op.selectbox("Op", list(operator_map.keys()), key=f"{key_prefix}_mod_op")
    
    c_val, c_btn = st.columns([1, 1], vertical_alignment="bottom")
    val_in = c_val.number_input("Val", value=1.0, step=0.5, key=f"{key_prefix}_mod_val")
    
    if c_btn.button("Add Modifier", key=f"{key_prefix}_btn_add_mod", use_container_width=True):
        val_fmt = int(val_in) if val_in.is_integer() else val_in
        if mod_list_key not in st.session_state: st.session_state[mod_list_key] = []
        st.session_state[mod_list_key].append(f"{{{stat_sel} {operator_map[op_sel]}{val_fmt}}}")

def render_item_form(prefix, current_values, mod_list_key, show_quantity=False, show_load=True):
    """
    Renders a standardized item form.
    current_values: dict with keys (name, weight, item_type, sub_type, range_normal, range_long, description, quantity)
    mod_list_key: session state key for the list of modifiers
    """
    
    if show_quantity and show_load:
        c_name, c_load, c_qty = st.columns([3, 1, 1])
    elif show_load:
        c_name, c_load = st.columns([3, 1])
        c_qty = None
    else:
        c_name = st.container()
        c_load = None
        c_qty = None
    
    k_name = f"{prefix}_name"
    if k_name in st.session_state:
        new_name = c_name.text_input("Name", key=k_name)
    else:
        new_name = c_name.text_input("Name", value=current_values.get("name", ""), key=k_name)

    if show_load and c_load:
        k_weight = f"{prefix}_weight"
        if k_weight in st.session_state:
            new_weight = c_load.number_input("Load", min_value=0.0, step=0.1, key=k_weight)
        else:
            new_weight = c_load.number_input("Load", min_value=0.0, step=0.1, value=float(current_values.get("weight", 0.0)), key=k_weight)
    else:
        new_weight = 0.0
    
    new_qty = 1
    if show_quantity and c_qty:
        k_qty = f"{prefix}_qty"
        if k_qty in st.session_state:
            new_qty = c_qty.number_input("Qty", min_value=1, step=1, key=k_qty)
        else:
            new_qty = c_qty.number_input("Qty", min_value=1, step=1, value=int(current_values.get("quantity", 1)), key=k_qty)
    
    c_type, c_sub = st.columns(2)
    types = ["Misc", "Weapon", "Apparel", "Aid", "Currency"]
    curr_type = current_values.get("item_type", "Misc")
    if curr_type not in types: curr_type = "Misc"
    
    k_type = f"{prefix}_type"
    if k_type in st.session_state:
        new_type = c_type.selectbox("Type", types, key=k_type)
    else:
        new_type = c_type.selectbox("Type", types, index=types.index(curr_type), key=k_type)
    
    new_subtype = current_values.get("sub_type")
    new_rn = int(current_values.get("range_normal", 0))
    new_rl = int(current_values.get("range_long", 0))
    
    if new_type == "Weapon":
        subs = ["Guns", "Melee", "Unarmed", "Explosives", "Energy Weapons"]
        curr_sub = new_subtype if new_subtype in subs else "Guns"
        
        # Ensure session state has a valid value for the selectbox to avoid crashes
        sb_key = f"{prefix}_sub"
        if sb_key in st.session_state and st.session_state[sb_key] not in subs:
            st.session_state[sb_key] = subs[0]
            
        if sb_key in st.session_state:
            new_subtype = c_sub.selectbox("Weapon Type", subs, key=sb_key)
        else:
            new_subtype = c_sub.selectbox("Weapon Type", subs, index=subs.index(curr_sub), key=sb_key)
        
        if new_subtype in ["Guns", "Energy Weapons"]:
            c_rn, c_rl = st.columns(2)
            k_rn = f"{prefix}_rn"
            k_rl = f"{prefix}_rl"
            
            if k_rn in st.session_state:
                new_rn = c_rn.number_input("Normal Range", step=1, min_value=0, key=k_rn)
            else:
                new_rn = c_rn.number_input("Normal Range", value=new_rn, step=1, min_value=0, key=k_rn)
                
            if k_rl in st.session_state:
                new_rl = c_rl.number_input("Long Range", step=1, min_value=0, key=k_rl)
            else:
                new_rl = c_rl.number_input("Long Range", value=new_rl, step=1, min_value=0, key=k_rl)
    else:
        new_subtype = None
        
    k_desc = f"{prefix}_desc"
    if k_desc in st.session_state:
        new_desc = st.text_input("Description", key=k_desc)
    else:
        new_desc = st.text_input("Description", value=current_values.get("description", ""), key=k_desc)
    
    st.markdown("**Modifiers**")
    render_modifier_builder(prefix, mod_list_key)
    
    # Display active modifiers
    if mod_list_key in st.session_state and st.session_state[mod_list_key]:
        for i, mod in enumerate(st.session_state[mod_list_key]):
            row = st.empty()
            with row.container():
                c1, c2 = st.columns([4, 1])
                c1.code(mod)
                if c2.button("🗑️", key=f"{prefix}_del_mod_{i}"):
                    st.session_state[mod_list_key].pop(i)
                    row.empty()
                    st.rerun()
    else:
        st.caption("No modifiers.")
        
    return {
        "name": new_name,
        "quantity": new_qty,
        "weight": new_weight,
        "item_type": new_type,
        "sub_type": new_subtype,
        "range_normal": new_rn,
        "range_long": new_rl,
        "description": new_desc
    }