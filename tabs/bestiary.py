import streamlit as st
from utils.data_manager import load_data
from utils.statblock import render_statblock, view_statblock_dialog
from constants import BESTIARY_FILE

# --- MAIN RENDERER ---
def render_bestiary() -> None:
    # The main function to render the Bestiary tab.
    
    bestiary_data = load_data(BESTIARY_FILE)
    
    if not bestiary_data:
        st.error("Bestiary data (`bestiary.json`) not found in `data` folder!")
        return
        
    if not isinstance(bestiary_data, dict):
        st.error("⚠️ Error: Bestiary data is formatted as a List, but must be a Dictionary. If you pasted new creatures, ensure they are inside the main `{}` object and keyed by name.")
        return

    # --- PREPARE FILTER DATA ---
    all_sources = sorted({item.get("source", "Unknown") for item in bestiary_data.values() if isinstance(item, dict)})
    all_types = sorted({item.get("type", "Unknown") for item in bestiary_data.values() if isinstance(item, dict)})
    all_sizes = sorted({item.get("size", "Unknown") for item in bestiary_data.values() if isinstance(item, dict) if "size" in item})
    all_biomes = sorted({b for item in bestiary_data.values() if isinstance(item, dict) for b in item.get("biomes", [])})
    all_sites = sorted({s for item in bestiary_data.values() if isinstance(item, dict) for s in item.get("sites", [])})
    all_factions = sorted({f for item in bestiary_data.values() if isinstance(item, dict) for f in item.get("factions", [])})

    # --- LAYOUT & SEARCH ---
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        st.subheader("Creatures")
        search_term = st.text_input("Search Creatures...", key="bestiary_search")
        
        with st.expander("Filters", expanded=False):
            filter_source = st.multiselect("Source", options=all_sources, key="bestiary_filter_source")
            filter_size = st.multiselect("Size", options=all_sizes, key="bestiary_filter_size")
            filter_type = st.multiselect("Type", options=all_types, key="bestiary_filter_type")
            filter_biome = st.multiselect("Biome", options=all_biomes, key="bestiary_filter_biome")
            filter_site = st.multiselect("Site", options=all_sites, key="bestiary_filter_site")
            filter_faction = st.multiselect("Faction", options=all_factions, key="bestiary_filter_faction")
            
            # Dynamic Subtypes based on Type selection
            if filter_type:
                relevant_subtypes = {
                    item.get("subtype") 
                    for item in bestiary_data.values() 
                    if isinstance(item, dict) and item.get("type", "Unknown") in filter_type and item.get("subtype")
                }
                all_subtypes = sorted(relevant_subtypes)
            else:
                all_subtypes = []
            
            filter_subtype = st.multiselect("Subtype", options=all_subtypes, key="bestiary_filter_subtype", disabled=(not all_subtypes))
            filter_level = st.slider("Level Range", 0, 100, (0, 100), key="bestiary_filter_level")

        # Filter Logic
        filtered_creatures = {}
        for name, data in bestiary_data.items():
            # Text Search
            if search_term and search_term.lower() not in name.lower():
                continue
            # Source Filter
            if filter_source and data.get("source", "Unknown") not in filter_source:
                continue
            # Size Filter
            if filter_size and data.get("size", "Unknown") not in filter_size:
                continue
            # Type Filter
            if filter_type and data.get("type", "Unknown") not in filter_type:
                continue
            # Biome Filter
            if filter_biome:
                if not set(data.get("biomes", [])).intersection(filter_biome):
                    continue
            # Site Filter
            if filter_site:
                if not set(data.get("sites", [])).intersection(filter_site):
                    continue
            # Faction Filter
            if filter_faction:
                if not set(data.get("factions", [])).intersection(filter_faction):
                    continue
            # Subtype Filter
            if filter_subtype and data.get("subtype") not in filter_subtype:
                continue
            # Level Filter
            level = data.get("level", 0)
            if not (filter_level[0] <= level <= filter_level[1]):
                continue
            
            filtered_creatures[name] = data
        
        sorted_creatures = sorted(filtered_creatures.keys())
        
        # --- CREATURE LIST ---
        # Use radio buttons for selection
        if sorted_creatures:
            # Set default selection to the first item if nothing is selected or selection is not in list
            current_selection = st.session_state.get("selected_creature", None)
            if current_selection not in sorted_creatures:
                st.session_state.selected_creature = sorted_creatures[0]
            
            st.radio(
                "Select a creature:",
                options=sorted_creatures,
                key="selected_creature",
                label_visibility="collapsed" # Hide the label as we have a subheader
            )
        else:
            st.warning("No creatures match your search.")

    # --- RIGHT COLUMN: STATBLOCK DISPLAY ---
    with right_col:
        selected_key = st.session_state.get("selected_creature")
        if selected_key and selected_key in bestiary_data:
            selected_data = bestiary_data[selected_key]
            
            with st.container():
                render_statblock(selected_key, selected_data)
        elif sorted_creatures:
            # If selection is somehow lost, default to the first in the filtered list
            st.session_state.selected_creature = sorted_creatures[0]
            st.rerun()
        else:
            # This case happens if the search yields no results
            st.info("Select a creature from the list to see its stats.")