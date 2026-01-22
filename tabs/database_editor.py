import streamlit as st
from tabs.database import encounters, items, bestiary, characters

def render() -> None:
    st.header("🛠️ General Database Editor")
    
    # Navigation for the Database Editor
    db_mode = st.radio(
        "Select Database:", 
        ["⚔️ Encounters (Threats/Loot)", "📖 Bestiary (Creatures)", "🎒 Items (Equip/Perks)", "👥 Players"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.divider()
    
    if "Encounters" in db_mode:
        encounters.render()
    elif "Bestiary" in db_mode:
        bestiary.render()
    elif "Items" in db_mode:
        items.render()
    elif "Players" in db_mode:
        characters.render()