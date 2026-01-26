import streamlit as st
from tabs.database import items, bestiary, characters

def render() -> None:
    
    # Navigation for the Database Editor
    db_mode = st.radio(
        "Select Database:", 
        ["📖 Bestiary (Creatures)", "🎒 Items (Equip/Perks)", "👥 Players"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.divider()
    
    if "Bestiary" in db_mode:
        bestiary.render()
    elif "Items" in db_mode:
        items.render()
    elif "Players" in db_mode:
        characters.render()