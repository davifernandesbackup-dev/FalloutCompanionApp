import streamlit as st
import uuid
from utils.data_manager import load_data, save_data
from constants import EQUIPMENT_FILE, PERKS_FILE, RECIPES_FILE
from utils.item_components import render_item_form, parse_modifiers, join_modifiers
from utils.character_logic import SKILL_MAP

def render() -> None:
    st.subheader("🎒 Item & Recipe Database")

    db_type = st.radio("Select Category:", ["Equipment", "Perks", "Recipes"], horizontal=True, key="db_item_type")
    target_file = EQUIPMENT_FILE if db_type == "Equipment" else (PERKS_FILE if db_type == "Perks" else RECIPES_FILE)
    
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
                    data_list.pop(i)
                    save_data(target_file, data_list)
                    st.rerun()
        return

    # --- ADD NEW ITEM ---
    with st.expander("➕ Create New Item", expanded=False):
        mod_key = "new_db_item_mods"
        if mod_key not in st.session_state: st.session_state[mod_key] = []
        show_load = (db_type == "Equipment")
        show_type = (db_type == "Equipment")
        
        render_item_form("new_db_item", {}, mod_key, show_quantity=False, show_load=show_load, show_type=show_type)
        
        def create_db_item_callback():
            name = st.session_state.get("new_db_item_name", "")
            if name:
                if any(x['name'] == name for x in data_list):
                    st.toast("Item with this name already exists.")
                else:
                    desc = st.session_state.get("new_db_item_desc", "")
                    weight = st.session_state.get("new_db_item_weight", 0.0) if show_load else 0.0
                    item_type = st.session_state.get("new_db_item_type", "Misc")
                    sub_type = st.session_state.get("new_db_item_sub", None)
                    range_normal = st.session_state.get("new_db_item_rn", 0)
                    range_long = st.session_state.get("new_db_item_rl", 0)
                    
                    final_desc = join_modifiers(desc, st.session_state[mod_key])
                    new_item = {
                        "name": name, 
                        "description": final_desc, 
                        "weight": weight, 
                        "is_container": False,
                        "item_type": item_type,
                        "sub_type": sub_type,
                        "range_normal": range_normal,
                        "range_long": range_long
                    }
                    data_list.append(new_item)
                    save_data(target_file, data_list)
                    st.session_state[mod_key] = [] # Clear modifiers
                    
                    # Clear inputs
                    st.session_state["new_db_item_name"] = ""
                    st.session_state["new_db_item_desc"] = ""
                    st.toast(f"Created {name}")
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
        with st.expander(f"**{item.get('name')}**"):
            mod_key = f"db_item_mods_{i}"
            # Initialize modifiers from description if not already in session state
            if mod_key not in st.session_state:
                clean_desc, mod_strings = parse_modifiers(item.get("description", ""))
                st.session_state[mod_key] = mod_strings
                # We also need to ensure the form sees the clean description initially
                # But render_item_form takes 'current_values'.
                # We can construct a temporary dict with the clean description for the form
                # However, if the user has already edited the description in the form, we want that value.
                # Since render_item_form uses widgets with keys, Streamlit handles the state.
                # We just need to pass the initial value correctly ONCE.
                # But render_item_form takes 'value=' arguments.
                # If we pass clean_desc every time, it might overwrite user input if not careful?
                # No, Streamlit widgets ignore 'value' if key is in session state.
                # So passing clean_desc is fine as long as the key matches.
                # But we need to make sure we don't pass the raw description with modifiers to the text input.
                pass
            
            # Prepare values, ensuring description is clean for display
            clean_desc, _ = parse_modifiers(item.get("description", ""))
            # We create a copy to avoid modifying the actual item in the list during render
            display_values = item.copy()
            display_values["description"] = clean_desc
            
            show_load = (db_type == "Equipment")
            show_type = (db_type == "Equipment")
            form_result = render_item_form(f"db_item_{i}", display_values, mod_key, show_quantity=False, show_load=show_load, show_type=show_type)
            
            c_save, c_del = st.columns([1, 1])
            
            with c_save:
                if st.button("Save Changes", key=f"save_item_{i}", use_container_width=True):
                    final_desc = join_modifiers(form_result["description"], st.session_state[mod_key])
                    
                    item["name"] = form_result["name"]
                    item["description"] = final_desc
                    item["weight"] = form_result["weight"] if show_load else 0.0
                    item["item_type"] = form_result["item_type"]
                    item["sub_type"] = form_result["sub_type"]
                    item["range_normal"] = form_result["range_normal"]
                    item["range_long"] = form_result["range_long"]
                    # is_container is not editable here yet, defaults to False for DB items
                    
                    # We need to save the full 'data_list' which contains this 'item' object
                    save_data(target_file, data_list)
                    st.success("Saved!")
                
            with c_del:
                if st.button("🗑️ Delete", key=f"del_item_{i}", type="primary", use_container_width=True):
                    # Remove from main list
                    data_list.remove(item)
                    save_data(target_file, data_list)
                    st.rerun()