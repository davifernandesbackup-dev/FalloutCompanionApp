import streamlit as st
import json
from utils.data_manager import load_data, save_data
from constants import BESTIARY_FILE

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
                        "level": 1,
                        "type": "Normal",
                        "hp": 10,
                        "stats": {"str": 5, "per": 5, "end": 5, "cha": 5, "int": 5, "agi": 5, "luc": 5},
                        "attacks": []
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
                del data[selected_creature]
                save_data(BESTIARY_FILE, data)
                st.rerun()
                
        # Preview
        with st.expander("Preview Statblock"):
            st.json(creature_data)