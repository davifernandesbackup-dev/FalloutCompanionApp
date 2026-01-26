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
    
    # Toggle state for builder visibility
    builder_visible_key = f"{key_prefix}_mod_builder_visible"
    if builder_visible_key not in st.session_state:
        st.session_state[builder_visible_key] = False

    def open_builder():
        st.session_state[builder_visible_key] = True

    def close_builder():
        st.session_state[builder_visible_key] = False

    if not st.session_state[builder_visible_key]:
        st.button("➕ Add Modifier", key=f"{key_prefix}_btn_open_mod_builder", on_click=open_builder)
        return

    st.markdown("---")
    st.caption("Construct Modifier")

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
    
    c_val, c_act = st.columns([1, 1], vertical_alignment="bottom")
    val_in = c_val.number_input("Val", value=1.0, step=0.5, key=f"{key_prefix}_mod_val")
    
    def add_modifier():
        curr_stat = st.session_state[f"{key_prefix}_mod_target"]
        curr_op = st.session_state[f"{key_prefix}_mod_op"]
        curr_val = st.session_state[f"{key_prefix}_mod_val"]
        val_fmt = int(curr_val) if curr_val.is_integer() else curr_val
        if mod_list_key not in st.session_state: st.session_state[mod_list_key] = []
        st.session_state[mod_list_key].append(f"{{{curr_stat} {operator_map[curr_op]}{val_fmt}}}")

    with c_act:
        c_confirm, c_cancel = st.columns(2)
        c_confirm.button("✅ Add", key=f"{key_prefix}_btn_add_mod", use_container_width=True, on_click=add_modifier)
        c_cancel.button("❌ Cancel", key=f"{key_prefix}_btn_cancel_mod", use_container_width=True, on_click=close_builder)
    st.markdown("---")

def render_item_form(prefix, current_values, mod_list_key, all_db_items, show_quantity=False):
    """
    Renders a standardized item form based on the new items.json schema.
    current_values: dict representing a single item from items.json.
    mod_list_key: session state key for the list of modifiers
    all_db_items: The full list of items from the database, for lookups (e.g., ammo).
    """
    
    # --- Universal Fields ---
    c_name, c_load, c_cost, c_str = st.columns(4)
    c_name.text_input("Name", value=current_values.get("name", ""), key=f"{prefix}_name")
    c_load.number_input("Load", min_value=0.0, step=0.1, value=float(current_values.get("load", 0.0)), key=f"{prefix}_load")
    c_cost.number_input("Cost", min_value=0, value=int(current_values.get("cost", 0)), key=f"{prefix}_cost")
    c_str.number_input("STR Req", min_value=0, value=int(current_values.get("strReq", 0)), key=f"{prefix}_strReq")
    
    if show_quantity:
        st.number_input("Quantity", min_value=1, step=1, value=int(current_values.get("quantity", 1)), key=f"{prefix}_qty")

    # --- Category & Props ---
    categories = sorted([
        "weapon", "armor", "power_armor", "ammo", "explosive", "mod", "ammo_mod",
        "gear", "bag", "food", "drink", "magazine", "medicine", "chem", "program"
    ])
    
    default_cat = current_values.get("category", "gear")
    if default_cat not in categories: default_cat = "gear"
    
    new_category = st.selectbox("Category", categories, index=categories.index(default_cat), key=f"{prefix}_category")

    props = current_values.get("props", {})

    st.markdown("---")
    st.caption(f"Properties for **{new_category.replace('_', ' ').title()}**")

    if new_category == "weapon":
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Weapon Type", ["ballistic", "energy", "melee"], index=["ballistic", "energy", "melee"].index(props.get("weaponType", "ballistic")), key=f"{prefix}_p_weaponType")
        c2.number_input("Hands", min_value=1, max_value=2, value=int(props.get("hands", 1)), key=f"{prefix}_p_hands")
        c3.number_input("AP Cost", min_value=0, value=int(props.get("apCost", 4)), key=f"{prefix}_p_apCost")

        c1, c2 = st.columns(2)
        c1.text_input("Damage", value=props.get("damage", "1d6"), key=f"{prefix}_p_damage")
        c2.text_input("Damage Type", value=props.get("damageType", "ballistic"), key=f"{prefix}_p_damageType")
        
        c1, c2 = st.columns(2)
        c1.text_input("Range", value=props.get("range", "x6/x10"), help="e.g., x6/x10", key=f"{prefix}_p_range")
        c2.text_input("Critical", value=str(props.get("critical", "20, x2")), help="e.g., 20, x2 or 19, 1d6", key=f"{prefix}_p_critical")

        st.markdown("---")
        c1, c2 = st.columns(2)
        ammo_ids = [""] + sorted([i['id'] for i in all_db_items if i.get('category') == 'ammo'])
        default_ammo = props.get("ammoType", "")
        ammo_idx = ammo_ids.index(default_ammo) if default_ammo in ammo_ids else 0
        c1.selectbox("Ammo ID", ammo_ids, index=ammo_idx, key=f"{prefix}_p_ammoType")
        c2.number_input("Magazine Size", min_value=0, value=int(props.get("magazineSize", 0)), key=f"{prefix}_p_magazineSize")
        
        st.text_area("Special Rules (one per line)", value="\n".join(props.get("special", [])), key=f"{prefix}_p_special")

    elif new_category in ["armor", "power_armor"]:
        c1, c2, c3 = st.columns(3)
        c1.number_input("AC Bonus", value=int(props.get("ac", 0)), key=f"{prefix}_p_ac")
        c2.number_input("DT", value=int(props.get("dt", 0)), key=f"{prefix}_p_dt")
        if new_category == "power_armor":
             c2.number_input("DP", value=int(props.get("dp", 0)), key=f"{prefix}_p_dp")
        c3.number_input("Slots", value=int(props.get("slots", 6)), key=f"{prefix}_p_slots")
        
        c1, c2 = st.columns(2)
        c1.number_input("Load (Worn)", value=float(props.get("loadWorn", 0.0)), key=f"{prefix}_p_loadWorn")
        if new_category == "armor":
            c2.selectbox("Armor Type", ["Light", "Heavy"], index=["Light", "Heavy"].index(props.get("type", "Light")), key=f"{prefix}_p_type")
    
    elif new_category == "ammo":
        c1, c2 = st.columns(2)
        c1.number_input("Pack Size", min_value=1, value=int(props.get("packSize", 1)), key=f"{prefix}_p_packSize")
        c2.text_input("Load Rule", value=props.get("loadRule", "10 rounds = 1 load"), key=f"{prefix}_p_loadRule")

    elif new_category == "bag":
        c1, c2 = st.columns(2)
        c1.number_input("Load (Worn)", value=float(props.get("loadWorn", 0.0)), key=f"{prefix}_p_loadWorn")
        c2.number_input("Carry Bonus", value=int(props.get("carryCapacityBonus", 0)), key=f"{prefix}_p_carryCapacityBonus")
        st.text_input("Encumbrance Rule", value=props.get("encumbranceRule", ""), key=f"{prefix}_p_encumbranceRule")
        st.text_area("Special Text", value=props.get("specialText", ""), key=f"{prefix}_p_specialText")

    elif new_category == "ammo_mod":
        c1, c2 = st.columns(2)
        c1.selectbox("Ammo Category", ["ballistic", "energy", "heavy", "explosive"], index=["ballistic", "energy", "heavy", "explosive"].index(props.get("ammoCategory", "ballistic")) if props.get("ammoCategory") in ["ballistic", "energy", "heavy", "explosive"] else 0, key=f"{prefix}_p_ammoCategory")
        c2.number_input("Cost Multiplier", value=float(props.get("costMultiplier", 1.0)), key=f"{prefix}_p_costMultiplier")
        
        # Compatible Ammo (List)
        comp_ammo = props.get("compatibleAmmo", [])
        st.text_area("Compatible Ammo (one per line)", value="\n".join(comp_ammo) if isinstance(comp_ammo, list) else str(comp_ammo), key=f"{prefix}_p_compatibleAmmo")
        
        st.text_area("Special Effect", value=props.get("specialEffect", ""), key=f"{prefix}_p_specialEffect")

    elif new_category == "chem":
        st.text_input("Addiction Type", value=props.get("addictionType", ""), key=f"{prefix}_p_addictionType")
        st.text_area("Chem Effect Description", value=props.get("description", ""), key=f"{prefix}_p_description")

    else:
        st.info(f"Form fields for category '{new_category}' are not yet implemented.")

    st.markdown("---")
    st.text_area("Description / Notes", value=current_values.get("description", ""), key=f"{prefix}_desc")

    st.markdown("**Modifiers**")
    render_modifier_builder(prefix, mod_list_key)
    
    # Display active modifiers
    if mod_list_key in st.session_state and st.session_state[mod_list_key]:
        for i, mod in enumerate(st.session_state[mod_list_key]):
            row = st.empty()
            with row.container():
                c1, c2 = st.columns([4, 1])
                c1.code(mod)
                
                def delete_mod(idx=i):
                    st.session_state[mod_list_key].pop(idx)
                
                c2.button("🗑️", key=f"{prefix}_del_mod_{i}", on_click=delete_mod)
    else:
        st.caption("No modifiers.")

def get_item_data_from_form(prefix, mod_list_key):
    """Constructs an item dictionary from session state based on form inputs."""
    name = st.session_state.get(f"{prefix}_name", "")
    load = st.session_state.get(f"{prefix}_load", 0.0)
    cost = st.session_state.get(f"{prefix}_cost", 0)
    strReq = st.session_state.get(f"{prefix}_strReq", 0)
    category = st.session_state.get(f"{prefix}_category", "gear")
    description = st.session_state.get(f"{prefix}_desc", "")
    quantity = st.session_state.get(f"{prefix}_qty", 1)
    
    props = {}
    prop_keys = [k for k in st.session_state if k.startswith(f"{prefix}_p_")]
    for key in prop_keys:
        prop_name = key.replace(f"{prefix}_p_", "")
        props[prop_name] = st.session_state[key]

    # Handle special cases like lists from text_area
    if "special" in props and isinstance(props["special"], str):
        props["special"] = [line.strip() for line in props["special"].split('\n') if line.strip()]
    if "compatibleAmmo" in props and isinstance(props["compatibleAmmo"], str):
        props["compatibleAmmo"] = [line.strip() for line in props["compatibleAmmo"].split('\n') if line.strip()]

    final_desc = join_modifiers(description, st.session_state.get(mod_list_key, []))

    return {
        "name": name, "load": load, "cost": cost, "strReq": strReq, "quantity": quantity,
        "category": category, "description": final_desc, "props": props
    }