import streamlit as st
from utils.data_manager import load_data, save_data
from constants import EQUIPMENT_FILE, PERKS_FILE
from utils.item_components import render_item_form, parse_modifiers, join_modifiers

def render() -> None:
    st.subheader("🎒 Item Database (Equipment & Perks)")

    db_type = st.radio("Select Category:", ["Equipment", "Perks"], horizontal=True, key="db_item_type")
    target_file = EQUIPMENT_FILE if db_type == "Equipment" else PERKS_FILE
    
    data_list = load_data(target_file)
    if not isinstance(data_list, list):
        data_list = []
        
    # Sort for display
    data_list.sort(key=lambda x: x.get("name", ""))

    # --- ADD NEW ITEM ---
    with st.expander("➕ Create New Item", expanded=False):
        mod_key = "new_db_item_mods"
        if mod_key not in st.session_state: st.session_state[mod_key] = []
        
        form_result = render_item_form("new_db_item", {}, mod_key, show_quantity=False)
        
        if st.button("Create Item", key="btn_create_db_item"):
            if form_result["name"]:
                if any(x['name'] == form_result["name"] for x in data_list):
                    st.error("Item with this name already exists.")
                else:
                    final_desc = join_modifiers(form_result["description"], st.session_state[mod_key])
                    new_item = {
                        "name": form_result["name"], 
                        "description": final_desc, 
                        "weight": form_result["weight"], 
                        "is_container": False,
                        "item_type": form_result["item_type"],
                        "sub_type": form_result["sub_type"],
                        "range_normal": form_result["range_normal"],
                        "range_long": form_result["range_long"]
                    }
                    data_list.append(new_item)
                    save_data(target_file, data_list)
                    st.session_state[mod_key] = [] # Clear modifiers
                    st.success(f"Created {form_result['name']}")
                    st.rerun()
            else:
                st.warning("Name is required.")

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
            
            form_result = render_item_form(f"db_item_{i}", display_values, mod_key, show_quantity=False)
            
            c_save, c_del = st.columns([1, 1])
            
            with c_save:
                if st.button("Save Changes", key=f"save_item_{i}", use_container_width=True):
                    final_desc = join_modifiers(form_result["description"], st.session_state[mod_key])
                    
                    item["name"] = form_result["name"]
                    item["description"] = final_desc
                    item["weight"] = form_result["weight"]
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