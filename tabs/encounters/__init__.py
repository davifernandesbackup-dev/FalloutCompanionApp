import streamlit as st
from .scanner import render_scanner
from .logs import render_saved
from .editor import render_editor

def render():
    st.header("☢️ Encounter Scanner")
    
    # Using tabs within the scanner page for better organization
    tab_scan, tab_saved, tab_db = st.tabs(["Scan", "Saved Logs", "Database Editor"])
    
    with tab_scan:
        render_scanner()
        
    with tab_saved:
        render_saved()
        
    with tab_db:
        render_editor()