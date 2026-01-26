import streamlit as st
import json
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

    st.divider()

    # --- SELECT & EDIT ---
    creatures = sorted(list(data.keys()))
    selected_creature = st.selectbox("Select Creature to Edit:", [""] + creatures)

    if selected_creature and selected_creature in data:
        creature_data = data[selected_creature]
        
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