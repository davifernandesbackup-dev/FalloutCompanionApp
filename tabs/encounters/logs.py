import streamlit as st
from utils.data_manager import load_data, save_data
from constants import SAVED_FILE, BESTIARY_FILE
from tabs.bestiary import render_statblock, view_statblock_dialog

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
        
        with st.expander(f"📁 **{biome}** ({date_str})"):
            
            # --- THREATS SECTION ---
            threats = encounter.get('threats', {})
            if threats:
                st.markdown("**⚠️ Threats**")
                
                for name, qty in threats.items():
                    c_txt, c_btn = st.columns([0.85, 0.15])
                    c_txt.markdown(f"- `{qty}x` {name}")
                    if c_btn.button("📄", key=f"saved_pop_{real_index}_{name}", help="View Statblock", use_container_width=True):
                        view_statblock_dialog(name, bestiary_data.get(name))
            else:
                st.markdown("**⚠️ Threats:** `None`")

            st.markdown("---") # Visual separator

            # --- LOOT SECTION ---
            loot = encounter.get('loot', {})
            if loot:
                st.markdown("**📦 Loot**")
                for name, qty in loot.items():
                    st.markdown(f"- `{qty}x` {name}")
            else:
                st.markdown("**📦 Loot:** `None`")

            st.divider()
            
            # --- DELETE BUTTON ---
            if st.button("🗑️ Delete Encounter", key=f"del_saved_{real_index}", use_container_width=True):
                # Find the encounter in the original list and remove it
                saved_data.pop(real_index)
                save_data(SAVED_FILE, saved_data)
                st.rerun()