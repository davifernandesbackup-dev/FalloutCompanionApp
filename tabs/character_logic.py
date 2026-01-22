import streamlit as st
import re
import random

def get_default_character():
    return {
        "name": "New Character",
        "level": 1,
        "origin": "Vault Dweller",
        "xp": 0,
        "caps": 0,
        "stats": {
            "STR": 5, "PER": 5, "END": 5, "CHA": 5, "INT": 5, "AGI": 5, "LUC": 5
        },
        "skills": {
            "Barter": 0, "Breach": 0, "Crafting": 0, "Energy Weapons": 0, 
            "Explosives": 0, "Guns": 0, "Intimidation": 0, "Medicine": 0, 
            "Melee Weapons": 0, "Science": 0, "Sneak": 0, "Speech": 0, 
            "Survival": 0, "Unarmed": 0
        },
        "hp_max": 10, "hp_current": 10, "stamina_max": 10, "stamina_current": 10,
        "ac": 10, "combat_sequence": 0, "action_points": 10, 
        "carry_load": 50, "perks": [], "inventory": []
    }

def sync_char_widgets():
    """Syncs session state widgets with the current character sheet data."""
    if "char_sheet" not in st.session_state:
        return
    char = st.session_state.char_sheet
    
    # Basic Info
    st.session_state["c_name"] = char.get("name", "")
    st.session_state["c_origin"] = char.get("origin", "")
    st.session_state["c_level"] = char.get("level", 1)
    st.session_state["c_xp"] = char.get("xp", 0)
    st.session_state["c_hp_curr"] = char.get("hp_current", 10)
    st.session_state["c_stamina_curr"] = char.get("stamina_current", 10)
    st.session_state["c_ac"] = char.get("ac", 10)
    st.session_state["c_caps"] = char.get("caps", 0)
    st.session_state["c_perks"] = char.get("perks", [])
    st.session_state["c_inv"] = char.get("inventory", [])
    
    for stat_key, stat_value in char.get("stats", {}).items():
        st.session_state[f"stat_{stat_key}"] = stat_value
    for skill_key, skill_value in char.get("skills", {}).items():
        st.session_state[f"skill_{skill_key}"] = skill_value

def migrate_character(char):
    """Converts legacy string-based inventory/perks to list-based objects."""
    # Migrate Inventory
    if isinstance(char.get("inventory"), str):
        new_inv = []
        lines = char["inventory"].split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            equipped = False
            if line.startswith("[x]"):
                equipped = True
                line = line[3:].strip()
            elif line.startswith("[ ]"):
                equipped = False
                line = line[3:].strip()
            elif line.startswith("-"):
                equipped = True
                line = line[1:].strip()
            
            # Attempt to separate Name and Description (Name (Desc))
            match = re.match(r"^(.*)\s\((.*)\)$", line)
            if match:
                new_inv.append({"name": match.group(1), "description": match.group(2), "equipped": equipped})
            else:
                new_inv.append({"name": line, "description": "", "equipped": equipped})
        char["inventory"] = new_inv

    # Migrate Perks
    if isinstance(char.get("perks"), str):
        new_perks = []
        lines = char["perks"].split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith("-"):
                line = line[1:].strip()
            
            match = re.match(r"^(.*)\s\((.*)\)$", line)
            if match:
                new_perks.append({"name": match.group(1), "description": match.group(2), "active": True})
            else:
                new_perks.append({"name": line, "description": "", "active": True})
        char["perks"] = new_perks

def calculate_stats(char):
    """Performs all auto-calculations for the character sheet."""
    
    # 1. Parse Modifiers
    modifiers = []
    full_text = ""

    # Process Perks
    for perk in char.get("perks", []):
        if perk.get("active", True):
            full_text += f" {perk.get('description', '')}"

    # Process Inventory
    for item in char.get("inventory", []):
        if item.get("equipped", False):
            full_text += f" {item.get('description', '')}"

    matches = re.findall(r"\{([a-zA-Z0-9\s]+?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)\}", full_text)
    for stat, operator, value in matches:
        modifiers.append((stat.strip().lower(), operator, float(value)))

    def get_effective_value(base, stat_name):
        base = float(base)
        flat_sum = 0.0
        mult_additive = 0.0
        stat_name = stat_name.lower()
        for name, operator, value in modifiers:
            if name == stat_name:
                if operator == "+": flat_sum += value
                elif operator == "-": flat_sum -= value
                elif operator == "*": mult_additive += (value - 1.0)
                elif operator == "/": mult_additive += ((1.0 / value) - 1.0) if value != 0 else 0
        return base + flat_sum + (base * mult_additive)

    # 2. Effective S.P.E.C.I.A.L.
    effective_stats = {}
    for key, value in char["stats"].items():
        effective_stats[key] = get_effective_value(value, key)

    # 3. Derived Stats
    base_carry_load = effective_stats.get("STR", 5) * 10
    char["carry_load"] = int(get_effective_value(base_carry_load, "Carry Load"))
    
    base_combat_sequence = effective_stats.get("PER", 5) + effective_stats.get("AGI", 5)
    char["combat_sequence"] = int(get_effective_value(base_combat_sequence, "Combat Sequence"))
    
    base_action_points = effective_stats.get("AGI", 5) + 5
    char["action_points"] = int(get_effective_value(base_action_points, "Action Points"))
    
    base_health = effective_stats.get("END", 5) + 5
    effective_health_max = int(get_effective_value(base_health, "Max HP"))
    char["hp_max"] = effective_health_max
    
    base_stamina = effective_stats.get("AGI", 5) + 5
    effective_stamina_max = int(get_effective_value(base_stamina, "Max SP"))
    char["stamina_max"] = effective_stamina_max
    
    effective_armor_class = int(get_effective_value(10, "Armor Class"))
    char["ac"] = effective_armor_class

    return effective_health_max, effective_stamina_max, effective_armor_class, effective_stats

def roll_skill(stat_val, skill_val, name):
    """Rolls d100 against Stat + Skill."""
    target = int(stat_val + skill_val)
    roll = random.randint(1, 100)
    is_success = roll <= target
    result_text = "SUCCESS" if is_success else "FAILURE"
    return roll, target, result_text