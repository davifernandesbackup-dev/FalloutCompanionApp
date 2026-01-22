import streamlit as st
from tabs import utilities, encounters, bestiary, charactersheet
from utils.data_manager import load_data
from constants import BESTIARY_FILE

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Wasteland Assistant", page_icon="☢️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #00b300;
    }
    .stButton>button {
        color: #00b300;
        background-color: #161b22;
        border-color: #00ff00;
        width: 100%; 
    }
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
        color: #00b300;
        background-color: #161b22;
        -webkit-text-fill-color: #00b300;
    }
    div[data-testid="stCaptionContainer"], 
    div[data-testid="stCaptionContainer"] * {
        color: #00b300 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #00b300 !important;
    }       
    div[data-testid="column"] {
        padding: 10px;
        border-radius: 5px;
        background-color: #161b22; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- POPOUT HANDLING ---
if "popout" in st.query_params:
    if st.query_params["popout"] == "statblock":
        st.markdown("""
            <style>
                header[data-testid="stHeader"] {display: none;}
                .block-container {padding-top: 1rem;}
            </style>
            """, unsafe_allow_html=True)
        target_id = st.query_params.get("id")
        if target_id:
            data = load_data(BESTIARY_FILE)
            if target_id in data:
                bestiary.render_statblock(target_id, data[target_id])
            else:
                st.error(f"Creature '{target_id}' not found.")
        st.stop()

# --- MAIN APP LAYOUT ---
st.title("📟 Wasteland Assistant")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("Pip-Boy 3000")
    st.divider()
    app_mode = st.radio("Select Module", ["☢️ Scanner", "📖 Bestiary", "🛠️ Utilities", "📝 Character Sheet"])
    st.divider()

if app_mode == "☢️ Scanner":
    encounters.render()
elif app_mode == "📖 Bestiary":
    bestiary.render_bestiary()
elif app_mode == "🛠️ Utilities":
    utilities.render()
elif app_mode == "📝 Character Sheet":
    charactersheet.render_character_sheet()