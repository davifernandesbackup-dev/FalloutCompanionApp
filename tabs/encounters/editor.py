import streamlit as st
from utils.data_manager import load_data, save_data
from constants import THREAT_FILE, LOOT_FILE

# --- UI: EDITOR MODE ---
def render_editor() -> None:
    st.caption("🛠️ **Database Editor**")
    
    if "expanded_index" not in st.session_state:
        st.session_state["expanded_index"] = None

    db_type = st.radio("Target Database:", ["Threats", "Loot"], horizontal=True)
    target_file = THREAT_FILE if db_type == "Threats" else LOOT_FILE
    
    current_data = load_data(target_file)
    existing_biomes = list(current_data.keys())
    
    biome_choice = st.selectbox(
        "Select Biome:", 
        ["➕ Create New Biome..."] + existing_biomes,
        key="editor_biome_select" 
    )
    
    target_biome = biome_choice
    if biome_choice == "➕ Create New Biome...":
        target_biome = st.text_input("New Biome Name:")

    if target_biome:
        st.divider()
        
        # --- SECTION 1: ADD NEW ENTRY ---
        st.subheader(f"➕ Add to: {target_biome}")
        with st.form("add_entry_form"):
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            with c1:
                new_name = st.text_input("Name", placeholder="e.g. Radroach")
            with c2:
                new_count = st.text_input("Count", value="1", help="Dice notation (1d6)")
            with c3:
                new_weight = st.number_input("Weight", min_value=1, value=10)
            with c4:
                new_cost = st.number_input("Cost", min_value=1, value=5)
            
            submitted = st.form_submit_button("💾 Save New Entry")
            
            if submitted and new_name:
                if target_biome not in current_data:
                    current_data[target_biome] = []
                
                new_entry = {
                    "name": new_name,
                    "count": new_count,
                    "weight": new_weight,
                    "cost": new_cost 
                }
                current_data[target_biome].append(new_entry)
                st.session_state["expanded_index"] = None 
                save_data(target_file, current_data)
                st.success(f"Added **{new_name}**!")
                st.rerun()

        # --- SECTION 2: EDIT EXISTING ENTRIES ---
        if target_biome in current_data and current_data[target_biome]:
            st.divider()
            
            # HEADER WITH SAVE ALL BUTTON
            col_head_text, col_head_btn = st.columns([2, 1])
            with col_head_text:
                st.subheader(f"✏️ Edit Entries ({len(current_data[target_biome])})")
            with col_head_btn:
                # GLOBAL SAVE BUTTON
                if st.button("💾 SAVE ALL CHANGES", use_container_width=True):
                    
                    new_list = []
                    for i, entry in enumerate(current_data[target_biome]):
                        saved_name = st.session_state.get(f"ed_name_{i}", entry["name"])
                        saved_count = st.session_state.get(f"ed_count_{i}", entry["count"])
                        saved_weight = st.session_state.get(f"ed_weight_{i}", entry["weight"])
                        saved_cost = st.session_state.get(f"ed_cost_{i}", entry["cost"])
                        
                        new_list.append({
                            "name": saved_name,
                            "count": saved_count,
                            "weight": saved_weight,
                            "cost": saved_cost
                        })
                    
                    current_data[target_biome] = new_list
                    save_data(target_file, current_data)
                    st.success("All changes saved!")
                    st.rerun()

            # --- COLUMN SETUP ---
            # Create two columns for the grid
            grid_cols = st.columns(2)
            
            # LIST LOOP
            for i, entry in enumerate(current_data[target_biome]):
                
                # Determine which column this entry goes into (Left=0, Right=1)
                col_index = i % 2
                entry_key = f"enc_{i}_{entry.get('name', 'u')}"
                
                with grid_cols[col_index]:
                    name_disp = entry.get("name", "Unnamed")
                    count_disp = entry.get("count", "1")
                    weight_disp = entry.get("weight", 10)
                    cost_disp = entry.get("cost", 5)
                    
                    label = f"📝 **{name_disp}** | Qty: {count_disp} | Weight: {weight_disp} | Cost: {cost_disp}"
                    should_be_open = (i == st.session_state["expanded_index"])
                    
                    with st.expander(label, expanded=should_be_open):
                        
                        col_a, col_b, col_c, col_d = st.columns([3, 1, 1, 1])
                        
                        ed_name = col_a.text_input("Name", value=name_disp, key=f"ed_name_{entry_key}")
                        ed_count = col_b.text_input("Count", value=count_disp, key=f"ed_count_{entry_key}")
                        ed_weight = col_c.number_input("Weight", value=int(weight_disp), min_value=1, key=f"ed_weight_{entry_key}")
                        ed_cost = col_d.number_input("Cost", value=int(cost_disp), min_value=1, key=f"ed_cost_{entry_key}")
                        
                        c_update, c_delete = st.columns([1, 1])
                        
                        with c_update:
                            if st.button("💾 Update", key=f"btn_update_{entry_key}", use_container_width=True):
                                st.session_state["expanded_index"] = i
                                current_data[target_biome][i] = {
                                    "name": ed_name,
                                    "count": ed_count,
                                    "weight": ed_weight,
                                    "cost": ed_cost
                                }
                                save_data(target_file, current_data)
                                st.success(f"Updated {ed_name}!")
                                st.rerun()

                        with c_delete:
                            if st.button("🗑️ Delete", key=f"btn_del_{entry_key}", use_container_width=True):
                                st.session_state["expanded_index"] = None
                                current_data[target_biome].pop(i)
                                save_data(target_file, current_data)
                                st.warning(f"Deleted {name_disp}!")
                                st.rerun()