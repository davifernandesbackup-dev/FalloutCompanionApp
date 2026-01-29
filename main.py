import streamlit as st
from tabs import utilities, encounters, bestiary, charactersheet, database_editor, dm_screen
from utils.data_manager import load_data
from utils.statblock import render_statblock
from constants import BESTIARY_FILE, CHARACTERS_FILE

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Wasteland Assistant", page_icon="☢️", layout="wide")

# --- THEME CONFIGURATION ---
THEMES = {
    "Default (Green)": {"primary": "#00ff00", "secondary": "#00b300"},
    "Amber (New Vegas)": {"primary": "#FFB642", "secondary": "#C58D32"},
    "Classic (Fallout 3)": {"primary": "#1AFF80", "secondary": "#12B359"},
    "Blue (Cyan)": {"primary": "#2ECFFF", "secondary": "#2090B2"},
    "White (Mint)": {"primary": "#C0FFFF", "secondary": "#86B3B3"},
    "Green (Fallout 4)": {"primary": "#14FF80", "secondary": "#0EB359"},
}

# Sync session_state with query_params to persist theme across reloads
# If a theme is selected via a widget, session_state is updated first.
# We then set the query_param to match, which triggers a rerun.
# On the next run, the query_param is present and sets the initial session_state.
if "app_theme" in st.session_state and st.session_state.app_theme != st.query_params.get("theme"):
    st.query_params["theme"] = st.session_state.app_theme

# On initial load or refresh, set session_state from query_params if they exist
if "theme" in st.query_params and st.query_params["theme"] in THEMES:
    st.session_state.app_theme = st.query_params["theme"]

# Default theme if none is set
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Default (Green)"

current_theme = THEMES.get(st.session_state.app_theme, THEMES["Default (Green)"])
primary_color = current_theme["primary"]
secondary_color = current_theme["secondary"]

# Store for other modules to access
st.session_state.theme_primary = primary_color
st.session_state.theme_secondary = secondary_color


# --- CUSTOM CSS ---
st.markdown(f"""
    <style>
    /* Hide Streamlit Header */
    header[data-testid="stHeader"],
    .stAppHeader {{
        display: none;
    }}
    /* Adjust top padding after header removal */
    .block-container {{
        padding-top: 0rem !important;
        padding-bottom: 1rem !important;
    }}
    .stApp {{
        background-color: #0d1117;
        color: {secondary_color};
    }}
    .stButton>button {{
        color: {secondary_color};
        background-color: #161b22;
        border-color: {primary_color};
        width: 100%; 
   }}
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {{
        color: {secondary_color};
        background-color: #161b22;
        -webkit-text-fill-color: {secondary_color};
    }}
    div[data-testid="stCaptionContainer"], 
    div[data-testid="stCaptionContainer"] * {{
        color: {secondary_color} !important;
        opacity: 1 !important;
        -webkit-text-fill-color: {secondary_color} !important;
    }}       
    div[data-testid="column"] {{
        padding: 10px;
        border-radius: 5px;
        background-color: #161b22; 
    }}
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
                render_statblock(target_id, data[target_id])
            else:
                # Fallback to characters
                chars = load_data(CHARACTERS_FILE)
                char_data = next((c for c in chars if c.get("name") == target_id), None)
                if char_data:
                    render_statblock(target_id, char_data)
                else:
                    st.error(f"Entity '{target_id}' not found.")
        st.stop()
        
def navigate_to(page):
    st.session_state["navigation"] = page

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("Pip-Boy 3000")
    st.divider()
    app_mode = st.radio("Select Module", ["🏠 Home", "☢️ Scanner", "📖 Bestiary", "🛠️ Utilities", "📝 Character Sheet", "🗃️ Database Editor", "🖥️ DM Screen (WIP)"], key="navigation")
    st.divider()
    st.selectbox("Interface Color", list(THEMES.keys()), key="app_theme")
    st.divider()

# Global Back Button
if app_mode != "🏠 Home" and app_mode != "🖥️ DM Screen (WIP)":
    c_back, c_title = st.columns([1, 5], vertical_alignment="center")
    with c_back:
        st.button("⬅️ Back to Title", key="global_back_home", on_click=navigate_to, args=("🏠 Home",))
    with c_title:
        if app_mode == "☢️ Scanner":
            st.subheader("☢️ Scanner")
        elif app_mode == "📖 Bestiary":
            st.subheader("📖 Bestiary")
        elif app_mode == "🛠️ Utilities":
            st.subheader("🛠️ Utilities")
        elif app_mode == "📝 Character Sheet":
            st.subheader("📝 Character Sheet")
        elif app_mode == "🗃️ Database Editor":
            st.subheader("🗃️ Database Editor")

if app_mode == "🏠 Home":
    st.title("📟 Wasteland Assistant")
    st.markdown("Welcome to the Wasteland Assistant. Select a module from the Pip-Boy menu to begin.")
    
    st.divider()
    c1, c2 = st.columns(2)
    
    with c1:
        st.button("☢️ Scanner", use_container_width=True, on_click=navigate_to, args=("☢️ Scanner",))
        st.caption("Generate encounters and loot.")
        
        st.button("📖 Bestiary", use_container_width=True, on_click=navigate_to, args=("📖 Bestiary",))
        st.caption("Browse creature database.")
        
        st.button("🛠️ Utilities", use_container_width=True, on_click=navigate_to, args=("🛠️ Utilities",))
        st.caption("Calculators and tools.")

    with c2:
        st.button("📝 Character Sheet", use_container_width=True, on_click=navigate_to, args=("📝 Character Sheet",))
        st.caption("Manage characters and inventory.")
        
        st.button("🗃️ Database Editor", use_container_width=True, on_click=navigate_to, args=("🗃️ Database Editor",))
        st.caption("Edit game data content.")

        st.button("🖥️ DM Screen (WIP)", use_container_width=True, on_click=navigate_to, args=("🖥️ DM Screen (WIP)",))
        st.caption("Customizable dashboard.")
    
    st.divider()
    st.subheader("System Settings")
    
    def update_theme_home():
        st.session_state.app_theme = st.session_state.home_theme_select
        
    try:
        current_index = list(THEMES.keys()).index(st.session_state.app_theme)
    except ValueError:
        current_index = 0
        
    st.selectbox("Interface Color", list(THEMES.keys()), index=current_index, key="home_theme_select", on_change=update_theme_home)
    
    if st.button("🔄 Clear Cache & Reload Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

elif app_mode == "☢️ Scanner":
    encounters.render()
elif app_mode == "📖 Bestiary":
    bestiary.render_bestiary()
elif app_mode == "🛠️ Utilities":
    utilities.render()
elif app_mode == "📝 Character Sheet":
    charactersheet.render_character_sheet()
elif app_mode == "🗃️ Database Editor":
    database_editor.render()
elif app_mode == "🖥️ DM Screen (WIP)":
    dm_screen.render()

