import streamlit as st
import json
import pandas as pd
from utils.data_manager import load_data, save_data
from utils.statblock import calculate_cr
from constants import BESTIARY_FILE

@st.dialog("Delete Creature")
def delete_creature_dialog(key, data):
    st.warning(f"Are you sure you want to delete **{key}**?")
    if st.button("Yes, Delete", type="primary", use_container_width=True):
        del data[key]
        save_data(BESTIARY_FILE, data)
        st.rerun()

def render() -> None:
    st.subheader("📖 Bestiary Database (Monster Statblocks)")
    
    data = load_data(BESTIARY_FILE)
    if not isinstance(data, dict):
        data = {}

    # --- ADD NEW CREATURE ---
    with st.expander("➕ Create New Creature"):
        new_id = st.text_input("Creature Name (Unique ID):").strip()
        if st.button("Create"):
            if new_id:
                if new_id in data:
                    st.error("Creature already exists.")
                else:
                    # Default Template
                    data[new_id] = {
                        "name": new_id,
                        "level": 1,
                        "type": "Normal",
                        "biomes": [],
                        "sites": [],
                        "factions": [],
                        "description": "",
                        "hp": 10,
                        "sp": 10,
                        "ac": 10,
                        "dt": 0,
                        "special": {"STR": 5, "PER": 5, "END": 5, "CHA": 5, "INT": 5, "AGI": 5, "LCK": 5},
                        "skills": "",
                        "senses": "",
                        "traits": [],
                        "actions": [],
                        "loot": []
                    }
                    save_data(BESTIARY_FILE, data)
                    st.success(f"Created {new_id}")
                    st.rerun()

    # --- BULK TAGGING ---
    with st.expander("🏷️ Bulk Tagging"):
        st.markdown("Apply tags (Biomes, Sites, Factions) to multiple creatures at once.")
        
        # --- FILTERS ---
        with st.expander("🔍 Filter Selection", expanded=False):
            # Gather unique values for filters
            all_sources = sorted({item.get("source", "Unknown") for item in data.values() if isinstance(item, dict)})
            all_types = sorted({item.get("type", "Unknown") for item in data.values() if isinstance(item, dict)})
            all_biomes = sorted({b for item in data.values() if isinstance(item, dict) for b in item.get("biomes", [])})
            all_factions = sorted({f for item in data.values() if isinstance(item, dict) for f in item.get("factions", [])})
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_source = st.multiselect("Source", all_sources, key="bt_filter_source")
                filter_type = st.multiselect("Type", all_types, key="bt_filter_type")
            with col_f2:
                filter_biome = st.multiselect("Biome", all_biomes, key="bt_filter_biome")
                filter_faction = st.multiselect("Faction", all_factions, key="bt_filter_faction")
            
            filter_search = st.text_input("Search Name", key="bt_filter_search")

        # Apply Filters
        filtered_creatures = []
        for name, item in data.items():
            if not isinstance(item, dict): continue
            
            if filter_search and filter_search.lower() not in name.lower(): continue
            if filter_source and item.get("source", "Unknown") not in filter_source: continue
            if filter_type and item.get("type", "Unknown") not in filter_type: continue
            if filter_biome and not set(item.get("biomes", [])).intersection(filter_biome): continue
            if filter_faction and not set(item.get("factions", [])).intersection(filter_faction): continue
                
            filtered_creatures.append(name)
        
        filtered_creatures.sort()
        
        # --- SELECTION LIST ---
        # Manage selection state manually to support the data editor
        if "bulk_tag_creatures" not in st.session_state:
            st.session_state.bulk_tag_creatures = []
        if "bulk_tag_version" not in st.session_state:
            st.session_state.bulk_tag_version = 0
        
        current_selection_set = set(st.session_state.bulk_tag_creatures)
        # Filter out deleted items
        current_selection_set = {c for c in current_selection_set if c in data}
        
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("Select All Filtered", key="bt_select_all_btn", use_container_width=True):
            st.session_state.bulk_tag_creatures = list(current_selection_set | set(filtered_creatures))
            st.session_state.bulk_tag_version += 1
            st.rerun()
        if c_btn2.button("Clear Selection", key="bt_clear_sel_btn", use_container_width=True):
            st.session_state.bulk_tag_creatures = []
            st.session_state.bulk_tag_version += 1
            st.rerun()
            
        # Prepare data for editor as DataFrame
        df_data = {
            "Selected": [name in current_selection_set for name in filtered_creatures],
            "Creature": filtered_creatures,
            "Type": [data.get(name, {}).get("type", "Unknown") for name in filtered_creatures],
            "CR": [calculate_cr(data.get(name, {})) for name in filtered_creatures]
        }
        df = pd.DataFrame(df_data)
            
        # Use a dynamic key based on the filtered items and version to prevent index misalignment
        # and ensure programmatic resets (Clear/Select All) work correctly.
        editor_key = f"bulk_tag_editor_{hash(str(filtered_creatures))}_{st.session_state.bulk_tag_version}"

        edited_df = st.data_editor(
            df,
            column_config={
                "Selected": st.column_config.CheckboxColumn("Select", required=True, width="small"),
                "Creature": st.column_config.TextColumn("Creature", disabled=True, width="medium"),
                "Type": st.column_config.TextColumn("Type", disabled=True, width="small"),
                "CR": st.column_config.TextColumn("CR", disabled=True, width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=1000,
            key=editor_key
        )
        
        # Sync selection from editor back to state
        if not edited_df.empty:
            selected_in_editor = set(edited_df[edited_df["Selected"]]["Creature"].tolist())
        else:
            selected_in_editor = set()
            
        visible_creatures = set(filtered_creatures)
        hidden_selection = current_selection_set - visible_creatures
        
        target_creatures = list(selected_in_editor | hidden_selection)
        target_creatures.sort()
        
        # Update session state so it persists
        st.session_state.bulk_tag_creatures = target_creatures
        
        st.caption(f"Selected: {len(target_creatures)} creatures.")
        
        c_cat, c_act = st.columns(2)
        with c_cat:
            tag_category = st.selectbox("Tag Category", ["biomes", "sites", "factions"], key="bulk_tag_category")
        with c_act:
            tag_action = st.radio("Action", ["Add", "Remove"], horizontal=True, key="bulk_tag_action")
            
        # Get existing tags for suggestions
        existing_tags = sorted({t for item in data.values() if isinstance(item, dict) for t in item.get(tag_category, [])})
        
        selected_tags = st.multiselect("Select Existing Tags", existing_tags, key="bulk_tag_select")
        new_tags_input = st.text_input("Or type new tags (comma separated)", key="bulk_tag_new")
        
        if st.button("Apply Tags", type="primary"):
            if not target_creatures:
                st.warning("No creatures selected.")
            else:
                # Process tags
                tags_to_process = set(selected_tags)
                if new_tags_input:
                    tags_to_process.update([t.strip() for t in new_tags_input.split(",") if t.strip()])
                
                if not tags_to_process:
                    st.warning("No tags specified.")
                else:
                    count = 0
                    for name in target_creatures:
                        if name in data:
                            current_list = data[name].get(tag_category, [])
                            if not isinstance(current_list, list):
                                current_list = []
                            
                            current_set = set(current_list)
                            
                            if tag_action == "Add":
                                current_set.update(tags_to_process)
                            else: # Remove
                                current_set.difference_update(tags_to_process)
                            
                            data[name][tag_category] = sorted(list(current_set))
                            count += 1
                    
                    save_data(BESTIARY_FILE, data)
                    st.success(f"Updated {count} creatures!")
                    st.rerun()

    st.divider()

    # --- SELECT & EDIT ---
    creatures = sorted(list(data.keys()))
    selected_creature = st.selectbox("Select Creature to Edit:", [""] + creatures)

    if selected_creature and selected_creature in data:
        creature_data = data[selected_creature]
        
        # --- QUICK EDIT: DESCRIPTION ---
        st.markdown("#### 📝 Quick Edit")
        desc_col, save_desc_col = st.columns([4, 1], vertical_alignment="bottom")
        with desc_col:
            new_desc = st.text_area("Description", value=creature_data.get("description", ""), height=100, key="quick_desc_edit")
        with save_desc_col:
            if st.button("Update Desc.", key="save_desc_btn", use_container_width=True):
                data[selected_creature]["description"] = new_desc
                save_data(BESTIARY_FILE, data)
                st.success("Updated!")
                st.rerun()

        st.info("💡 Edit the raw JSON below. This allows full control over stats, attacks, and skills.")
        
        # JSON Editor
        # We convert dict to string for text_area, then parse back
        json_str = json.dumps(creature_data, indent=4)
        new_json_str = st.text_area("JSON Data", value=json_str, height=400)
        
        if st.button("🧮 Calculate CR", help="Estimate the Combat Rating (Cost) based on current stats."):
            try:
                # Parse the JSON from the text area to get the most up-to-date values
                temp_data = json.loads(new_json_str)
                cr = calculate_cr(temp_data)
                st.info(f"Estimated Combat Rating: **{cr}**")
            except json.JSONDecodeError:
                st.error("Invalid JSON. Please fix errors before calculating.")
        
        c_save, c_del = st.columns([1, 1])
        
        with c_save:
            if st.button("💾 Save Changes", use_container_width=True):
                try:
                    new_data = json.loads(new_json_str)
                    data[selected_creature] = new_data
                    save_data(BESTIARY_FILE, data)
                    st.success("Saved!")
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")
        
        with c_del:
            if st.button("🗑️ Delete Creature", type="primary", use_container_width=True):
                delete_creature_dialog(selected_creature, data)
                
        # Preview
        with st.expander("Preview Statblock"):
            st.json(creature_data)