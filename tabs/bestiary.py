import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any
import urllib.parse
from utils.data_manager import load_data
from constants import BESTIARY_FILE

# --- UI: STATBLOCK DISPLAY ---
def render_statblock(name: str, data: Dict[str, Any], container: Any = st) -> None:
    # Renders a creature's statblock into a given Streamlit container.
    
    if not data:
        container.warning(f"No statblock data found for **{name}**.")
        return

    primary = st.session_state.get("theme_primary", "#00ff00")
    secondary = st.session_state.get("theme_secondary", "#00b300")

    # --- CSS STYLING ---
    statblock_css = f"""
    <style>
        .statblock-container {{
            border: 2px solid {secondary};
            border-radius: 8px;
            padding: 15px;
            background-color: rgba(13, 17, 23, 0.9);
            font-family: "Source Sans Pro", sans-serif;
            box-shadow: 0 0 10px {primary}33;
            margin-bottom: 10px;
        }}
        .statblock-header {{
            border-bottom: 2px solid {secondary};
            margin-bottom: 10px;
            padding-bottom: 5px;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }}
        .statblock-title {{
            font-size: 1.4em;
            font-weight: bold;
            color: {primary};
            text-transform: uppercase;
            text-shadow: 0 0 5px {primary}B3;
        }}
        .statblock-meta {{
            font-style: italic;
            color: {secondary};
            font-size: 0.9em;
        }}
        .special-grid {{
            display: flex;
            width: 100%;
            border: 2px solid {secondary};
            border-radius: 6px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .special-box {{
            text-align: center;
            flex: 1;
            border-right: 1px solid {secondary};
            background-color: #0d1117;
        }}
        .special-box:last-child {{
            border-right: none;
        }}
        .special-label {{
            background-color: {secondary};
            color: #0d1117;
            font-weight: bold;
            font-size: 0.75em;
            padding: 2px 0;
            text-shadow: none;
        }}
        .special-value {{
            font-size: 1.1em;
            font-weight: bold;
            padding: 4px 0;
            color: {primary};
        }}
        .derived-row {{
            display: flex;
            justify-content: space-around;
            background-color: rgba(0, 179, 0, 0.15);
            padding: 6px;
            border-radius: 4px;
            margin-bottom: 12px;
            font-weight: bold;
            color: #e6fffa;
        }}
        .section-header {{
            border-bottom: 1px solid {secondary};
            color: {primary};
            font-weight: bold;
            margin-top: 12px;
            margin-bottom: 6px;
            text-transform: uppercase;
            font-size: 0.9em;
        }}
        .attack-row {{
            margin-bottom: 6px;
            padding-left: 8px;
            border-left: 3px solid {secondary};
        }}
        /* CRT SCANLINE EFFECT */
        .scanlines {{
            background: linear-gradient(
                to bottom,
                rgba(255,255,255,0),
                rgba(255,255,255,0) 50%,
                rgba(0,0,0,0.2) 50%,
                rgba(0,0,0,0.2)
            );
            background-size: 100% 4px;
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            pointer-events: none;
            z-index: 10;
            opacity: 0.6;
        }}
    </style>
    """

    # --- HTML CONSTRUCTION ---
    
    # 1. SPECIAL Stats
    stats = data.get('stats', {})
    stat_keys = ["str", "per", "end", "cha", "int", "agi", "luc"]
    stat_labels = ["STR", "PER", "END", "CHA", "INT", "AGI", "LUC"]
    
    special_html = '<div class="special-grid">'
    for key, label in zip(stat_keys, stat_labels):
        val = stats.get(key, 5)
        special_html += (
            f'<div class="special-box">'
            f'<div class="special-label">{label}</div>'
            f'<div class="special-value">{val}</div>'
            f'</div>'
        )
    special_html += '</div>'

    # 2. Derived Stats
    derived_html = (
        f'<div class="derived-row">'
        f'<span>HP: {data.get("hp", 10)}</span>'
        f'<span>DEF: {data.get("defense", 1)}</span>'
        f'<span>INIT: {data.get("initiative", stats.get("per", 5) + stats.get("agi", 5))}</span>'
        f'</div>'
    )

    # 3. Skills
    skills_str = ", ".join(data.get('skills', []))
    skills_html = f'<div style="margin-bottom: 10px;"><strong>Skills:</strong> {skills_str}</div>' if skills_str else ""

    # 4. Attacks
    attacks_html = ""
    attacks = data.get('attacks', [])
    if attacks:
        attacks_html += '<div class="section-header">Attacks</div>'
        for atk in attacks:
            dmg = atk.get('damage', '').replace('$CD$', '🎲')
            effect = atk.get('effect', '-')
            attacks_html += (
                f'<div class="attack-row">'
                f'<div><strong>{atk["name"]}</strong></div>'
                f'<div style="font-size: 0.9em; color: #ccffcc;">{dmg} <span style="font-style: italic; opacity: 0.8;">({effect})</span></div>'
                f'</div>'
            )

    # Assemble Full HTML
    full_html = (
        f'<div class="statblock-container">'
        f'<div class="scanlines"></div>' # Add scanline overlay
        f'<div class="statblock-header">'
        f'<span class="statblock-title">{name}</span>'
        f'<span class="statblock-meta">Lvl {data.get("level", "?")} {data.get("type", "Normal")}</span>'
        f'</div>'
        f'{special_html}'
        f'{derived_html}'
        f'{skills_html}'
        f'{attacks_html}'
        f'</div>'
    )

    container.markdown(statblock_css + full_html, unsafe_allow_html=True)

    with container.expander("Raw Data"):
        st.json(data)

# --- DIALOG WRAPPER ---
@st.dialog("Creature Intel")
def view_statblock_dialog(name: str, data: Dict[str, Any]) -> None:
    safe_name = urllib.parse.quote(name)
    
    primary = st.session_state.get("theme_primary", "#00ff00")
    secondary = st.session_state.get("theme_secondary", "#00b300")
    
    # Use JavaScript window.open to create a "popout" style window (no toolbar, etc.)
    # We use a component to inject the HTML/JS button.
    window_name = f"sb_{safe_name.replace('%', '')}"
    
    html_code = f"""
    <html>
    <head>
    <style>
        body {{ margin: 0; padding: 0; background-color: transparent; }}
        button {{
            width: 100%;
            background-color: #161b22;
            color: {secondary};
            border: 1px solid {primary};
            border-radius: 0.5rem;
            padding: 0.25rem 0.75rem;
            min-height: 38.4px;
            font-size: 1rem;
            cursor: pointer;
            font-family: "Source Sans Pro", sans-serif;
        }}
        button:hover {{
            border-color: {secondary};
            color: {primary};
        }}
    </style>
    </head>
    <body>
        <script>
            function openPopout() {{
                // Construct URL relative to the parent window
                const url = "?popout=statblock&id={safe_name}";
                window.open(url, '{window_name}', 'width=700,height=600,menubar=no,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes');
            }}
        </script>
        <button onclick="openPopout()">Open in New Window ⧉</button>
    </body>
    </html>
    """
    components.html(html_code, height=50)
    
    render_statblock(name, data)

# --- MAIN RENDERER ---
def render_bestiary() -> None:
    # The main function to render the Bestiary tab.
    
    bestiary_data = load_data(BESTIARY_FILE)
    
    if not bestiary_data:
        st.error("Bestiary data (`bestiary.json`) not found in `data` folder!")
        return

    # --- LAYOUT & SEARCH ---
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        st.subheader("Creatures")
        search_term = st.text_input("Search Creatures...", key="bestiary_search")

        # Filter creatures based on search term
        if search_term:
            filtered_creatures = {k: v for k, v in bestiary_data.items() if search_term.lower() in k.lower()}
        else:
            filtered_creatures = bestiary_data
        
        sorted_creatures = sorted(filtered_creatures.keys())
        
        # --- CREATURE LIST ---
        # Use radio buttons for selection
        if sorted_creatures:
            # Set default selection to the first item if nothing is selected or selection is not in list
            current_selection = st.session_state.get("selected_creature", None)
            if current_selection not in sorted_creatures:
                st.session_state.selected_creature = sorted_creatures[0]
            
            st.radio(
                "Select a creature:",
                options=sorted_creatures,
                key="selected_creature",
                label_visibility="collapsed" # Hide the label as we have a subheader
            )
        else:
            st.warning("No creatures match your search.")

    # --- RIGHT COLUMN: STATBLOCK DISPLAY ---
    with right_col:
        selected_key = st.session_state.get("selected_creature")
        if selected_key and selected_key in bestiary_data:
            selected_data = bestiary_data[selected_key]
            
            with st.container():
                render_statblock(selected_key, selected_data)
        elif sorted_creatures:
            # If selection is somehow lost, default to the first in the filtered list
            st.session_state.selected_creature = sorted_creatures[0]
            st.rerun()
        else:
            # This case happens if the search yields no results
            st.info("Select a creature from the list to see its stats.")