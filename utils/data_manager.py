import streamlit as st
import json
import os
import shutil
from typing import Any, Union, Dict, List
from constants import BESTIARY_FILE, SAVED_FILE, CHARACTERS_FILE, ITEM_FILE, PERKS_FILE, RECIPES_FILE

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

# --- CLOUD SYNC (Placeholder) ---
def push_to_cloud():
    """
    Reads local JSON files and uploads them to the cloud database.
    """
    try:
        # 1. Load local data
        characters = load_data(CHARACTERS_FILE)
        bestiary = load_data(BESTIARY_FILE)
        items = load_data(ITEM_FILE)
        # ... load other files as needed

        # 2. Connect to Database (e.g., Firestore)
        # db = firestore.Client.from_service_account_info(st.secrets["gcp_service_account"])

        # 3. Upload Data
        # db.collection("app_data").document("characters").set({"data": characters})
        # db.collection("app_data").document("bestiary").set({"data": bestiary})
        
        st.toast("☁️ Data pushed to cloud successfully! (Simulated)", icon="✅")
        return True
    except Exception as e:
        st.error(f"Cloud Push Failed: {e}")
        return False

def pull_from_cloud():
    """
    Downloads data from the cloud database and overwrites local JSON files.
    """
    try:
        # 1. Connect to Database
        # db = firestore.Client.from_service_account_info(st.secrets["gcp_service_account"])

        # 2. Fetch Data
        # char_ref = db.collection("app_data").document("characters").get()
        # if char_ref.exists:
        #     save_data(CHARACTERS_FILE, char_ref.to_dict().get("data", []))
        
        # ... save other files
        
        st.toast("☁️ Data pulled from cloud! Reloading...", icon="✅")
        return True
    except Exception as e:
        st.error(f"Cloud Pull Failed: {e}")
        return False
