import streamlit as st
import json
import os
import shutil
from typing import Any, Union, Dict, List
from constants import BESTIARY_FILE, SAVED_FILE

# --- DATA MANAGEMENT ---
@st.cache_data
def load_data(filepath: str) -> Union[Dict, List]:
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.warning(f"⚠️ Data corruption detected in {filepath}. Resetting file and creating backup at {filepath}.bak")
        try:
            shutil.copy(filepath, f"{filepath}.bak")
        except Exception:
            pass
        return {}
    except Exception as e:
        st.error(f"Error loading {filepath}: {e}")
        return {}

def save_data(filepath: str, data: Any) -> None:
    try:
        # Serialize to string first to prevent file corruption on error
        json_str = json.dumps(data, indent=2)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_str)
        # Clear the cache so the next load gets the updated data
        load_data.clear()
    except TypeError as e:
        st.error(f"Serialization Error (Data not saved): {e}")
    except Exception as e:
        st.error(f"Error saving to {filepath}: {e}")
