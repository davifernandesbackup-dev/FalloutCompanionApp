import streamlit as st
import json
import os
from typing import Any, Union, Dict, List
from constants import THREAT_FILE, LOOT_FILE, BESTIARY_FILE, SAVED_FILE

# --- DATA MANAGEMENT ---
@st.cache_data
def load_data(filepath: str) -> Union[Dict, List]:
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error(f"Error decoding JSON from {filepath}. The file might be corrupted.")
        return {}
    except Exception as e:
        st.error(f"Error loading {filepath}: {e}")
        return {}

def save_data(filepath: str, data: Any) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    # Clear the cache so the next load gets the updated data
    load_data.clear()
