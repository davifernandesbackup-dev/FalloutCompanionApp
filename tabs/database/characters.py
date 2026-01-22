import streamlit as st
import json
from utils.data_manager import load_data, save_data
from constants import CHARACTERS_FILE

def render() -> None:
    st.subheader("👥 Player Character Database")
    
    data = load_data(CHARACTERS_FILE)
    if not isinstance(data, list):
        data = []

    if not data:
        st.info("No saved characters found.")
        return

    # Helper to create unique labels
    def get_label(idx, char):
        return f"{idx+1}. {char.get('name', 'Unnamed')} (Lvl {char.get('level', 1)})"

    char_options = [get_label(i, c) for i, c in enumerate(data)]
    selected_label = st.selectbox("Select Character to Edit:", [""] + char_options)

    if selected_label:
        # Extract index from label "1. Name..." -> 0
        try:
            index = int(selected_label.split(".")[0]) - 1
            if 0 <= index < len(data):
                char_data = data[index]
                
                st.info("💡 Edit the raw JSON below. This allows full control over all character data.")
                
                # JSON Editor
                json_str = json.dumps(char_data, indent=4)
                new_json_str = st.text_area("JSON Data", value=json_str, height=500)
                
                c_save, c_del = st.columns([1, 1])
                
                with c_save:
                    if st.button("💾 Save Changes", use_container_width=True, key=f"save_char_{index}"):
                        try:
                            new_data = json.loads(new_json_str)
                            data[index] = new_data
                            save_data(CHARACTERS_FILE, data)
                            st.success("Saved!")
                            st.rerun()
                        except json.JSONDecodeError as e:
                            st.error(f"Invalid JSON: {e}")
                
                with c_del:
                    if st.button("🗑️ Delete Character", type="primary", use_container_width=True, key=f"del_char_{index}"):
                        data.pop(index)
                        save_data(CHARACTERS_FILE, data)
                        st.rerun()
        except (ValueError, IndexError):
            st.error("Error selecting character.")