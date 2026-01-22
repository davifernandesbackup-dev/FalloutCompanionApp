import streamlit as st
from utils.data_manager import load_data, save_data
from constants import EQUIPMENT_FILE, PERKS_FILE

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
        with st.form("new_item_form"):
            c1, c2 = st.columns([1, 2])
            new_name = c1.text_input("Name")
            new_desc = c2.text_input("Description / Stats")
            
            if st.form_submit_button("Create"):
                if new_name:
                    if any(x['name'] == new_name for x in data_list):
                        st.error("Item with this name already exists.")
                    else:
                        data_list.append({"name": new_name, "description": new_desc})
                        save_data(target_file, data_list)
                        st.success(f"Created {new_name}")
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
            c_edit, c_del = st.columns([3, 1])
            
            with c_edit:
                edit_name = st.text_input("Name", value=item.get("name", ""), key=f"item_name_{i}")
                edit_desc = st.text_area("Description", value=item.get("description", ""), key=f"item_desc_{i}")
                
                if st.button("Save Changes", key=f"save_item_{i}"):
                    # Update in original list
                    # We need to find the item in the original list if we filtered, 
                    # but here 'i' is the index from the sorted/filtered loop if we aren't careful.
                    # Actually, let's just update the object reference since lists are mutable.
                    # However, to save, we need to ensure the list structure is intact.
                    
                    # Better approach: Update the object in place
                    item["name"] = edit_name
                    item["description"] = edit_desc
                    
                    # We need to save the full 'data_list' which contains this 'item' object
                    save_data(target_file, data_list)
                    st.success("Saved!")
            
            with c_del:
                st.markdown("<br>", unsafe_allow_html=True) # Spacer
                if st.button("🗑️ Delete", key=f"del_item_{i}", type="primary"):
                    # Remove from main list
                    data_list.remove(item)
                    save_data(target_file, data_list)
                    st.rerun()