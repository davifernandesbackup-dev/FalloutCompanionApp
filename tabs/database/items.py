import streamlit as st
import uuid
from utils.data_manager import load_data, save_data
from constants import ITEM_FILE, PERKS_FILE, RECIPES_FILE
from utils.item_components import render_item_form, parse_modifiers, join_modifiers, get_item_data_from_form
from utils.character_logic import SKILL_MAP

BACKGROUNDS_FILE = "data/backgrounds.json"

@st.dialog("Delete Item")
def delete_db_item_dialog(item, data_list, target_file):
    st.warning(f"Are you sure you want to delete **{item.get('name')}**?")
    if st.button("Yes, Delete", type="primary", use_container_width=True):
        data_list.remove(item)
        save_data(target_file, data_list)
        st.rerun()

@st.dialog("Delete Recipe")
def delete_recipe_dialog(index, data_list, target_file):
    st.warning("Are you sure you want to delete this recipe?")
    if st.button("Yes, Delete", type="primary", use_container_width=True):
        data_list.pop(index)
        save_data(target_file, data_list)
        st.rerun()

def render() -> None:
    st.subheader("🎒 Item & Recipe Database")

    db_type = st.radio("Select Category:", ["Equipment", "Perks", "Backgrounds", "Recipes"], horizontal=True, key="db_item_type")
    target_file = ITEM_FILE if db_type == "Equipment" else (PERKS_FILE if db_type == "Perks" else (BACKGROUNDS_FILE if db_type == "Backgrounds" else RECIPES_FILE))
    
    data_list = load_data(target_file)
    if not isinstance(data_list, list):
        data_list = []
        
    # Sort for display
    data_list.sort(key=lambda x: x.get("name", ""))

    # --- RECIPE EDITOR LOGIC ---
    if db_type == "Recipes":
        with st.expander("➕ Create New Recipe", expanded=False):
            c_name, c_res, c_qty = st.columns([2, 2, 1])
            r_name = c_name.text_input("Recipe Name", key="new_rec_name")
            r_result = c_res.text_input("Result Item Name", key="new_rec_res")
            r_qty = c_qty.number_input("Result Qty", min_value=1, value=1, key="new_rec_qty")
            
            st.caption("Ingredients")
            if "new_rec_ing" not in st.session_state: st.session_state.new_rec_ing = []
            
            # Ingredient Adder
            c_ing_name, c_ing_qty, c_ing_add = st.columns([2, 1, 1], vertical_alignment="bottom")
            ing_name = c_ing_name.text_input("Ingredient", key="new_ing_name_in")
            ing_qty = c_ing_qty.number_input("Qty", min_value=1, value=1, key="new_ing_qty_in")
            if c_ing_add.button("Add", key="btn_add_ing_new"):
                if ing_name:
                    st.session_state.new_rec_ing.append({"name": ing_name, "quantity": ing_qty})
            
            # List Ingredients
            for i, ing in enumerate(st.session_state.new_rec_ing):
                st.text(f"- {ing['name']} (x{ing['quantity']})")
            
            if st.button("Clear Ingredients", key="btn_clr_ing_new"):
                st.session_state.new_rec_ing = []

            st.caption("Requirements")
            c_skill, c_lvl = st.columns(2)
            r_skill = c_skill.selectbox("Skill", ["None"] + sorted(list(SKILL_MAP.keys())), key="new_rec_skill")
            r_lvl = c_lvl.number_input("Level Req", min_value=0, step=5, key="new_rec_slvl")

            if st.button("Save Recipe", key="btn_save_rec_new"):
                if r_name and r_result:
                    new_recipe = {
                        "id": str(uuid.uuid4()),
                        "name": r_name,
                        "result": {"name": r_result, "quantity": r_qty},
                        "ingredients": st.session_state.new_rec_ing,
                        "skill_requirement": {"skill": r_skill if r_skill != "None" else None, "level": r_lvl}
                    }
                    data_list.append(new_recipe)
                    save_data(target_file, data_list)
                    st.session_state.new_rec_ing = []
                    st.success(f"Created recipe for {r_name}")
                    st.rerun()
                else:
                    st.warning("Name and Result Item are required.")
        
        st.divider()
        st.markdown(f"**Existing Recipes ({len(data_list)})**")
        
        for i, recipe in enumerate(data_list):
            with st.expander(f"🛠️ {recipe.get('name')}"):
                st.write(f"**Result:** {recipe['result']['name']} (x{recipe['result']['quantity']})")
                st.write("**Ingredients:**")
                for ing in recipe.get("ingredients", []):
                    st.write(f"- {ing['name']} x{ing['quantity']}")
                
                req = recipe.get("skill_requirement", {})
                if req.get("skill"):
                    st.write(f"**Requires:** {req['skill']} {req.get('level', 0)}")
                
                if st.button("🗑️ Delete Recipe", key=f"del_rec_{i}"):
                    delete_recipe_dialog(i, data_list, target_file)
        return

    # --- ADD NEW ITEM ---
    with st.expander("➕ Create New Item", expanded=False):
        mod_key = "new_db_item_mods"
        if mod_key not in st.session_state: st.session_state[mod_key] = []
        
        # Pass all items for ammo lookup
        all_items = load_data(ITEM_FILE) if db_type == "Equipment" else []
        render_item_form("new_db_item", {}, mod_key, all_items)
        
        def create_db_item_callback():
            item_data = get_item_data_from_form("new_db_item", mod_key)
            if item_data["name"]:
                if any(x['name'] == item_data["name"] for x in data_list):
                    st.toast("Item with this name already exists.")
                else:
                    new_item = item_data
                    new_item["id"] = str(uuid.uuid4())
                    data_list.append(new_item)
                    save_data(target_file, data_list)
                    st.session_state[mod_key] = [] # Clear modifiers
                    
                    # Clear inputs
                    st.session_state["new_db_item_name"] = ""
                    st.toast(f"Created {item_data['name']}")
            else:
                st.toast("Name is required.")

        st.button("Create Item", key="btn_create_db_item", on_click=create_db_item_callback)

    st.divider()
    
    # --- LIST & EDIT ITEMS ---
    st.markdown(f"**Existing {db_type} ({len(data_list)})**")
    
    search = st.text_input("Search...", key="item_db_search")
    
    filtered_list = [
        (i, item) for i, item in enumerate(data_list) 
        if search.lower() in item.get("name", "").lower()
    ]
    
    for i, item in filtered_list:
        item_key = f"db_item_{item.get('name', 'unknown')}"
        with st.expander(f"**{item.get('name')}**"):
            mod_key = f"{item_key}_mods"
            # Initialize modifiers from description if not already in session state
            if mod_key not in st.session_state:
                clean_desc, mod_strings = parse_modifiers(item.get("description", ""))
                st.session_state[mod_key] = mod_strings
            
            # Pass all items for ammo lookup
            all_items = load_data(ITEM_FILE) if db_type == "Equipment" else []
            render_item_form(item_key, item, mod_key, all_items)
            
            c_save, c_del = st.columns([1, 1])
            
            with c_save:
                if st.button("Save Changes", key=f"save_{item_key}", use_container_width=True):
                    updated_data = get_item_data_from_form(item_key, mod_key)
                    
                    # Update the item in the list
                    item.update(updated_data)
                    
                    # We need to save the full 'data_list' which contains this 'item' object
                    save_data(target_file, data_list)
                    st.success("Saved!")
                
            with c_del:
                if st.button("🗑️ Delete", key=f"del_{item_key}", type="primary", use_container_width=True):
                    delete_db_item_dialog(item, data_list, target_file)