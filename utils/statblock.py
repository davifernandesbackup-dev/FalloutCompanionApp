import streamlit as st
import streamlit.components.v1 as components
from typing import Dict, Any
import urllib.parse
from utils.character_logic import calculate_stats

def convert_character_to_statblock(char: Dict[str, Any]) -> Dict[str, Any]:
    """Converts a player character dictionary into a monster statblock format."""
    # Calculate effective stats (HP, SP, AC, SPECIAL, Skills)
    eff_hp, eff_sp, eff_ac, eff_stats, eff_skills = calculate_stats(char)
    
    sb = {}
    sb["name"] = char.get("name", "Unknown")
    sb["size"] = "Medium"
    sb["type"] = "Human" # Default, could be derived if race was stored
    sb["subtype"] = "Player Character"
    sb["level"] = char.get("level", 1)
    sb["description"] = char.get("notes", "") or "A wasteland wanderer."
    
    sb["hp"] = eff_hp
    sb["sp"] = eff_sp
    sb["ac"] = eff_ac
    sb["dt"] = char.get("dt", 0)
    sb["ap"] = char.get("action_points", 0)
    
    sb["special"] = eff_stats
    
    # Format Skills
    skill_strs = []
    for s, v in eff_skills.items():
        if v > 0:
            skill_strs.append(f"{s} +{v}")
    sb["skills"] = ", ".join(skill_strs)
    
    sb["senses"] = f"Passive Sense {char.get('passive_sense', 10)}"
    sb["healing_rate"] = char.get("healing_rate", 1)
    
    # Traits & Perks
    trait_list = []
    for t in char.get("traits", []) + char.get("perks", []):
        if t.get("active", True):
            trait_list.append(f"**{t.get('name')}**: {t.get('description')}")
    sb["traits"] = trait_list
    
    # Actions (Equipped Weapons)
    actions = []
    inventory = char.get("inventory", [])
    for item in inventory:
        if item.get("equipped") and item.get("item_type") == "Weapon":
            name = item.get("name", "Weapon")
            ap_cost = item.get("ap_cost", 4)
            
            # Calculate Hit & Damage
            sub = item.get("sub_type", "Melee")
            skill_map = {"Archery": "Survival", "Guns": "Guns", "Melee": "Melee Weapons", "Unarmed": "Unarmed", "Energy Weapons": "Energy Weapons", "Explosives": "Explosives"}
            skill_name = skill_map.get(sub, "Melee Weapons")
            atk_bonus = eff_skills.get(skill_name, 0) + int(item.get("attack_bonus", 0))
            
            dmg_attr_map = {"Archery": "END", "Guns": "AGI", "Melee": "STR", "Unarmed": "STR", "Energy Weapons": "PER", "Explosives": "PER"}
            attr_key = dmg_attr_map.get(sub, "STR")
            attr_val = eff_stats.get(attr_key, 5)
            dmg_bonus = (attr_val - 5) + int(item.get("damage_bonus", 0))
            
            dmg_str = f"{item.get('damage_dice_count', 1)}d{item.get('damage_dice_sides', 6)}"
            if dmg_bonus != 0:
                dmg_str += f"{'+' if dmg_bonus > 0 else ''}{dmg_bonus}"
                
            range_info = f"Range {item.get('range_normal', 0)}/{item.get('range_long', 0)}" if item.get('range_normal', 0) > 0 else "Reach 5 ft."
            crit_str = f"Crit {item.get('crit_threshold', 20)}"
            
            actions.append(f"{ap_cost} AP **{name}**. {sub} attack: +{atk_bonus} to hit, {range_info}. {crit_str}. Hit: {dmg_str} damage.")
            
    sb["actions"] = actions
    
    # Loot
    sb["loot"] = [f"x{i.get('quantity', 1)} {i.get('name')}" for i in inventory]
    
    return sb

# --- UI: STATBLOCK DISPLAY ---
def render_statblock(name: str, data: Dict[str, Any], container: Any = st) -> None:
    # Renders a creature's statblock into a given Streamlit container.
    
    if not data:
        container.warning(f"No statblock data found for **{name}**.")
        return
        
    # Auto-convert Character Sheet data to Statblock format
    if "stats" in data and "special" not in data:
        data = convert_character_to_statblock(data)

    primary = st.session_state.get("theme_primary", "#00ff00")
    secondary = st.session_state.get("theme_secondary", "#00b300")

    is_dark = st.session_state.get("theme_mode", "Dark") == "Dark"
    bg_color = "rgba(13, 17, 23, 0.9)" if is_dark else "rgba(255, 255, 255, 0.9)"
    box_bg = "#0d1117" if is_dark else "#f0f2f6"

    # --- CSS STYLING ---
    statblock_css = f"""
    <style>
        .statblock-container {{
            border: 2px solid {secondary};
            border-radius: 8px;
            padding: 15px;
            background-color: {bg_color};
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
            background-color: {box_bg};
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
    raw_stats = data.get('special', {})
    # Normalize keys to uppercase for display
    stats = {k.upper(): v for k, v in raw_stats.items()}
    
    stat_order = ["STR", "PER", "END", "CHA", "INT", "AGI", "LCK"]
    
    special_html = '<div class="special-grid">'
    for key in stat_order:
        # Check for key or alias (LCK/LUC)
        val = stats.get(key)
        if val is None and key == "LCK":
             val = stats.get("LUC", 5)
        elif val is None:
             val = 5
             
        special_html += (
            f'<div class="special-box">'
            f'<div class="special-label">{key}</div>'
            f'<div class="special-value">{val}</div>'
            f'</div>'
        )
    special_html += '</div>'

    # 2. Derived Stats
    hp = data.get("hp", 10)
    sp = data.get("sp", 0)
    ac = data.get("ac", 10)
    dt = data.get("dt", 0)
    ap = data.get("ap", 0)
    
    derived_html = (
        f'<div class="derived-row">'
        f'<span>HP: {hp}</span>'
        f'<span>SP: {sp}</span>'
        f'<span>AC: {ac}</span>'
        f'<span>DT: {dt}</span>'
        f'<span>AP: {ap}</span>'
        f'</div>'
    )
    
    # 3. Resistances/Weaknesses
    weak = data.get("weaknesses")
    res = data.get("resistances")
    imm = data.get("immunities")
    
    res_html = ""
    if weak or res or imm:
        res_html += '<div style="font-size: 0.9em; margin-bottom: 10px;">'
        if weak: res_html += f'<div><strong>Weaknesses:</strong> {weak}</div>'
        if res: res_html += f'<div><strong>Resistances:</strong> {res}</div>'
        if imm: res_html += f'<div><strong>Immunities:</strong> {imm}</div>'
        res_html += '</div>'

    # 4. Skills & Senses
    skills = data.get("skills", "")
    if isinstance(skills, list): skills = ", ".join(skills) # Handle old format
    senses = data.get("senses", "")
    
    info_html = ""
    if skills: info_html += f'<div><strong>Skills:</strong> {skills}</div>'
    if senses: info_html += f'<div><strong>Senses:</strong> {senses}</div>'
    if info_html: info_html = f'<div style="margin-bottom: 10px;">{info_html}</div>'
    
    # Tags (Biome, Faction)
    tags_html = ""
    biomes = data.get("biomes", [])
    sites = data.get("sites", [])
    factions = data.get("factions", [])
    
    if biomes: tags_html += f'<div><strong>Biomes:</strong> {", ".join(biomes)}</div>'
    if sites: tags_html += f'<div><strong>Sites:</strong> {", ".join(sites)}</div>'
    if factions: tags_html += f'<div><strong>Factions:</strong> {", ".join(factions)}</div>'
    if tags_html: tags_html = f'<div style="margin-bottom: 10px; font-size: 0.9em; color: {secondary};">{tags_html}</div>'

    # 5. Traits
    traits_html = ""
    traits = data.get("traits", [])
    if traits:
        traits_html += '<div class="section-header">Traits</div>'
        for t in traits:
            traits_html += f'<div style="margin-bottom: 4px; font-size: 0.9em;">• {t}</div>'

    # 6. Actions
    attacks_html = ""
    attacks = data.get("actions", [])
    if attacks:
        attacks_html += '<div class="section-header">Attacks</div>'
        for atk in attacks:
            if isinstance(atk, str):
                attacks_html += f'<div class="attack-row"><div style="font-size: 0.9em;">{atk}</div></div>'
            elif isinstance(atk, dict):
                dmg = atk.get('damage', '').replace('$CD$', '🎲')
                effect = atk.get('effect', '-')
                attacks_html += (
                    f'<div class="attack-row">'
                    f'<div><strong>{atk["name"]}</strong></div>'
                    f'<div style="font-size: 0.9em; color: #ccffcc;">{dmg} <span style="font-style: italic; opacity: 0.8;">({effect})</span></div>'
                    f'</div>'
                )

    # 7. Loot
    loot_html = ""
    loot = data.get("loot", [])
    if loot:
        loot_html += '<div class="section-header">Loot</div>'
        loot_str = ", ".join(loot)
        loot_html += f'<div style="font-size: 0.9em; font-style: italic;">{loot_str}</div>'

    # Construct Display Type
    size = data.get("size", "")
    c_type = data.get("type", "Unknown")
    subtype = data.get("subtype")

    full_type_str = c_type
    if subtype:
        full_type_str = f"{c_type} ({subtype})"

    if size:
        display_type = f"{size} {full_type_str}"
    else:
        display_type = full_type_str

    # Assemble Full HTML
    full_html = (
        f'<div class="statblock-container">'
        f'<div class="scanlines"></div>' # Add scanline overlay
        f'<div class="statblock-header">'
        f'<span class="statblock-title">{data.get("name", name)}</span>'
        f'<span class="statblock-meta">Lvl {data.get("level", "?")} {display_type}</span>'
        f'</div>'
        f'<div style="font-style: italic; margin-bottom: 10px; font-size: 0.9em;">{data.get("description", "")}</div>'
        f'{special_html}'
        f'{derived_html}'
        f'{res_html}'
        f'{info_html}'
        f'{tags_html}'
        f'{traits_html}'
        f'{attacks_html}'
        f'{loot_html}'
        f'</div>'
    )

    container.markdown(statblock_css + full_html, unsafe_allow_html=True)

    base_cr = calculate_cr(data, use_ap_multiplier=False)
    advanced_cr = calculate_cr(data, use_ap_multiplier=True)

    if base_cr == advanced_cr:
        container.caption(f"**Combat Rating:** {base_cr}")
    else:
        container.caption(f"**Combat Rating:** {base_cr} | **AP-Adjusted CR:** {advanced_cr}")

    with container.expander("Raw Data"):
        st.json(data)

# --- DIALOG WRAPPER ---
@st.dialog("Creature Intel")
def view_statblock_dialog(name: str, data: Dict[str, Any]) -> None:
    safe_name = urllib.parse.quote(name)
    
    primary = st.session_state.get("theme_primary", "#00ff00")
    secondary = st.session_state.get("theme_secondary", "#00b300")
    
    # Get current theme to pass to popout
    current_theme = st.session_state.get("app_theme", "Default (Green)")
    safe_theme = urllib.parse.quote(current_theme)
    
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
                const url = "?popout=statblock&id={safe_name}&theme={safe_theme}";
                window.open(url, '{window_name}', 'width=700,height=600,menubar=no,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes');
            }}
        </script>
        <button onclick="openPopout()">Open in New Window ⧉</button>
    </body>
    </html>
    """
    components.html(html_code, height=50)
    
    render_statblock(name, data)

# --- MECHANICS ---
def calculate_cr(data: Dict[str, Any], use_ap_multiplier: bool = False) -> int:
    """Calculates the Combat Rating (CR) based on creature stats."""
    # 1. Base Score (Level * 5)
    level = data.get("level", 1)
    base_score = level * 5

    # 2. Durability Score
    hp = data.get("hp", 0)
    sp = data.get("sp", 0)
    dt = data.get("dt", 0)
    ac = data.get("ac", 10)
    durability_score = ((hp + sp) / 2) + (dt * 4) + ((ac - 10) * 2)

    # 3. Capability Score
    ap = data.get("ap", 0)
    special = data.get("special", {})
    if not isinstance(special, dict):
        special = {}
    
    # Sum SPECIAL stats (defaulting to 5 if missing)
    special_sum = sum(special.get(k, special.get("LUC" if k == "LCK" else k, 5)) for k in ["STR", "PER", "END", "CHA", "INT", "AGI", "LCK"])
    capability_score = (ap * 2) + (special_sum / 2)

    total = base_score + durability_score + capability_score

    # 4. Action Economy Multiplier
    if use_ap_multiplier:
        # Baseline AP is 10. +5% per point above, -5% per point below.
        multiplier = 1.0 + ((ap - 10) * 0.05)
        total *= multiplier

    return int(total)

def get_creature_role(data: Dict[str, Any]) -> str:
    """Determines the combat role of a creature based on stats and actions."""
    # 1. Check for Controller (Status Effects)
    actions = data.get("actions", [])
    keywords = ["Stunned", "Prone", "Blinded", "Fatigue", "Paralyzed", "Unconscious", "Grappled", "Restrained"]
    for act in actions:
        text = ""
        if isinstance(act, str): text = act
        elif isinstance(act, dict): text = f"{act.get('name','')} {act.get('effect','')}"
        
        if any(k in text for k in keywords):
            return "Controller"

    # 2. Tank vs Striker (Stat Weighting)
    hp = data.get("hp", 0)
    sp = data.get("sp", 0)
    dt = data.get("dt", 0)
    level = data.get("level", 1)
    ap = data.get("ap", 0)

    tank_score = (hp + sp) + (dt * 10)
    striker_score = (level * 5) + (ap * 5)

    return "Tank" if tank_score > striker_score else "Striker"