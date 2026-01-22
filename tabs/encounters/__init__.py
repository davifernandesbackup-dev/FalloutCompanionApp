import streamlit as st
from .scanner import render_scanner
from .logs import render_saved

def render():
    st.header("☢️ Encounter Scanner")
    
    # Using tabs within the scanner page for better organization
    tab_scan, tab_saved = st.tabs(["Scan", "Saved Logs"])
    
    with tab_scan:
        render_scanner()
        
    with tab_saved:
        render_saved()