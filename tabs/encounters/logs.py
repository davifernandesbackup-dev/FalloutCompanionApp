import streamlit as st
from utils.data_manager import load_data, save_data
from constants import SAVED_FILE, BESTIARY_FILE
from utils.statblock import render_statblock, view_statblock_dialog
from utils.dice import parse_and_roll_loot

@st.dialog("Delete Log")
def delete_log_dialog(idx, data):
    st.warning("Are you sure you want to delete this encounter log?")
    if st.button("Yes, Delete", type="primary", use_container_width=True):
        data.pop(idx)
        save_data(SAVED_FILE, data)
        st.rerun()

# --- UI: SAVED ENCOUNTERS ---
def render_saved() -> None:
    # --- Renders the saved encounters tab ---
    st.header("🗃️ Encounter Log")

    saved_data = load_data(SAVED_FILE)
    bestiary_data = load_data(BESTIARY_FILE)
    
    if not saved_data:
        st.info("No saved encounters yet. Use the 'Scan' tab to generate and save one!")
        return

    # --- Filtering and Sorting ---
    c1, c2 = st.columns(2)
    search_query = c1.text_input("Search by Biome...", key="saved_search")
    sort_order = c2.selectbox("Sort by Date:", ["Newest First", "Oldest First"], key="saved_sort")

    # Filter data
    filtered_data = [
        enc for enc in saved_data 
        if search_query.lower() in enc.get('biome', '').lower()
    ]

    # Sort data
    if sort_order == "Newest First":
        filtered_data.sort(key=lambda x: x.get('date', ''), reverse=True)
    else:
        filtered_data.sort(key=lambda x: x.get('date', ''))

    st.divider()
    
    if not filtered_data:
        st.warning("No encounters match your search.")
        return

    st.caption(f"Found **{len(filtered_data)}** matching encounters.")

    # --- Display Encounters ---
    for i, encounter in enumerate(filtered_data):
        # Use a unique index from the original list for stable keys
        try:
            real_index = saved_data.index(encounter)
        except ValueError:
            real_index = i # Fallback, though it shouldn't happen

        date_str = encounter.get('date', 'Unknown Date')
        biome = encounter.get('biome', 'Unknown Biome')
        cost = encounter.get('cost', 0)
        cost_str = f" | CR: {cost}" if cost > 0 else ""
        
        # Generate descriptive title
        threats = encounter.get('threats', {})
        if threats:
            threat_list = [f"{qty}x {name}" for name, qty in threats.items()]
            threat_str = ", ".join(threat_list)
            if len(threat_str) > 60:
                threat_str = threat_str[:57] + "..."
            title = f"📁 **{biome}**: {threat_str} ({date_str}){cost_str}"
        else:
            title = f"📁 **{biome}** ({date_str}){cost_str}"

        # Check if this expander should be kept open
        is_expanded = False
        if st.session_state.get("saved_log_open_idx") == real_index:
            is_expanded = True
            # Consume the state so it doesn't stay open on subsequent, unrelated reruns
            del st.session_state["saved_log_open_idx"]
        
        with st.expander(title, expanded=is_expanded):
            
            # --- THREATS SECTION ---
            if threats:
                st.markdown("**⚠️ Threats**")
                
                for name, qty in threats.items():
                    c_txt, c_btn = st.columns([0.85, 0.15])
                    c_txt.markdown(f"- `{qty}x` {name}")
                    if c_btn.button("📄", key=f"saved_pop_{real_index}_{name}", help="View Statblock", use_container_width=True):
                        view_statblock_dialog(name, bestiary_data.get(name))
            else:
                st.markdown("**⚠️ Threats:** `None`")

            #st.markdown("---") # Visual separator

            # --- LOOT SECTION ---
            loot = encounter.get('loot', {})
            if loot:
                st.markdown("**📦 Loot**")
                
                # Display Loot
                loot_text = []
                for name, qty in loot.items():
                    loot_text.append(f"- `{qty}x` {name}")
                st.markdown("\n".join(loot_text))
                
                # Loot Controls
                c_edit, c_reroll = st.columns([1, 1])
                
                with c_edit:
                    with st.popover("✏️ Edit Loot", use_container_width=True):
                        # Convert dict to list for editor
                        loot_list = [{"Item": k, "Quantity": v} for k, v in loot.items()]
                        edited_loot = st.data_editor(loot_list, num_rows="dynamic", key=f"edit_loot_{real_index}", hide_index=True)
                        
                        if st.button("Save Changes", key=f"save_loot_{real_index}", use_container_width=True):
                            new_loot = {row["Item"]: row["Quantity"] for row in edited_loot if row["Item"] and row["Quantity"] > 0}
                            encounter["loot"] = new_loot
                            st.session_state["saved_log_open_idx"] = real_index
                            save_data(SAVED_FILE, saved_data)
                            st.rerun()

                with c_reroll:
                    if st.button("🎲 Re-roll Loot", key=f"reroll_loot_{real_index}", use_container_width=True, help="Regenerate loot based on the threats present."):
                        temp_loot = {}
                        threats_map = encounter.get('threats', {})
                        
                        for t_name, t_count in threats_map.items():
                            # Fetch loot table from bestiary
                            b_loot = bestiary_data.get(t_name, {}).get("loot", [])
                            # Roll for each individual creature
                            for _ in range(t_count):
                                for item_str in b_loot:
                                    item_name, item_qty, qty_str, decay_val, decay_str = parse_and_roll_loot(item_str)
                                    
                                    if decay_str:
                                        key = f"{item_name} (Decay: {decay_val})"
                                        extras = []
                                        if qty_str and qty_str != "1": extras.append(qty_str)
                                        extras.append(f"{decay_str} levels of decay")
                                        key += f" [{', '.join(extras)}]"
                                        
                                        if key not in temp_loot: temp_loot[key] = {'qty': 0, 'dice': set(), 'is_decay': True}
                                        temp_loot[key]['qty'] += item_qty
                                    else:
                                        key = item_name
                                        if key not in temp_loot: temp_loot[key] = {'qty': 0, 'dice': set(), 'is_decay': False}
                                        temp_loot[key]['qty'] += item_qty
                                        if qty_str: temp_loot[key]['dice'].add(qty_str)
                        
                        new_loot_summary = {}
                        for key, data in temp_loot.items():
                            if data['is_decay']:
                                new_loot_summary[key] = data['qty']
                            else:
                                dice_strs = sorted(list(data['dice']))
                                dice_suffix = f" [{', '.join(dice_strs)}]" if dice_strs else ""
                                new_loot_summary[f"{key}{dice_suffix}"] = data['qty']
                        
                        encounter["loot"] = new_loot_summary
                        st.session_state["saved_log_open_idx"] = real_index
                        save_data(SAVED_FILE, saved_data)
                        st.rerun()

            else:
                st.markdown("**📦 Loot:** `None`")

            st.divider()
            
            # --- DELETE BUTTON ---
            if st.button("🗑️ Delete Encounter", key=f"del_saved_{real_index}", use_container_width=True):
                delete_log_dialog(real_index, saved_data)