import streamlit as st
import streamlit.components.v1 as components
import re
import uuid
import random
from utils.data_manager import load_data, save_data
from utils.character_logic import get_default_character, calculate_stats, SKILL_MAP
from utils.item_components import render_item_form, render_modifier_builder, parse_modifiers, join_modifiers, get_item_data_from_form
from utils.dice import roll_dice
from constants import ITEM_FILE, PERKS_FILE, RECIPES_FILE

def render_css(compact=True):
    primary = st.session_state.get("theme_primary", "#00ff00")
    secondary = st.session_state.get("theme_secondary", "#00b300")
    
    st.markdown(f"""
    <style>
        /* Global Font & Colors */
        .stApp {{
            font-family: "Source Sans Pro", sans-serif;
            background-color: #0d1117;
            color: {secondary};
        }}

        .section-header {{
            border-bottom: 1px solid {secondary};
            margin-top: 0px;
            margin-bottom: 6px;
            font-size: 1.1em;
            font-weight: bold;
            text-transform: uppercase;
            color: {primary};
            text-shadow: 0 0 5px {primary}B3; /* B3 is approx 70% alpha */
        }}

        /* TERMINAL INPUT STYLING (Base) */
        div[data-testid="stTextInput"] {{
            border-bottom: 1px solid {secondary};
        }}
        
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextInput"] input {{
            color: {primary} !important;
            background-color: transparent !important;
            font-family: "Source Code Pro", monospace;
            padding: 0px !important;
            height: 1.8rem !important;
            min-height: 1.8rem !important;
            -webkit-text-fill-color: {primary} !important;
            text-align: center !important;
        }}

        div[data-testid="stTextArea"] textarea {{
            color: {primary} !important;
            background-color: transparent !important;
            font-family: "Source Code Pro", monospace;
            -webkit-text-fill-color: {primary} !important;
        }}
        
        /* Style the +/- buttons in NumberInput */
        div[data-testid="stNumberInput"] button {{
            color: {primary} !important;
            border: none !important;
            background-color: transparent !important;
        }}
        
        div[data-testid="stSelectbox"] > div > div {{
            background-color: rgba(13, 17, 23, 0.9) !important;
            color: {primary} !important;
            border: 1px solid {secondary} !important;
            box-shadow: 0 0 5px {primary}33;
        }}

        .stat-bar-container {{
            width: 100%;
            background-color: #0d1117;
            border: 1px solid {secondary};
            border-radius: 4px;
            height: 38px;
            position: relative;
            overflow: hidden;
            margin-top: -0px;
        }}
        .stat-bar-text {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85em;
            font-weight: bold;
            color: #ffffff;
            text-shadow: 1px 1px 2px black;
            pointer-events: none;
        }}
        
        .custom-bar-bg {{
            width: 100%;
            background-color: #0d1117;
            border: 1px solid {secondary};
            border-radius: 4px;
            height: 28px;
            position: relative;
            overflow: hidden;
        }}
        
        .custom-bar-fill {{
            height: 100%;
            transition: width 0.5s ease-in-out;
        }}
        .hp-fill {{ background-color: #ff3333; box-shadow: 0 0 10px #ff0000; }}
        .stamina-fill {{ background-color: #bbbb00; box-shadow: 0 0 10px #ccff00; }}
        .load-fill {{ background-color: {secondary}; box-shadow: 0 0 10px {primary}; }}
        .xp-fill {{ background-color: #0066cc; box-shadow: 0 0 10px #003366; }}
        
        .stat-bar-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        
        .roll-btn {{
            padding: 0px 5px;
            font-size: 0.8em;
            margin-left: 5px;
        }}
        .item-row {{
            background-color: rgba(0, 179, 0, 0.1);
            border-left: 3px solid {secondary};
            border-radius: 0 4px 4px 0;
            padding: 8px;
            margin-bottom: 6px;
            color: #e6fffa;
        }}

        /* Button Styling */
        .stButton > button,
        div[data-testid="stPopover"] > button {{
            text-transform: uppercase;
            font-weight: bold;
            transition: all 0.2s;
        }}

        /* Secondary button (default, unequipped) */
        .stButton > button[data-testid="stButton-secondary"],
        div[data-testid="stPopover"] > button {{
            background-color: transparent;
            color: {secondary};
            border: 1px solid {secondary} !important;
        }}
        .stButton > button[data-testid="stButton-secondary"]:hover,
        div[data-testid="stPopover"] > button:hover {{
            background-color: {secondary};
            color: #0d1117;
            box-shadow: 0 0 10px {primary}80;
            border-color: {primary} !important;
        }}

        /* Secondary popoverbutton (default) */
        .stButton > button[data-testid="stPopoverButton"],
        button[kind="secondary"] {{
            background-color: transparent;
            color: {secondary};
            border: 1px solid {secondary} !important;
        }}

        /* Primary button (filled, equipped) */
        .stButton > button[data-testid="stButton-primary"] {{
            background-color: {secondary};
            color: #0d1117;
            border: 1px solid {secondary};
        }}
        .stButton > button[data-testid="stButton-primary"]:hover {{
            background-color: {primary};
            border-color: {primary};
            color: #0d1117;
            box-shadow: 0 0 10px {primary}B3;
        }}
                
        /* CRT SCANLINE EFFECT */
        .scanlines {{
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
        }}
        
        /* Data Editor Styling */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {secondary};
            background-color: rgba(13, 17, 23, 0.9);
        }}

        /* Popover Content Styling */
        div[data-testid="stPopoverButton"] {{
            border: 2px solid {secondary} !important;
            background-color: #0d1117 !important;
            color: {secondary} !important;
        }}

        /* STATBLOCK STYLING */
        /* Target the st.container(border=True) */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border: 2px solid {secondary} !important;
            border-radius: 8px;
            background-color: rgba(13, 17, 23, 0.9) !important;
            box-shadow: 0 0 10px {primary}33 !important;
            padding: 10px !important;
        }}
        .statblock-header {{
            border-bottom: 2px solid {secondary};
            margin-bottom: 10px;
            padding-bottom: 5px;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }}
        .statblock-title {{
            font-size: 1.4em;
            font-weight: bold;
            color: {primary};
            text-transform: uppercase;
            text-shadow: 0 0 5px {primary}B3;
        }}
        .statblock-meta {{
            font-style: italic;
            color: {secondary};
            font-size: 0.9em;
        }}
        .special-grid {{
            display: flex;
            width: 100%;
            border: 2px solid {secondary};
            border-radius: 6px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .special-box {{
            text-align: center;
            flex: 1;
            border-right: 1px solid {secondary};
            background-color: #0d1117;
        }}
        .special-box:hover {{ background-color: {secondary}33; }}
        .special-box:last-child {{
            border-right: none;
        }}
        .special-label {{
            background-color: {secondary};
            color: #0d1117;
            font-weight: bold;
            font-size: 0.75em;
            padding: 2px 0;
            text-shadow: none;
        }}
        .special-value {{
            font-size: 1.1em;
            font-weight: bold;
            padding: 4px 0;
            color: {primary};
            line-height: 1.2;
        }}
        .derived-row {{
            display: flex;
            justify-content: space-around;
            background-color: rgba(0, 179, 0, 0.15);
            padding: 6px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-weight: bold;
            color: #e6fffa;
        }}
        .attack-row {{
            margin-bottom: 6px;
            padding-left: 8px;
            border-left: 3px solid {secondary};
            background-color: rgba(0, 179, 0, 0.05);
        }}
    </style>
    <div class="scanlines"></div>
    """, unsafe_allow_html=True)

def get_descendants(pid, items_list):
    """Recursively finds all descendant item IDs for a given parent ID."""
    desc = []
    children = [i for i in items_list if i.get("parent_id") == pid]
    for child in children:
        desc.append(child["id"])
        desc.extend(get_descendants(child["id"], items_list))
    return desc

def render_move_menu(item, all_items, key_prefix, callback=None):
    """Renders dynamic buttons to move items between Root/Stash/Containers."""
    
    # 1. Root/Location Toggle
    if item.get("parent_id"):
        # Item is inside a container -> Extract options
        if st.button("🎒 Extract to Carried", key=f"{key_prefix}_ext_carry", use_container_width=True):
            item["parent_id"] = None
            item["location"] = "carried"
            if callback: callback()
            st.rerun()
        if st.button("📦 Extract to Stash", key=f"{key_prefix}_ext_stash", use_container_width=True):
            item["parent_id"] = None
            item["location"] = "stash"
            item["equipped"] = False
            if callback: callback()
            st.rerun()
    else:
        # Item is at root -> Swap Location
        if item.get("location") == "carried":
            if st.button("📦 To Stash", key=f"{key_prefix}_to_stash", use_container_width=True):
                item["location"] = "stash"
                item["parent_id"] = None
                item["equipped"] = False
                if callback: callback()
                st.rerun()
        else:
            if st.button("🎒 To Carried", key=f"{key_prefix}_to_carry", use_container_width=True):
                item["location"] = "carried"
                item["parent_id"] = None
                if callback: callback()
                st.rerun()

    # 2. Move to Container
    descendants = get_descendants(item["id"], all_items)
    # Valid containers: is_container, not self, not a descendant of self
    valid_containers = [
        c for c in all_items 
        if c.get("is_container") 
        and c["id"] != item["id"] 
        and c["id"] not in descendants
    ]
    
    if valid_containers:
        st.caption("Move To:")
        valid_containers.sort(key=lambda x: x.get("name", ""))
        
        # If many containers, use selectbox to save space
        if len(valid_containers) > 4:
            opts = {c["id"]: c.get("name", "Unnamed") for c in valid_containers}
            sel_id = st.selectbox("Container", options=list(opts.keys()), format_func=lambda x: opts[x], key=f"{key_prefix}_sel_cont", label_visibility="collapsed")
            if st.button("Move", key=f"{key_prefix}_go_move", use_container_width=True):
                target = next((c for c in valid_containers if c["id"] == sel_id), None)
                if target:
                    item["parent_id"] = target["id"]
                    item["location"] = target.get("location", "carried")
                    item["equipped"] = False
                    if callback: callback()
                    st.rerun()
        else:
            for c in valid_containers:
                if st.button(f"➡️ {c.get('name')}", key=f"{key_prefix}_mv_{c['id']}", use_container_width=True):
                    item["parent_id"] = c["id"]
                    item["location"] = c.get("location", "carried")
                    item["equipped"] = False
                    if callback: callback()
                    st.rerun()

@st.dialog("Confirm Deletion")
def confirm_delete_item_dialog(item, all_items, callback=None):
    st.markdown(f"Are you sure you want to delete **{item.get('name', 'Unknown')}**?")
    
    if item.get("is_container", False):
        descendants = get_descendants(item["id"], all_items)
        if descendants:
            st.warning(f"⚠️ This container contains {len(descendants)} items. They will also be deleted.")
    
    if st.button("Confirm Delete", type="primary", use_container_width=True):
        to_remove = get_descendants(item["id"], all_items) + [item["id"]]
        all_items[:] = [i for i in all_items if i["id"] not in to_remove]
        if callback: callback()
        st.rerun()

@st.dialog("Confirm Deletion")
def confirm_delete_simple_dialog(item, item_list, callback=None):
    st.markdown(f"Are you sure you want to delete **{item.get('name', 'Unknown')}**?")
    if st.button("Confirm Delete", type="primary", use_container_width=True):
        if item in item_list:
            item_list.remove(item)
        if callback: callback()
        st.rerun()

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

@st.dialog("Manage Health")
def hp_manager_dialog(char, max_hp, save_callback=None):
    st.markdown("Manage Hit Points.")
    current = char.get("hp_current", 0)
    st.metric("Current HP", f"{current} / {max_hp}")
    
    amount = st.number_input("Amount", min_value=1, value=1, step=1, key="hp_dlg_amount")
    
    c_heal, c_dmg = st.columns(2)
    if c_heal.button("➕ Heal", use_container_width=True, key="hp_dlg_heal"):
        char["hp_current"] = min(max_hp, current + amount)
        if save_callback: save_callback()
        st.rerun()
        
    if c_dmg.button("➖ Damage", use_container_width=True, key="hp_dlg_dmg"):
        char["hp_current"] = max(0, current - amount)
        if save_callback: save_callback()
        st.rerun()

@st.dialog("Manage Stamina")
def stamina_manager_dialog(char, max_sp, save_callback=None):
    st.markdown("Manage Stamina Points.")
    current = char.get("stamina_current", 0)
    st.metric("Current SP", f"{current} / {max_sp}")
    
    amount = st.number_input("Amount", min_value=1, value=1, step=1, key="sp_dlg_amount")
    
    c_rec, c_spend = st.columns(2)
    if c_rec.button("➕ Recover", use_container_width=True, key="sp_dlg_rec"):
        char["stamina_current"] = min(max_sp, current + amount)
        if save_callback: save_callback()
        st.rerun()
        
    if c_spend.button("➖ Spend", use_container_width=True, key="sp_dlg_spend"):
        char["stamina_current"] = max(0, current - amount)
        if save_callback: save_callback()
        st.rerun()

@st.dialog("Manage Experience")
def xp_manager_dialog(char, save_callback=None):
    """Dialog to add or remove experience points."""
    st.markdown("Add or remove experience points.")
    current_xp = char.get("xp", 0)
    st.metric("Current XP", current_xp)
    
    amount = st.number_input("Amount", min_value=1, value=100, step=100, key="xp_dlg_amount")
    
    col_add, col_remove = st.columns(2)
    
    if col_add.button("➕ Add XP", use_container_width=True, key="xp_dlg_add"):
        char["xp"] = current_xp + amount
        if save_callback: save_callback()
        st.rerun()
        
    if col_remove.button("➖ Remove XP", use_container_width=True, key="xp_dlg_remove"):
        char["xp"] = max(0, current_xp - amount)
        if save_callback: save_callback()
        st.rerun()

@st.dialog("Manage Caps")
def caps_manager_dialog(char, save_callback=None):
    """Dialog to add or remove caps from inventory."""
    st.markdown("Add or remove caps from your inventory.")
    
    # Find existing caps
    inventory = char.get("inventory", [])
    caps_item = next((i for i in inventory if i.get("name") == "Cap" and i.get("location") == "carried" and i.get("parent_id") is None), None)
    
    current_caps = caps_item.get("quantity", 0) if caps_item else 0
    st.metric("Current Caps", current_caps)
    
    amount = st.number_input("Amount", min_value=1, value=10, step=1, key="caps_dlg_amount")
    
    col_add, col_remove = st.columns(2)
    
    if col_add.button("➕ Add Caps", use_container_width=True, key="caps_dlg_add"):
        if not caps_item:
            caps_item = {
                "id": str(uuid.uuid4()),
                "name": "Cap",
                "description": "Currency",
                "weight": 0.02,
                "quantity": 0,
                "equipped": False,
                "location": "carried",
                "parent_id": None,
                "is_container": False,
                "item_type": "Currency"
            }
            inventory.append(caps_item)
        
        # Ensure properties are correct even if item existed
        caps_item["weight"] = 0.02
        caps_item["item_type"] = "Currency"
        caps_item["quantity"] = caps_item.get("quantity", 0) + amount
        if save_callback: save_callback()
        st.rerun()
        
    if col_remove.button("➖ Remove Caps", use_container_width=True, key="caps_dlg_remove"):
        if caps_item:
            new_qty = max(0, caps_item.get("quantity", 0) - amount)
            caps_item["quantity"] = new_qty
            if new_qty == 0:
                inventory.remove(caps_item)
            if save_callback: save_callback()
            st.rerun()

@st.dialog("Crafting")
def crafting_manager_dialog(char, save_callback=None):
    """Dialog to handle crafting items based on recipes."""
    recipes = load_data(RECIPES_FILE)
    if not isinstance(recipes, list):
        st.warning("No recipes found in database.")
        return

    inventory = char.get("inventory", [])
    
    # Helper to count items in inventory (recursive not strictly needed if we assume flat names, but good for robustness)
    def get_inv_qty(name):
        total = 0
        for item in inventory:
            if item.get("name") == name:
                total += item.get("quantity", 1)
        return total

    st.markdown("### Available Recipes")
    
    search = st.text_input("Search Recipes", key="craft_search")
    filtered_recipes = [r for r in recipes if search.lower() in r.get("name", "").lower()]
    
    for recipe in filtered_recipes:
        # Check Requirements
        can_craft = True
        missing_text = []
        
        # 1. Check Ingredients
        ingredients = recipe.get("ingredients", [])
        for ing in ingredients:
            have = get_inv_qty(ing["name"])
            need = ing["quantity"]
            if have < need:
                can_craft = False
                missing_text.append(f"Missing {ing['name']} ({have}/{need})")
        
        # 2. Check Skill
        req = recipe.get("skill_requirement", {})
        if req.get("skill"):
            skill_name = req["skill"]
            skill_level = req.get("level", 0)
            char_skill = char.get("skills", {}).get(skill_name, 0)
            # We should probably use effective skill, but raw is safer for now or we need to pass effective stats
            # For now, let's use the value in char dict which is usually base, 
            # but let's assume the user has updated the sheet. 
            # Ideally we pass effective_skills to this dialog, but for now let's trust the sheet state or calc it.
            # Let's do a quick calc or just use base to be safe/simple.
            if char_skill < skill_level:
                can_craft = False
                missing_text.append(f"Low {skill_name} ({char_skill}/{skill_level})")

        # Render Row
        with st.container(border=True):
            c_info, c_act = st.columns([3, 1])
            with c_info:
                st.markdown(f"**{recipe['name']}**")
                res = recipe.get("result", {})
                st.caption(f"Result: {res.get('name')} x{res.get('quantity', 1)}")
                
                # Ingredients List
                ing_strs = []
                for ing in ingredients:
                    have = get_inv_qty(ing["name"])
                    color = "green" if have >= ing["quantity"] else "red"
                    ing_strs.append(f":{color}[{ing['name']} {have}/{ing['quantity']}]")
                st.markdown(" | ".join(ing_strs))
                
                if missing_text:
                    st.error(", ".join(missing_text))
            
            with c_act:
                if st.button("🛠️ Craft", key=f"btn_craft_{recipe.get('id')}", disabled=not can_craft, use_container_width=True):
                    # Deduct Ingredients
                    for ing in ingredients:
                        qty_needed = ing["quantity"]
                        # Iterate inventory to remove
                        for item in inventory[:]: # Copy to modify
                            if item.get("name") == ing["name"]:
                                take = min(qty_needed, item.get("quantity", 1))
                                item["quantity"] -= take
                                qty_needed -= take
                                if item["quantity"] <= 0:
                                    inventory.remove(item)
                                if qty_needed <= 0:
                                    break
                    
                    # Add Result
                    res_name = res.get("name")
                    res_qty = res.get("quantity", 1)
                    
                    # Check if we can stack
                    # For simplicity, just add new item. The user can stack manually or we implement auto-stack later.
                    # We should try to find item data from ITEM_FILE to get weight/desc
                    eq_db = load_data(ITEM_FILE)
                    db_item = next((i for i in eq_db if i["name"] == res_name), None)
                    
                    new_item = {
                        "id": str(uuid.uuid4()),
                        "name": res_name,
                        "description": db_item.get("description", "Crafted item") if db_item else "Crafted item",
                        "weight": db_item.get("weight", 0.0) if db_item else 0.0,
                        "quantity": res_qty,
                        "equipped": False,
                        "location": "carried",
                        "parent_id": None,
                        "is_container": False,
                        "item_type": db_item.get("item_type", "Misc") if db_item else "Misc"
                    }
                    inventory.append(new_item)
                    
                    st.success(f"Crafted {res_name}!")
                    if save_callback: save_callback()
                    st.query_params["_update"] = str(uuid.uuid4())

def convert_nested_to_flat(nested_item):
    """Converts a new schema item (nested props) to the flat inventory format."""
    props = nested_item.get("props", {})
    category = nested_item.get("category", "gear")
    
    # Map Category to Item Type
    cat_map = {
        "weapon": "Weapon", "armor": "Armor", "power_armor": "Power Armor", "bag": "Bag",
        "ammo": "Ammo", "ammo_mod": "Mod", "explosive": "Weapon", "food": "Food", "drink": "Drink",
        "medicine": "Medicine", "chem": "Chem", "mod": "Mod", "gear": "Gear",
        "program": "Program", "magazine": "Magazine"
    }
    item_type = cat_map.get(category, "Misc")
    
    flat_item = {
        "name": nested_item.get("name", "Unknown"),
        "description": nested_item.get("description", ""),
        "weight": float(nested_item.get("load", 0.0)),
        "cost": int(nested_item.get("cost", 0)),
        "quantity": int(nested_item.get("quantity", 1)),
        "item_type": item_type,
        "category": category
    }
    
    # Weapon Specifics
    if category in ["weapon", "explosive"]:
        w_type = props.get("weaponType", "")
        if w_type == "ballistic": flat_item["sub_type"] = "Guns"
        elif w_type == "energy": flat_item["sub_type"] = "Energy Weapons"
        elif w_type == "melee": flat_item["sub_type"] = "Melee"
        elif category == "explosive": flat_item["sub_type"] = "Explosives"
        
        dmg = str(props.get("damage", "1d6"))
        if "d" in dmg:
            parts = dmg.split("d")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                flat_item["damage_dice_count"] = int(parts[0])
                flat_item["damage_dice_sides"] = int(parts[1])
        elif dmg.isdigit():
            flat_item["damage_dice_count"] = int(dmg)
            flat_item["damage_dice_sides"] = 1
        
        rng = str(props.get("range", ""))
        if "/" in rng:
            parts = rng.replace("x", "").split("/")
            if len(parts) == 2:
                # Handle potential whitespace
                p0 = parts[0].strip()
                p1 = parts[1].strip()
                flat_item["range_normal"] = int(p0) if p0.isdigit() else 0
                flat_item["range_long"] = int(p1) if p1.isdigit() else 0
        
        flat_item["ammo_item"] = props.get("ammoType", "")
        flat_item["ammo_capacity"] = props.get("magazineSize", 0)
        if flat_item["ammo_capacity"] > 0:
            flat_item["uses_ammo"] = True
            
    # Bag Specifics
    if category == "bag":
        flat_item["load_worn"] = float(props.get("loadWorn", 0.0))
        flat_item["carry_bonus"] = int(props.get("carryCapacityBonus", 0))
        try:
            flat_item["encumbrance_rule"] = int(props.get("encumbranceRule", 0))
        except (ValueError, TypeError):
            flat_item["encumbrance_rule"] = 0

    # Armor Specifics
    if category in ["armor", "power_armor"]:
        flat_item["ac_bonus"] = props.get("ac", 0)
        flat_item["dt"] = props.get("dt", 0)
        flat_item["sub_type"] = props.get("type", "")
        flat_item["load_worn"] = float(props.get("loadWorn", 0.0))
        
    return flat_item

@st.dialog("Edit Item")
def edit_item_dialog(item, item_id, all_items, callback, show_load=True, show_type=True):
    """Dialog to edit an item's name, description, weight, and modifiers."""
    # Generate a unique key for this dialog session based on item ID
    dialog_id = f"edit_dialog_{item_id}"
    
    # Signature to detect item swaps on same ID (e.g. index reuse)
    current_sig = f"{item.get('name')}|{item.get('description')}|{item.get('weight', 0)}"
    sig_key = f"{dialog_id}_sig"
    
    # Initialize session state for this item if not already done
    if f"{dialog_id}_initialized" not in st.session_state or f"{dialog_id}_name" not in st.session_state or st.session_state.get(sig_key) != current_sig:
        desc = item.get("description", "")
        clean_desc, mod_strings = parse_modifiers(desc)
        
        # --- MAP FLAT -> NESTED FOR FORM INITIALIZATION ---
        cat_map_rev = {
            "Weapon": "weapon", "Apparel": "armor", "Ammo": "ammo",
            "Aid": "chem", "Mod": "mod", "Misc": "gear", "Currency": "gear", "Ammo Mod": "ammo_mod"
        }
        # Try to use existing category, fallback to mapping from item_type
        category = item.get("category", cat_map_rev.get(item.get("item_type"), "gear"))
        
        st.session_state[f"{dialog_id}_name"] = item.get("name", "")
        st.session_state[f"{dialog_id}_desc"] = clean_desc
        st.session_state[f"{dialog_id}_load"] = float(item.get("weight", 0.0))
        st.session_state[f"{dialog_id}_cost"] = int(item.get("cost", 0))
        st.session_state[f"{dialog_id}_qty"] = int(item.get("quantity", 1))
        st.session_state[f"{dialog_id}_category"] = category
        st.session_state[f"{dialog_id}_mods"] = mod_strings
        st.session_state[f"{dialog_id}_initialized"] = True
        st.session_state[sig_key] = current_sig
        
        # Instance specific fields (not in props)
        st.session_state[f"{dialog_id}_is_cont"] = item.get("is_container", False)
        st.session_state[f"{dialog_id}_loc"] = item.get("location", "carried")
        st.session_state[f"{dialog_id}_pid"] = item.get("parent_id", None)
        st.session_state[f"{dialog_id}_ammo_curr"] = int(item.get("ammo_current", 0))
        st.session_state[f"{dialog_id}_reloads"] = int(item.get("reloads_count", 0))
        st.session_state[f"{dialog_id}_decay"] = int(item.get("decay", 0))
        
        # Map Flat Props -> Session State Props
        if category == "weapon":
            st.session_state[f"{dialog_id}_p_damage"] = f"{item.get('damage_dice_count', 1)}d{item.get('damage_dice_sides', 6)}"
            st.session_state[f"{dialog_id}_p_range"] = f"x{item.get('range_normal', 0)}/x{item.get('range_long', 0)}"
            st.session_state[f"{dialog_id}_p_ammoType"] = item.get("ammo_item", "")
            st.session_state[f"{dialog_id}_p_magazineSize"] = int(item.get("ammo_capacity", 0))
            
            ct = item.get("crit_threshold", 20)
            cd = item.get("crit_damage", "")
            st.session_state[f"{dialog_id}_p_critical"] = f"{ct}, {cd}" if cd else f"{ct}, x2"
            
            w_type_map = {"Guns": "ballistic", "Energy Weapons": "energy", "Melee": "melee", "Explosives": "explosive"}
            st.session_state[f"{dialog_id}_p_weaponType"] = w_type_map.get(item.get("sub_type"), "ballistic")
        
        elif category in ["armor", "power_armor"]:
            st.session_state[f"{dialog_id}_p_ac"] = int(item.get("ac_bonus", 0))
            st.session_state[f"{dialog_id}_p_dt"] = int(item.get("dt", 0))
            st.session_state[f"{dialog_id}_p_type"] = item.get("sub_type", "Light")
            st.session_state[f"{dialog_id}_p_loadWorn"] = float(item.get("load_worn", 0.0))

        elif category == "bag":
            st.session_state[f"{dialog_id}_p_loadWorn"] = float(item.get("load_worn", 0.0))
            st.session_state[f"{dialog_id}_p_carryCapacityBonus"] = int(item.get("carry_bonus", 0))
            st.session_state[f"{dialog_id}_p_encumbranceRule"] = str(item.get("encumbrance_rule", 0))

    # Prepare values for form
    # We pass an empty dict because we've already populated session state keys
    # render_item_form will use the session state keys
    current_values = {} 
    mods_key = f"{dialog_id}_mods"
    
    db_items = load_data(ITEM_FILE)
    render_item_form(dialog_id, current_values, mods_key, db_items, show_quantity=True)
    
    # Retrieve updated data
    updated_nested = get_item_data_from_form(dialog_id, mods_key)

    st.divider()
    
    # Instance Specific State (Ammo/Reloads)
    # Check props from updated_nested
    props = updated_nested.get("props", {})
    if updated_nested["category"] == "weapon" and int(props.get("magazineSize", 0)) > 0:
        c_ac, c_rc = st.columns(2)
        new_ammo_curr = c_ac.number_input("Current Ammo", min_value=0, max_value=int(props.get("magazineSize", 0)), value=st.session_state[f"{dialog_id}_ammo_curr"], key=f"{dialog_id}_in_ac")
        new_reloads = c_rc.number_input("Reloads Count", min_value=0, value=st.session_state[f"{dialog_id}_reloads"], key=f"{dialog_id}_in_rc")
        
    new_decay = st.number_input("Decay", min_value=0, value=st.session_state[f"{dialog_id}_decay"], key=f"{dialog_id}_in_decay")

    # Container & Location Logic
    c_cont, c_loc = st.columns(2)
    is_container = c_cont.checkbox("Is Container?", value=st.session_state[f"{dialog_id}_is_cont"], key=f"{dialog_id}_chk_cont")
    
    # Build Move To Options
    # Options: "Carried (Root)", "Stash (Root)", and any valid container
    # Prevent moving into itself or its children to avoid cycles
    
    invalid_targets = [item["id"]] + get_descendants(item["id"], all_items)
    potential_containers = [i for i in all_items if i.get("is_container") and i["id"] not in invalid_targets]
    
    # Check for duplicate names to disambiguate
    name_counts = {}
    for c in potential_containers:
        name_counts[c["name"]] = name_counts.get(c["name"], 0) + 1

    # Build options map: ID -> Display String
    loc_map = {
        "carried": "Carried",
        "stash": "Stash"
    }
    
    for c in potential_containers:
        display_name = c["name"]
        if name_counts.get(c["name"], 0) > 1:
            display_name = f"{c['name']} ({c['id'][:4]})"
        loc_map[c["id"]] = f"Container: {display_name}"
    
    loc_options = ["carried", "stash"] + [c["id"] for c in potential_containers]
    
    # Determine current selection
    current_pid = st.session_state[f"{dialog_id}_pid"]
    current_loc = st.session_state[f"{dialog_id}_loc"]
    
    default_val = "carried"
    if current_pid and current_pid in loc_map:
        default_val = current_pid
    elif current_loc == "stash":
        default_val = "stash"
    
    try:
        default_idx = loc_options.index(default_val)
    except ValueError:
        default_idx = 0
        
    move_selection = c_loc.selectbox(
        "Location / Container", 
        loc_options, 
        index=default_idx, 
        format_func=lambda x: loc_map.get(x, x),
        key=f"{dialog_id}_move_sel"
    )

    st.divider()
    
    if st.button("💾 Save Changes", type="primary"):
        # Convert Nested -> Flat
        flat_update = convert_nested_to_flat(updated_nested)
        
        # Update item in place
        item.update(flat_update)
        
        # Update Instance Specifics
        item["is_container"] = is_container
        item["decay"] = new_decay
        
        if updated_nested["category"] == "weapon" and int(props.get("magazineSize", 0)) > 0:
            item["ammo_current"] = new_ammo_curr
            item["reloads_count"] = new_reloads
        
        # Update Location
        if move_selection == "carried":
            item["parent_id"] = None
            item["location"] = "carried"
        elif move_selection == "stash":
            item["parent_id"] = None
            item["location"] = "stash"
        else:
            # move_selection is the container ID
            item["parent_id"] = move_selection
            item["location"] = "carried" 

        # Cleanup session state
        del st.session_state[f"{dialog_id}_initialized"]
        for key in list(st.session_state.keys()):
            if key.startswith(dialog_id):
                del st.session_state[key]
                
        if callback:
            callback()
        st.rerun()

@st.dialog("Add Item")
def add_db_item_dialog(label, file_path, char, char_key, session_key, prefix, callback=None, close_key=None):
    """Dialog to add items from database or custom."""
    
    # Check for cleanup flag from previous run
    cleanup_key = f"{prefix}_cleanup_needed"
    if st.session_state.get(cleanup_key):
        st.session_state[f"{prefix}_dlg_name"] = ""
        st.session_state[f"{prefix}_dlg_desc"] = ""
        if label == "Equipment":
            st.session_state[f"{prefix}_dlg_load"] = 0.0
            # Clear other props if needed, but they default safely
        st.session_state[cleanup_key] = False

    show_load = (label == "Equipment")
    show_type = (label == "Equipment")
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
            
            # --- SCHEMA MAPPING (New items.json -> Inventory) ---
            props = entry.get("props", {})
            category = entry.get("category", "misc")
            
            # Map Category to Item Type
            cat_map = {
                "weapon": "Weapon", "armor": "Armor", "power_armor": "Power Armor", "bag": "Bag",
                "ammo": "Ammo", "ammo_mod": "Mod", "explosive": "Weapon", "food": "Food", "drink": "Drink",
                "medicine": "Medicine", "chem": "Chem", "mod": "Mod", "gear": "Gear",
                "program": "Program", "magazine": "Magazine"
            }
            item_type = cat_map.get(category, "Misc")
            
            # Construct Description
            desc_parts = []
            if entry.get("description"): desc_parts.append(entry["description"])
            if "special" in props: desc_parts.extend(props["special"])
            if "effects" in props: desc_parts.extend(props["effects"])
            if "specialText" in props: desc_parts.append(props["specialText"])
            if "specialEffect" in props: desc_parts.append(props["specialEffect"])
            description = " | ".join(desc_parts)
            
            is_bag = (category == "bag")
            new_item = {
                "name": selected_item,
                "description": description,
                "weight": float(entry.get("load", 0.0)) if entry else 0.0,
                "cost": entry.get("cost", 0),
                "equipped": False if label == "Equipment" else True,
                "active": True,
                "quantity": 1,
                "id": str(uuid.uuid4()),
                "parent_id": None,
                "location": "carried",
                "is_container": is_bag,
                "item_type": item_type,
                "category": category
            }
            
            # Weapon Specifics
            if category in ["weapon", "explosive"]:
                w_type = props.get("weaponType", "")
                if w_type == "ballistic": new_item["sub_type"] = "Guns"
                elif w_type == "energy": new_item["sub_type"] = "Energy Weapons"
                elif w_type == "melee": new_item["sub_type"] = "Melee"
                elif category == "explosive": new_item["sub_type"] = "Explosives"
                
                # Damage
                dmg = str(props.get("damage", "1d6"))
                if "d" in dmg:
                    parts = dmg.split("d")
                    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        new_item["damage_dice_count"] = int(parts[0])
                        new_item["damage_dice_sides"] = int(parts[1])
                elif dmg.isdigit():
                    new_item["damage_dice_count"] = int(dmg)
                    new_item["damage_dice_sides"] = 1
                
                # Range
                rng = str(props.get("range", ""))
                if "/" in rng:
                    parts = rng.replace("x", "").split("/")
                    if len(parts) == 2:
                        new_item["range_normal"] = int(parts[0]) if parts[0].isdigit() else 0
                        new_item["range_long"] = int(parts[1]) if parts[1].isdigit() else 0
                
                # Ammo & Crit
                new_item["ammo_item"] = props.get("ammoType", "")
                new_item["ammo_capacity"] = props.get("magazineSize", 0)
                if new_item["ammo_capacity"] > 0:
                    new_item["uses_ammo"] = True
                    new_item["ammo_current"] = new_item["ammo_capacity"]
                
                crit = str(props.get("critical", ""))
                if "," in crit:
                    c_parts = crit.split(",")
                    new_item["crit_threshold"] = int(c_parts[0].strip()) if c_parts[0].strip().isdigit() else 20
                    if len(c_parts) > 1: new_item["crit_damage"] = c_parts[1].strip()

            # Bag Specifics
            if category == "bag":
                new_item["load_worn"] = float(props.get("loadWorn", 0.0))
                new_item["carry_bonus"] = int(props.get("carryCapacityBonus", 0))
                try:
                    new_item["encumbrance_rule"] = int(props.get("encumbranceRule", 0))
                except (ValueError, TypeError):
                    new_item["encumbrance_rule"] = 0

            # Armor Specifics
            if category in ["armor", "power_armor"]:
                new_item["ac_bonus"] = props.get("ac", 0)
                new_item["dt"] = props.get("dt", 0)
                new_item["sub_type"] = props.get("type", "")
                new_item["load_worn"] = float(props.get("loadWorn", 0.0))
            
            if char_key not in char or not isinstance(char[char_key], list):
                char[char_key] = []
            
            char[char_key].append(new_item)
            st.session_state[session_key] = char[char_key]
            if callback: callback()
            st.query_params["_update"] = str(uuid.uuid4())
            st.rerun()

    st.divider()
    st.caption(f"Or Create Custom {label}")
    
    # Initialize defaults for custom item form
    name_key = f"{prefix}_dlg_name"
    if name_key not in st.session_state: st.session_state[name_key] = ""
    
    mod_key = f"{prefix}_modifiers_dlg"
    if mod_key not in st.session_state: st.session_state[mod_key] = []
    
    # Use render_item_form but we need to manage the values manually since it's not bound to an existing item
    # We can pass empty dict and let it use keys
    render_item_form(prefix + "_dlg", {}, mod_key, data_list, show_quantity=False)

    if st.button("Create & Add", type="primary", use_container_width=True, key=f"{prefix}_btn_create_dlg"):
        nested_data = get_item_data_from_form(prefix + "_dlg", mod_key)
        
        if nested_data["name"]:
            item_data = convert_nested_to_flat(nested_data)
            
            is_bag = (nested_data.get("category") == "bag")
            # Add instance defaults
            item_data.update({
                "id": str(uuid.uuid4()),
                "parent_id": None,
                "location": "carried",
                "is_container": is_bag,
                "equipped": False if label == "Equipment" else True,
                "active": True,
                "ammo_current": 0,
                "decay": 0,
                "reloads_count": 0
            })
            
            if char_key not in char or not isinstance(char[char_key], list):
                char[char_key] = []
            char[char_key].append(item_data)
            st.session_state[session_key] = char[char_key]
            st.session_state[mod_key] = []
            
            # Set flag to clear inputs on next open
            st.session_state[cleanup_key] = True

            if callback: callback()
            if close_key: st.session_state[close_key] = False
            st.query_params["_update"] = str(uuid.uuid4())
            st.rerun()

def render_database_manager(label, file_path, char, char_key, session_key, prefix):
    show_load = (label == "Equipment")
    show_type = (label == "Equipment")
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
                
                # --- SCHEMA MAPPING (New items.json -> Inventory) ---
                props = entry.get("props", {})
                category = entry.get("category", "misc")
                
                cat_map = {
                    "weapon": "Weapon", "armor": "Armor", "power_armor": "Power Armor", "bag": "Bag",
                    "ammo": "Ammo", "ammo_mod": "Mod", "explosive": "Weapon", "food": "Food", "drink": "Drink",
                    "medicine": "Medicine", "chem": "Chem", "mod": "Mod", "gear": "Gear",
                    "program": "Program", "magazine": "Magazine"
                }
                item_type = cat_map.get(category, "Misc")
                
                # Construct Description
                desc_parts = []
                if entry.get("description"): desc_parts.append(entry["description"])
                if "special" in props: desc_parts.extend(props["special"])
                if "effects" in props: desc_parts.extend(props["effects"])
                if "specialText" in props: desc_parts.append(props["specialText"])
                if "specialEffect" in props: desc_parts.append(props["specialEffect"])
                description = " | ".join(desc_parts)
                
                is_bag = (category == "bag")
                new_item = {
                    "name": selected_item,
                    "description": description,
                    "weight": float(entry.get("load", 0.0)) if entry else 0.0,
                    "cost": entry.get("cost", 0),
                    "equipped": False if label == "Equipment" else True,
                    "active": True,
                    "quantity": 1,
                    "id": str(uuid.uuid4()),
                    "parent_id": None,
                    "location": "carried",
                    "is_container": is_bag,
                    "item_type": item_type,
                    "category": category
                }
                
                # Weapon Specifics
                if category in ["weapon", "explosive"]:
                    w_type = props.get("weaponType", "")
                    if w_type == "ballistic": new_item["sub_type"] = "Guns"
                    elif w_type == "energy": new_item["sub_type"] = "Energy Weapons"
                    elif w_type == "melee": new_item["sub_type"] = "Melee"
                    elif category == "explosive": new_item["sub_type"] = "Explosives"
                    
                    dmg = str(props.get("damage", "1d6"))
                    if "d" in dmg:
                        parts = dmg.split("d")
                        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                            new_item["damage_dice_count"] = int(parts[0])
                            new_item["damage_dice_sides"] = int(parts[1])
                    elif dmg.isdigit():
                        new_item["damage_dice_count"] = int(dmg)
                        new_item["damage_dice_sides"] = 1
                    
                    rng = str(props.get("range", ""))
                    if "/" in rng:
                        parts = rng.replace("x", "").split("/")
                        if len(parts) == 2:
                            new_item["range_normal"] = int(parts[0]) if parts[0].isdigit() else 0
                            new_item["range_long"] = int(parts[1]) if parts[1].isdigit() else 0
                    
                    new_item["ammo_item"] = props.get("ammoType", "")
                    new_item["ammo_capacity"] = props.get("magazineSize", 0)
                    if new_item["ammo_capacity"] > 0:
                        new_item["uses_ammo"] = True
                        new_item["ammo_current"] = new_item["ammo_capacity"]

                if category == "bag":
                    new_item["load_worn"] = float(props.get("loadWorn", 0.0))
                    new_item["carry_bonus"] = int(props.get("carryCapacityBonus", 0))
                    try:
                        new_item["encumbrance_rule"] = int(props.get("encumbranceRule", 0))
                    except (ValueError, TypeError):
                        new_item["encumbrance_rule"] = 0

                if category in ["armor", "power_armor"]:
                    new_item["ac_bonus"] = props.get("ac", 0)
                    new_item["dt"] = props.get("dt", 0)
                    new_item["sub_type"] = props.get("type", "")
                    new_item["load_worn"] = float(props.get("loadWorn", 0.0))
                
                if char_key not in char or not isinstance(char[char_key], list):
                    char[char_key] = []
                
                char[char_key].append(new_item)
                st.session_state[session_key] = char[char_key]

        st.button(f"Add to {label}", key=f"{prefix}_btn_add", on_click=add_db_item)

        st.markdown("---")
        st.caption(f"Create New {label}")
        
        # Modifier Builder
        mod_key = f"{prefix}_modifiers"
        if mod_key not in st.session_state: st.session_state[mod_key] = []
        
        render_item_form(prefix, {}, mod_key, data_list, show_quantity=False)
        
        c_local, c_db = st.columns(2)
        
        def clear_inputs():
            st.session_state[f"{prefix}_name"] = ""
            st.session_state[f"{prefix}_desc"] = ""
            if show_load:
                st.session_state[f"{prefix}_weight"] = 0.0
            st.session_state[mod_key] = []

        def add_local_callback():
            nested_data = get_item_data_from_form(prefix, mod_key)
            if nested_data["name"]:
                item_data = convert_nested_to_flat(nested_data)
                item_data.update({
                    "id": str(uuid.uuid4()), "parent_id": None, "location": "carried", "is_container": False,
                    "equipped": False if label == "Equipment" else True, "active": True, "ammo_current": 0, "decay": 0, "reloads_count": 0
                })
                if char_key not in char or not isinstance(char[char_key], list):
                    char[char_key] = []
                char[char_key].append(item_data)
                st.toast(f"Added {nested_data['name']} to Character")
                clear_inputs()

        def save_db_callback():
            nested_data = get_item_data_from_form(prefix, mod_key)
            if nested_data["name"]:
                # 1. Create Flat Item for Character
                item_data = convert_nested_to_flat(nested_data)
                is_bag = (nested_data.get("category") == "bag")
                item_data.update({
                    "id": str(uuid.uuid4()), "parent_id": None, "location": "carried", "is_container": is_bag,
                    "equipped": False if label == "Equipment" else True, "active": True, "ammo_current": 0, "decay": 0, "reloads_count": 0
                })
                
                # Add to Char
                if char_key not in char or not isinstance(char[char_key], list):
                    char[char_key] = []
                char[char_key].append(item_data)

                # Add to DB
                if label == "Equipment":
                    # Use the nested data directly for DB entry
                    db_entry = {
                        "id": str(uuid.uuid4()),
                        "name": nested_data["name"],
                        "description": nested_data["description"],
                        "load": nested_data["load"],
                        "cost": nested_data["cost"],
                        "strReq": nested_data["strReq"],
                        "category": nested_data["category"],
                        "props": nested_data["props"]
                    }
                else:
                    db_entry = {k: v for k, v in item_data.items() if k not in ["equipped", "active"]}

                if not any(e['name'] == nested_data["name"] for e in data_list):
                    data_list.append(db_entry)
                    save_data(file_path, data_list)
                    st.toast(f"Added {nested_data['name']} to Database & Character")
                else:
                    st.toast(f"Item {nested_data['name']} already in database (Added to Character only)")
                
                clear_inputs()

        c_local.button("Add to Character Only", key=f"{prefix}_btn_add_local", on_click=add_local_callback)
        c_db.button("Save to DB & Add", key=f"{prefix}_btn_save_db", on_click=save_db_callback)

def render_inventory_management(char, key, label, max_load=None, current_load=None, effective_stats=None):
    """Renders the inventory with Carried/Stash sections and nesting."""
    items = char.get(key, [])
    if not isinstance(items, list):
        items = []
        char[key] = items

    # --- FILTER & SORT UI ---
    if label == "Equipment":
        c_filter, c_sort = st.columns(2)
        filter_types = c_filter.multiselect("Filter by Type", ["Weapon", "Armor", "Power Armor", "Bag", "Food", "Drink", "Medicine", "Chem", "Gear", "Ammo", "Mod", "Program", "Magazine", "Currency", "Misc"], key=f"inv_filter_{key}")
        sort_option = c_sort.selectbox("Sort by", ["Name (A-Z)", "Load (Low-High)", "Load (High-Low)", "Type"], key=f"inv_sort_{key}")
        
        # Apply Filter
        if filter_types:
            items_to_show = [i for i in items if i.get("item_type", "Misc") in filter_types]
        else:
            items_to_show = items
    else:
        items_to_show = items
        filter_types = []
        sort_option = None

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
                    edit_item_dialog(item, item.get("id", str(i)), items, lambda: None, show_load=False, show_type=False)
                if cb.button("🗑️", key=f"{key}_del_{i}"):
                    confirm_delete_simple_dialog(item, items)
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
                
                # Visual indicator for equipped state
                eq_prefix = "🔗 " if item.get("equipped", False) else ""
                label = f"{eq_prefix}📦 {item.get('name')}{qty_str}"
                
                with st.expander(label):
                    # Container Actions & Details
                    c_chk, c_desc, c_act = st.columns([0.2, 4, 1])
                    
                    with c_chk:
                        can_equip = (item.get("parent_id") is None and item.get("location") == "carried")
                        if can_equip:
                            is_equipped = item.get("equipped", False)
                            if st.checkbox("Eq", value=is_equipped, key=f"cont_eq_{item['id']}", label_visibility="collapsed"):
                                item["equipped"] = True
                            else:
                                item["equipped"] = False

                    with c_desc:
                        desc_parts = []
                        if float(item.get("weight", 0)) > 0: desc_parts.append(f"{float(item['weight'])} Load")
                        if item.get("description"): desc_parts.append(item["description"])
                        if desc_parts:
                            st.caption(" | ".join(desc_parts))

                    with c_act:
                        with st.popover("⚙️", use_container_width=True):
                            if st.button("Delete", key=f"inv_del_{item['id']}", type="primary", use_container_width=True):
                                confirm_delete_item_dialog(item, items)
                            st.divider()
                            if st.button("Edit", key=f"inv_ed_{item['id']}", use_container_width=True):
                                edit_item_dialog(item, item['id'], items, lambda: None, show_load=True)
                            render_move_menu(item, items, f"inv_mv_{item['id']}")
                            
                    
                    # Render Children
                    if item["id"] in tree:
                        render_tree_node(tree[item["id"]])
            else:
                # --- ITEM (STANDARD ROW) ---
                c_chk, c_name, c_act = st.columns([0.5, 4, 1.5], vertical_alignment="top")
                
                # Checkbox
                is_caps = item.get("name") == "Cap"
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
                    # Type Info
                    i_type = item.get("item_type", "Misc")
                    if i_type == "Weapon":
                        sub = item.get("sub_type", "")
                        if sub: desc_parts.append(sub)
                        if sub in ["Guns", "Energy Weapons", "Archery", "Explosives"]:
                            rn = int(item.get('range_normal', 0))
                            rl = int(item.get('range_long', 0))
                            if rn > 0:
                                if effective_stats:
                                    # Calculate Range
                                    range_attr_map = {"Guns": "PER", "Energy Weapons": "PER", "Archery": "STR", "Explosives": "STR"}
                                    stat_key = range_attr_map.get(sub, "PER")
                                    stat_val = effective_stats.get(stat_key, 5)
                                    
                                    rn_ft = int(stat_val * rn)
                                    rl_ft = int(stat_val * rl)
                                    rn_m = round(rn_ft * 0.3)
                                    rl_m = round(rl_ft * 0.3)
                                    desc_parts.append(f"Range: Normal - {rn_m}m ({rn_ft}f, {rn}x) / Long - {rl_m}m ({rl_ft}f, {rl}x)")
                                    
                                    # Ammo Status
                                    if item.get("ammo_capacity", 0) > 0:
                                        desc_parts.append(f"Ammo: {item.get('ammo_current', 0)}/{item.get('ammo_capacity', 0)}")
                                else:
                                    desc_parts.append(f"Range: {rn}/{rl}")
                    elif i_type != "Misc":
                        desc_parts.append(i_type)

                    if float(item.get("weight", 0)) > 0: desc_parts.append(f"{float(item['weight'])} Load")
                    if item.get("description"): desc_parts.append(item["description"])
                    if item.get("decay", 0) > 0: desc_parts.append(f"Decay: {item['decay']}")
                    
                    if i_type == "Weapon" and item.get("crit_threshold", 20) < 20:
                        desc_parts.append(f"Crit: {item['crit_threshold']}+")

                    if desc_parts:
                        st.caption(" | ".join(desc_parts))
                
                # Actions
                with c_act:
                    with st.popover("⚙️", use_container_width=True):
                        if st.button("Delete", key=f"inv_del_{item['id']}", type="primary", use_container_width=True):
                            confirm_delete_item_dialog(item, items)
                        
                        st.divider()

                        if st.button("Edit", key=f"inv_ed_{item['id']}", use_container_width=True):
                            edit_item_dialog(item, item['id'], items, lambda: None, show_load=True)
                        render_move_menu(item, items, f"inv_mv_{item['id']}")


    # --- RENDER UI ---
    if label == "Equipment":
        # Header with Load Bar and Add Button
        c_load, c_add = st.columns([3, 1], vertical_alignment="bottom")
        with c_load:
            if max_load is not None and current_load is not None:
                pct = min(1.0, current_load / max_load) if max_load > 0 else 1.0
                st.markdown(f"""
                <div style="margin-bottom: 0px; font-weight: bold;">Load: {current_load} / {max_load}</div>
                <div class="custom-bar-bg" style="height: 12px; margin-bottom: 0px;">
                    <div class="custom-bar-fill load-fill" style="width: {pct*100}%;"></div>
                </div>
                """, unsafe_allow_html=True)
        with c_add:
            if st.button("➕ Add Item", use_container_width=True, key=f"btn_open_add_{key}"):
                add_db_item_dialog("Equipment", ITEM_FILE, char, key, "c_inv_db", "eq")

        # Tabs for Carried vs Stash
        tab_carried, tab_stash = st.tabs(["🎒 Carried", "📦 Stash"])
        
        with tab_carried:
            # Filter roots based on filter_types if applied
            carried_roots = [i for i in items_to_show if i.get("parent_id") is None and i.get("location") == "carried"]
            if carried_roots:
                render_tree_node(carried_roots)
            else:
                st.caption("Nothing carried.")
                
        with tab_stash:
            stash_roots = [i for i in items_to_show if i.get("parent_id") is None and i.get("location") == "stash"]
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

@st.dialog("Attack Result")
def show_attack_result(weapon, char, attack_total, attack_roll, attack_mod, damage_total, damage_formula, is_crit=False, crit_damage_val=0, crit_effect="", save_callback=None):
    if isinstance(weapon, dict):
        name = weapon.get("name", "Weapon")
    else:
        name = str(weapon)
        
    st.markdown(f"### {name}")
    
    if is_crit:
        st.markdown(f"**Attack:** :red[CRITICAL HIT!] ({attack_total})")
        st.caption(f"Rolled {attack_roll} + {attack_mod}")
        if crit_effect:
            st.info(f"**Effect:** {crit_effect}")
    else:
        st.markdown(f"**Attack:** {attack_total} (d20({attack_roll}) + {attack_mod})")
    st.markdown(f"**Damage:** {damage_total} ({damage_formula})")
    
    if isinstance(weapon, dict) and weapon.get("uses_ammo", False):
        st.divider()
        c_fire, c_reload = st.columns(2)
        
        ammo_cap = weapon.get("ammo_capacity", 0)
        ammo_item_name = weapon.get("ammo_item", "")
        
        # Magazine System
        if ammo_cap > 0:
            current_ammo = weapon.get("ammo_current", 0)
            st.caption(f"Ammo: {current_ammo}/{ammo_cap}")
            
            # Fire Button
            if c_fire.button("🔥 Fire", key=f"pop_fire_{weapon['id']}", use_container_width=True, disabled=(current_ammo <= 0)):
                weapon["ammo_current"] -= 1
                if save_callback: save_callback()
                st.rerun()
            
            # Reload Button
            if c_reload.button("🔄 Reload", key=f"pop_reload_{weapon['id']}", use_container_width=True):
                missing = ammo_cap - current_ammo
                if missing > 0:
                    ammo_inv = next((i for i in char.get("inventory", []) if i.get("name") == ammo_item_name), None)
                    if ammo_inv and ammo_inv.get("quantity", 0) > 0:
                        to_load = min(missing, ammo_inv["quantity"])
                        weapon["ammo_current"] = current_ammo + to_load
                        ammo_inv["quantity"] -= to_load
                        if ammo_inv["quantity"] <= 0:
                            char["inventory"].remove(ammo_inv)
                        
                        # Decay Logic
                        weapon["reloads_count"] = weapon.get("reloads_count", 0) + 1
                        if weapon["reloads_count"] % 10 == 0:
                            weapon["decay"] = weapon.get("decay", 0) + 1
                            st.toast(f"{weapon['name']} decay increased!")
                        
                        if save_callback: save_callback()
                        st.rerun()
                    else:
                        st.error(f"No {ammo_item_name} found!")
                else:
                    st.info("Magazine full!")
        
        # Direct Feed System
        elif ammo_item_name:
            ammo_inv = next((i for i in char.get("inventory", []) if i.get("name") == ammo_item_name), None)
            qty = ammo_inv.get("quantity", 0) if ammo_inv else 0
            st.caption(f"Ammo ({ammo_item_name}): {qty}")
            
            if c_fire.button("🔥 Fire", key=f"pop_fire_{weapon['id']}", use_container_width=True, disabled=(qty <= 0)):
                if ammo_inv and qty > 0:
                    ammo_inv["quantity"] -= 1
                    if ammo_inv["quantity"] <= 0:
                        char["inventory"].remove(ammo_inv)
                    if save_callback: save_callback()
                    st.rerun()
                else:
                    st.error(f"Out of {ammo_item_name}!")

def render_character_statblock(char, save_callback=None):
    """Renders the character sheet as a visual statblock with interactive elements."""
    # Ensure stats are up to date within the fragment
    _, _, _, effective_stats, effective_skills = calculate_stats(char)
    
    primary = st.session_state.get("theme_primary", "#00ff00")
    secondary = st.session_state.get("theme_secondary", "#00b300")
    
    # --- FIXED LAYOUT CSS OVERRIDE ---
    st.markdown(f"""
    <style>
        /* Target the Statblock Container */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            padding: 5px !important;
            background-color: #000000 !important;
            border: 2px solid {primary} !important;
        }}
        
        /* Remove Gaps */
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] {{
            gap: 2px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {{
            gap: 5px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] {{
            padding: 0px !important;
        }}
        
        /* Compact Inputs */
        div[data-testid="stVerticalBlockBorderWrapper"] input {{
            background-color: #0d1117 !important;
            border: 1px solid {secondary} !important;
            color: {primary} !important;
            height: 28px !important;
            min-height: 28px !important;
            font-size: 14px !important;
        }}
        
        .stat-label {{
            font-size: 0.8em;
            color: {secondary};
            margin-bottom: 0px;
        }}
        
        /* Custom Status Buttons (Streamlit Widgets) */
        div[data-testid="stVerticalBlockBorderWrapper"] button,
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stPopover"] > button {{
            border: 1px solid {secondary} !important;
            background-color: rgba(13, 17, 23, 0.8) !important;
            color: {primary} !important;
            border-radius: 4px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 39px !important;
            height: 39px !important;
            margin: 0px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] button:hover,
        div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stPopover"] > button:hover {{
            background-color: {secondary} !important;
            color: #0d1117 !important;
            border-color: {primary} !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] button p {{
            font-size: 1.2em !important;
            color: {primary} !important;
            padding-top: 0px !important;
        }}
        
        .stat-bar-container {{
            width: 100%;
            background-color: #0d1117;
            border: 1px solid {secondary};
            border-radius: 4px;
            height: 39px;
            position: relative;
            overflow: hidden;
            top: -8px;
        }}
        .hp-fill {{ background-color: rgba(255, 50, 50, 0.7); }}
        .stamina-fill {{ background-color: rgba(200, 255, 50, 0.7); }}
        .xp-fill {{ background-color: rgba(50, 100, 255, 0.7); }}
        
        .stat-label-sm {{
            font-size: 0.7em;
            color: {secondary};
            margin-bottom: 2px;
            text-transform: uppercase;
            text-align: center;
        }}
    </style>
    """, unsafe_allow_html=True)

    # 1. SPECIAL Stats
    stat_keys = ["STR", "PER", "END", "CHA", "INT", "AGI", "LCK"]
    
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
    skills_by_stat = {k: [] for k in ["STR", "PER", "END", "CHA", "INT", "AGI", "LCK"]}
    
    # Helper for grid boxes
    def make_box(label, value, help_text=""):
        return (
            f'<div class="special-box" title="{help_text}">'
            f'<div class="special-label">{label}</div>'
            f'<div class="special-value">{value}</div>'
            f'</div>'
        )
    
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
    skills_html += f'<div style="border-bottom: 1px solid {secondary}; margin-bottom: 4px; font-weight: bold; color: {primary};">SKILLS</div>'
    for stat in ["STR", "PER", "END", "CHA", "INT", "AGI", "LCK"]:
        skill_list = skills_by_stat.get(stat, [])
        if skill_list:
            skill_list.sort(key=lambda x: x[0]) # Sort alphabetically
            s_strs = [f"{name} {val}" for name, val in skill_list]
            skills_html += f'<div><strong style="color: {secondary};">{stat}:</strong> {", ".join(s_strs)}</div>'
    skills_html += '</div>'

    # --- RENDER CONTAINER ---
    # HEADER
    bg_list = char.get("backgrounds", [])
    bg_name = bg_list[0].get("name", "Wastelander") if bg_list else "Wastelander"
    
    header_html = (
    f'<div class="statblock-header">'
    f'<span class="statblock-title">{char.get("name", "Unnamed")}</span>'
    f'<span class="statblock-meta">Lvl {char.get("level", 1)} {bg_name}</span>'
    f'</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)
    
    unique_id = char.get("name", "char")
    
    tab_stats, tab_inv, tab_feat = st.tabs(["📊 Stats", "🎒 Inventory", "🧬 Features"])

    with tab_stats:
        st.markdown(special_html, unsafe_allow_html=True)
        # INTERACTIVE STATS ROW
        st.markdown('<div class="section-header">Status</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown('<div class="stat-label-sm">Hit Points</div>', unsafe_allow_html=True)
            b_bar, b_man = st.columns([6, 1], vertical_alignment="center")

            with b_bar:
                curr = char.get("hp_current", 0)
                maxx = char.get("hp_max", 1)
                pct = min(1.0, curr / maxx) if maxx > 0 else 0
                st.markdown(f"""
                <div class="stat-bar-container">
                    <div class="stat-bar-fill hp-fill" style="width: {pct*100}%;"></div>
                    <div class="stat-bar-text">{curr} / {maxx}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with b_man:
                if st.button("⚙️", key=f"btn_man_hp_{unique_id}", use_container_width=True, help="Manage HP"):
                    hp_manager_dialog(char, maxx, save_callback)
                
        with c2:
            st.markdown('<div class="stat-label-sm">Stamina</div>', unsafe_allow_html=True)
            b_bar, b_man = st.columns([6, 1], vertical_alignment="center")

            with b_bar:
                curr = char.get("stamina_current", 0)
                maxx = char.get("stamina_max", 1)
                pct = min(1.0, curr / maxx) if maxx > 0 else 0
                st.markdown(f"""
                <div class="stat-bar-container">
                    <div class="stat-bar-fill stamina-fill" style="width: {pct*100}%;"></div>
                    <div class="stat-bar-text">{curr} / {maxx}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with b_man:
                if st.button("⚙️", key=f"btn_man_sp_{unique_id}", use_container_width=True, help="Manage Stamina"):
                    stamina_manager_dialog(char, maxx, save_callback)

        with c3:
            st.markdown('<div class="stat-label-sm">Experience</div>', unsafe_allow_html=True)
            b_bar, b_man = st.columns([6, 1], vertical_alignment="center")
            
            with b_bar:
                curr_xp = char.get("xp", 0)
                pct = (curr_xp % 1000) / 1000.0
                st.markdown(f"""
                <div class="stat-bar-container">
                    <div class="stat-bar-fill xp-fill" style="width: {pct*100}%;"></div>
                    <div class="stat-bar-text">{curr_xp}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with b_man:
                if st.button("⚙️", key=f"btn_man_xp_{unique_id}", use_container_width=True, help="Manage XP"):
                    xp_manager_dialog(char, save_callback)
        
        with c4:
            st.markdown('<div class="stat-label-sm">Caps</div>', unsafe_allow_html=True)
            b_val, b_man = st.columns([6, 1], vertical_alignment="center")
            with b_val:
                st.markdown(f"<div style='text-align: center;margin-top: -20px; font-weight: bold; color: #e6fffa; line-height: 39px;'>🪙 {char.get('caps', 0)}</div>", unsafe_allow_html=True)
            with b_man:
                if st.button("⚙️", key=f"btn_man_caps_{unique_id}", use_container_width=True, help="Manage Caps"):
                    caps_manager_dialog(char, save_callback)

        # CONDITIONS ROW
        cond1, cond2, cond3, cond4 = st.columns(4)
        
        with cond1:
            st.markdown("<div class='stat-label'>Fatigue</div>", unsafe_allow_html=True)
            f_key = f"sb_fatigue_{unique_id}"
            st.number_input("Fatigue", value=char.get("fatigue", 0), min_value=0, step=1, key=f_key, label_visibility="collapsed", on_change=update_stat_callback, args=(char, "fatigue", f_key, save_callback))
        with cond2:
            st.markdown("<div class='stat-label'>Exhaustion</div>", unsafe_allow_html=True)
            e_key = f"sb_exhaustion_{unique_id}"
            st.number_input("Exhaustion", value=char.get("exhaustion", 0), min_value=0, step=1, key=e_key, label_visibility="collapsed", on_change=update_stat_callback, args=(char, "exhaustion", e_key, save_callback))
        with cond3:
            st.markdown("<div class='stat-label'>Hunger</div>", unsafe_allow_html=True)
            h_key = f"sb_hunger_{unique_id}"
            st.number_input("Hunger", value=char.get("hunger", 0), min_value=0, step=1, key=h_key, label_visibility="collapsed", on_change=update_stat_callback, args=(char, "hunger", h_key, save_callback))
        with cond4:
            st.markdown("<div class='stat-label'>Dehydration</div>", unsafe_allow_html=True)
            d_key = f"sb_dehydration_{unique_id}"
            st.number_input("Dehydration", value=char.get("dehydration", 0), min_value=0, step=1, key=d_key, label_visibility="collapsed", on_change=update_stat_callback, args=(char, "dehydration", d_key, save_callback))

        # DERIVED & TACTICAL GRID
        st.markdown('<div class="section-header">Combat & Survival</div>', unsafe_allow_html=True)
        
        # Row 1: Combat
        grid_html = '<div class="special-grid">'
        grid_html += make_box("AC", char.get("ac", 10), "Armor Class")
        grid_html += make_box("SEQ", char.get("combat_sequence", 0), "Combat Sequence (PER Mod)")
        grid_html += make_box("AP", char.get("action_points", 0), "Action Points (AGI + 5)")
        grid_html += make_box("LOAD", f"{char.get('current_weight', 0)}/{char.get('carry_load', 0)}", "Current Load / Max Load")
        grid_html += '</div>'
        
        # Row 2: Survival / Tactical
        grid_html += '<div class="special-grid">'
        grid_html += make_box("SENSE", char.get("passive_sense", 0), "Passive Sense (12 + PER Mod)")
        grid_html += make_box("HEAL", char.get("healing_rate", 0), "Healing Rate (END + Level)")
        grid_html += make_box("RAD DC", char.get("radiation_dc", 0), "Radiation DC (12 - END Mod)")
        grid_html += make_box("NERVE", char.get("party_nerve", 0), "Party Nerve (Sum CHA Mods / 2)")
        grid_html += make_box("G.SNEAK", char.get("group_sneak", 0), "Group Sneak (Avg of Party Sneak)")
        grid_html += '</div>'
        
        st.markdown(grid_html, unsafe_allow_html=True)
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        c_skills, c_attacks = st.columns(2)
        with c_skills:
            st.markdown(skills_html, unsafe_allow_html=True)
        with c_attacks:
            st.markdown(f'<div style="border-bottom: 1px solid {secondary}; margin-bottom: 4px; font-weight: bold; color: {primary};">ATTACKS</div>', unsafe_allow_html=True)
            
            equipped_weapons = [
                i for i in char.get("inventory", []) 
                if i.get("equipped") and i.get("item_type") == "Weapon" and i.get("location") == "carried" and i.get("parent_id") is None
            ]
            
            if not equipped_weapons:
                # Add Unarmed default
                unarmed_skill = effective_skills.get("Unarmed", 0)
                str_stat = effective_stats.get("STR", 5)
                dmg_bonus = str_stat - 5
                dmg_sign = "+" if dmg_bonus >= 0 else ""
                
                c_atk_info, c_atk_roll = st.columns([4, 1], vertical_alignment="center")
                with c_atk_info:
                    st.markdown(
                        f'<div style="margin-bottom: 4px;">'
                        f'<div style="font-weight: bold; color: #e6fffa;">Unarmed <span style="color: {secondary};">+{unarmed_skill}</span></div>'
                        f'<div style="font-size: 0.85em; color: {secondary};">Damage: 1d2{dmg_sign}{dmg_bonus}</div>'
                        f'</div>', unsafe_allow_html=True
                    )
                with c_atk_roll:
                    if st.button("🎲", key=f"btn_roll_unarmed_{unique_id}", use_container_width=True):
                        atk_roll = random.randint(1, 20)
                        atk_total = atk_roll + unarmed_skill
                        dmg_roll = roll_dice("1d2")
                        
                        # Unarmed Crit Logic
                        eff_luc = effective_stats.get("LCK", 5)
                        luc_mod = eff_luc - 5
                        luck_reduction = int(luc_mod // 2)
                        base_crit = 20
                        crit_threshold = min(20, base_crit - luck_reduction)
                        is_crit = atk_roll >= crit_threshold
                        
                        dmg_total = max(1, dmg_roll + dmg_bonus)
                        show_attack_result("Unarmed", char, atk_total, atk_roll, unarmed_skill, dmg_total, f"1d2{dmg_sign}{dmg_bonus}", is_crit=is_crit, save_callback=save_callback)
            else:
                for w in equipped_weapons:
                    sub = w.get("sub_type", "Melee")
                    
                    # Skill Mapping
                    skill_map = {
                        "Archery": "Survival",
                        "Guns": "Guns",
                        "Melee": "Melee Weapons",
                        "Unarmed": "Unarmed",
                        "Energy Weapons": "Energy Weapons",
                        "Explosives": "Explosives"
                    }
                    skill_name = skill_map.get(sub, "Melee Weapons")
                    atk_bonus = effective_skills.get(skill_name, 0)
                    
                    # Damage Mapping
                    dmg_attr_map = {"Archery": "END", "Guns": "AGI", "Melee": "STR", "Unarmed": "STR", "Energy Weapons": "PER", "Explosives": "PER"}
                    attr_key = dmg_attr_map.get(sub, "STR")
                    attr_val = effective_stats.get(attr_key, 5)
                    dmg_bonus = attr_val - 5
                    dmg_sign = "+" if dmg_bonus >= 0 else ""
                    
                    # Range Calc
                    range_str = ""
                    rn = int(w.get("range_normal", 0))
                    rl = int(w.get("range_long", 0))
                    if rn > 0:
                        range_attr_map = {"Guns": "PER", "Energy Weapons": "PER", "Archery": "STR", "Explosives": "STR"}
                        stat_key = range_attr_map.get(sub, "PER")
                        stat_val = effective_stats.get(stat_key, 5)
                        rn_ft = int(stat_val * rn)
                        rl_ft = int(stat_val * rl)
                        rn_m = round(rn_ft * 0.3)
                        rl_m = round(rl_ft * 0.3)
                        range_str = f" | Range: Normal - {rn_m}m ({rn_ft}f, {rn}x) / Long - {rl_m}m ({rl_ft}f, {rl}x)"
                    
                    # Decay & Ammo Info
                    decay_val = w.get("decay", 0)
                    decay_str = f" | Decay: {decay_val}" if decay_val > 0 else ""
                    
                    ammo_str = ""
                    if w.get("ammo_capacity", 0) > 0:
                        ammo_str = f" | Ammo: {w.get('ammo_current', 0)}/{w.get('ammo_capacity', 0)}"
                    
                    crit_val = w.get("crit_threshold", 20)
                    crit_str = f" | Crit: {crit_val}+" if crit_val < 20 else ""
                    
                    c_atk_info, c_atk_act = st.columns([3.5, 1.5], vertical_alignment="center")
                    with c_atk_info:
                        st.markdown(
                            f'<div style="margin-bottom: 6px;">'
                            f'<div style="font-weight: bold; color: #e6fffa;">{w.get("name")} <span style="color: {secondary};">+{atk_bonus}</span></div>'
                            f'<div style="font-size: 0.85em; color: {secondary};">Damage: {w.get("damage_dice_count", 1)}d{w.get("damage_dice_sides", 6)}{dmg_sign}{dmg_bonus}{range_str}{ammo_str}{decay_str}{crit_str}</div>'
                            f'</div>', unsafe_allow_html=True
                        )
                    with c_atk_act:
                        c_roll, c_reload = st.columns(2)
                        
                        # Reload Button
                        if w.get("ammo_capacity", 0) > 0 and w.get("ammo_item"):
                            with c_reload:
                                if st.button("🔄", key=f"btn_reload_{w['id']}", help=f"Reload {w['name']}", use_container_width=True):
                                    current_ammo = w.get("ammo_current", 0)
                                    capacity = w.get("ammo_capacity", 0)
                                    missing = capacity - current_ammo
                                    
                                    if missing > 0:
                                        ammo_inv = next((i for i in char.get("inventory", []) if i.get("name") == w["ammo_item"]), None)
                                        if ammo_inv and ammo_inv.get("quantity", 0) > 0:
                                            to_load = min(missing, ammo_inv["quantity"])
                                            w["ammo_current"] = current_ammo + to_load
                                            ammo_inv["quantity"] -= to_load
                                            if ammo_inv["quantity"] <= 0:
                                                char["inventory"].remove(ammo_inv)
                                            
                                            # Decay Logic
                                            w["reloads_count"] = w.get("reloads_count", 0) + 1
                                            if w["reloads_count"] % 10 == 0:
                                                w["decay"] = w.get("decay", 0) + 1
                                                st.toast(f"{w['name']} decay increased!")
                                            
                                            if save_callback: save_callback()
                                            st.rerun()
                                        else:
                                            st.toast(f"No {w['ammo_item']} found!", icon="⚠️")
                                    else:
                                        st.toast("Magazine full!", icon="ℹ️")

                        with c_roll:
                            if st.button("🎲", key=f"btn_roll_{w['id']}", use_container_width=True):
                                atk_roll = random.randint(1, 20)
                                atk_total = atk_roll + atk_bonus
                                
                                # Crit Logic
                                eff_luc = effective_stats.get("LCK", 5)
                                luc_mod = eff_luc - 5
                                luck_reduction = int(luc_mod // 2)
                                base_crit = w.get("crit_threshold", 20)
                                crit_threshold = min(20, base_crit - luck_reduction)
                                is_crit = atk_roll >= crit_threshold
                                
                                d_count = w.get("damage_dice_count", 1)
                                d_sides = w.get("damage_dice_sides", 6)
                                dmg_roll = roll_dice(f"{d_count}d{d_sides}")
                                
                                crit_dmg_val = 0
                                if is_crit and w.get("crit_damage"):
                                    crit_dmg_val = roll_dice(w.get("crit_damage"))
                                
                                dmg_total = max(1, dmg_roll + dmg_bonus + crit_dmg_val)
                                dmg_formula = f"{d_count}d{d_sides}{dmg_sign}{dmg_bonus}"
                                if is_crit and crit_dmg_val > 0:
                                    dmg_formula += f" + {crit_dmg_val} (Crit)"
                                
                                show_attack_result(w, char, atk_total, atk_roll, atk_bonus, dmg_total, dmg_formula, is_crit, crit_dmg_val, w.get("crit_effect", ""), save_callback)

    with tab_inv:
        # INVENTORY / EQUIPMENT
        st.markdown('<div class="section-header">Inventory & Equipment</div>', unsafe_allow_html=True)
        if "inventory" not in char:
            char["inventory"] = []
        inventory = char["inventory"]
        
        if not inventory:
            st.caption("Inventory is empty.")
        
        # Load Bar (Full Width)
        max_load = char.get("carry_load", 0)
        curr_load = char.get("current_load", 0)
        is_over = char.get("is_overencumbered", False)
        
        bar_color = "load-fill"
        text_style = "font-weight: bold;"
        if is_over:
            bar_color = "hp-fill" # Red
            text_style = "font-weight: bold; color: #ff4444;"
            
        pct = min(1.0, curr_load / max_load) if max_load > 0 else 1.0
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px; {text_style}">
            <span>Load{' (OVERENCUMBERED)' if is_over else ''}</span>
            <span>{curr_load} / {max_load}</span>
        </div>
        <div class="custom-bar-bg" style="height: 12px; margin-bottom: 8px;">
            <div class="custom-bar-fill {bar_color}" style="width: {pct*100}%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Buttons
        c_craft, c_add = st.columns(2)
        with c_craft:
            if st.button("🛠️ Craft", use_container_width=True, key=f"sb_btn_craft_{unique_id}"):
                crafting_manager_dialog(char, save_callback)

        with c_add:
            if st.button("➕ Add Item", use_container_width=True, key=f"sb_btn_add_{unique_id}"):
                add_db_item_dialog("Equipment", ITEM_FILE, char, "inventory", f"sb_inv_sync_{unique_id}", f"sb_eq_{unique_id}", callback=save_callback)
                if save_callback: save_callback()

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
                    
                    # Visual indicator for equipped state in label
                    eq_prefix = "🔗 " if item.get("equipped", False) else ""
                    label = f"{eq_prefix}📦 {item.get('name')}{qty_str}{weight_str}{desc_str}"
                    
                    c_chk, c_exp, c_act = st.columns([0.23, 9.5, 0.58], vertical_alignment="top")
                    
                    with c_chk:
                        can_equip = (item.get("parent_id") is None and item.get("location") == "carried")
                        if can_equip:
                            is_equipped = item.get("equipped", False)
                            button_type = "primary" if is_equipped else "secondary"
                            if st.button(" ", key=f"sb_cont_eq_{item['id']}", help="Toggle Equip", use_container_width=True, type=button_type):
                                item["equipped"] = not is_equipped
                                if save_callback: save_callback()
                                st.rerun()

                    with c_act:
                        with st.popover("⚙️", use_container_width=True):
                            if st.button("Delete", key=f"sb_del_{item['id']}", type="primary", use_container_width=True):
                                confirm_delete_item_dialog(item, inventory, callback=save_callback)
                            
                            st.divider()

                            if st.button("Edit", key=f"sb_ed_{item['id']}", use_container_width=True):
                                edit_item_dialog(item, item['id'], inventory, save_callback, show_load=True)
                            render_move_menu(item, inventory, f"sb_mv_{item['id']}", callback=save_callback)
                            

                    with c_exp:
                        with st.expander(label, expanded=True):
                            if item["id"] in tree:
                                render_sb_node(tree[item["id"]])
                else:
                    # Item (Row)
                    st.markdown(f'<div style="border-top: 1px dashed {{secondary}}33; margin-top: -5px; margin-bottom: 8px;"></div>', unsafe_allow_html=True)
                    c_chk, c_lbl, c_act = st.columns([0.2, 8.2, 0.5], vertical_alignment="top")
                    
                    # Equip Checkbox
                    is_caps = item.get("name") == "Cap"
                    can_equip = (item.get("parent_id") is None and item.get("location") == "carried" and not is_caps)
                    
                    with c_chk:
                        if can_equip:
                            is_equipped = item.get("equipped", False)
                            button_type = "primary" if is_equipped else "secondary"
                            if st.button(" ", key=f"sb_eq_btn_{item['id']}", help="Toggle Equip", use_container_width=True, type=button_type):
                                item["equipped"] = not is_equipped
                                if save_callback: save_callback()
                                st.rerun()
                    
                    with c_lbl:
                        style = "color: #e6fffa;"
                        qty_str = f" (x{item.get('quantity', 1)})" if item.get('quantity', 1) > 1 else ""
                        
                        desc_parts = []
                        # Type Info
                        i_type = item.get("item_type", "Misc")
                        if i_type == "Weapon":
                            sub = item.get("sub_type", "")
                            if sub: desc_parts.append(sub)
                            if sub in ["Guns", "Energy Weapons", "Archery", "Explosives"]:
                                rn = int(item.get('range_normal', 0))
                                rl = int(item.get('range_long', 0))
                                if rn > 0:
                                    # Calculate Range using effective_stats from closure
                                    range_attr_map = {"Guns": "PER", "Energy Weapons": "PER", "Archery": "STR", "Explosives": "STR"}
                                    stat_key = range_attr_map.get(sub, "PER")
                                    stat_val = effective_stats.get(stat_key, 5)
                                    
                                    rn_ft = int(stat_val * rn)
                                    rl_ft = int(stat_val * rl)
                                    rn_m = round(rn_ft * 0.3)
                                    rl_m = round(rl_ft * 0.3)
                                    desc_parts.append(f"Range: Normal - {rn_m}m ({rn_ft}f, {rn}x) / Long - {rl_m}m ({rl_ft}f, {rl}x)")
                                    
                                    if item.get("ammo_capacity", 0) > 0:
                                        desc_parts.append(f"Ammo: {item.get('ammo_current', 0)}/{item.get('ammo_capacity', 0)}")
                        
                        if float(item.get("weight", 0)) > 0: desc_parts.append(f"{float(item['weight'])} Load")
                        if item.get("description"): desc_parts.append(item["description"])
                        if item.get("decay", 0) > 0: desc_parts.append(f"Decay: {item['decay']}")
                        
                        if i_type == "Weapon" and item.get("crit_threshold", 20) < 20:
                            desc_parts.append(f"Crit: {item['crit_threshold']}+")
                        
                        desc_html = f"<div style='font-size:0.85em; color:{secondary}; line-height: 1.2; margin-top: 2px;'>{' | '.join(desc_parts)}</div>" if desc_parts else ""
                        
                        st.markdown(f"<div style='line-height: 1.2; padding-top: 0px;'><span style='{style}'>{item.get('name')}{qty_str}</span>{desc_html}</div>", unsafe_allow_html=True)
                    
                    with c_act:
                        with st.popover("⚙️", use_container_width=True):
                            if st.button("Delete", key=f"sb_del_{item['id']}", type="primary", use_container_width=True):
                                confirm_delete_item_dialog(item, inventory, callback=save_callback)
                            
                            st.divider()

                            if st.button("Edit", key=f"sb_ed_{item['id']}", use_container_width=True):
                                edit_item_dialog(item, item['id'], inventory, save_callback, show_load=True)
                            render_move_menu(item, inventory, f"sb_mv_{item['id']}", callback=save_callback)

                            

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

    with tab_feat:
        # FEATURES & TRAITS SECTION
        st.markdown('<div class="section-header">Features & Traits</div>', unsafe_allow_html=True)
        
        # Background
        backgrounds = char.get("backgrounds", [])
        for bg in backgrounds:
            st.markdown(f'<span style="color: {primary}; font-weight: bold;">Background</span>: **{bg.get("name")}**: {bg.get("description", "")}', unsafe_allow_html=True)
        
        # Traits
        traits = char.get("traits", [])
        if traits:
            if backgrounds:
                st.markdown(f'<div style="border-top: 1px dashed {secondary}33; margin-top: 5px; margin-bottom: 5px;"></div>', unsafe_allow_html=True)
            for t in traits:
                st.markdown(f'<span style="color: {primary}; font-weight: bold;">Trait</span>: **{t.get("name")}**: {t.get("description", "")}', unsafe_allow_html=True)
        
        # Perks
        perks = char.get("perks", [])
        if perks:
            if backgrounds or traits:
                st.markdown(f'<div style="border-top: 1px dashed {secondary}33; margin-top: 5px; margin-bottom: 5px;"></div>', unsafe_allow_html=True)
            for p in perks:
                st.markdown(f'<span style="color: {primary}; font-weight: bold;">Perk</span>: **{p.get("name")}**: {p.get("description", "")}', unsafe_allow_html=True)

        # NOTES SECTION
        st.markdown('<div class="section-header">Notes</div>', unsafe_allow_html=True)
        notes_key = f"sb_notes_{unique_id}"
        st.text_area("Notes", value=char.get("notes", ""), height=400, key=notes_key, label_visibility="collapsed",
                        on_change=update_stat_callback, args=(char, "notes", notes_key, save_callback))
