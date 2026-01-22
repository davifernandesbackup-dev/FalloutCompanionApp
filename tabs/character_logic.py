import streamlit as st
import re
import random
import uuid

SKILL_MAP = {
    "Barter": ["CHA"],
    "Breach": ["PER", "INT"],
    "Crafting": ["INT"],
    "Energy Weapons": ["PER"],
    "Explosives": ["PER"],
    "Guns": ["AGI"],
    "Intimidation": ["STR", "CHA"],
    "Medicine": ["PER", "INT"],
    "Melee Weapons": ["STR"],
    "Science": ["INT"],
    "Sneak": ["AGI"],
    "Speech": ["CHA"],
    "Survival": ["END"],
    "Unarmed": ["STR"]
}

def get_default_character():
    return {
        "name": "New Character",
        "level": 1,
        "origin": "Vault Dweller",
        "xp": 0,
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

    # Migrate Container/ID System
    inventory = char.get("inventory", [])
    for item in inventory:
        if "id" not in item: item["id"] = str(uuid.uuid4())
        if "parent_id" not in item: item["parent_id"] = None
        if "is_container" not in item: item["is_container"] = False
        if "quantity" not in item: item["quantity"] = 1
        if "location" not in item: item["location"] = "carried" # carried, stash

    # Ensure Perks have IDs (required for edit dialog)
    for perk in char.get("perks", []):
        if "id" not in perk: perk["id"] = str(uuid.uuid4())

    # Migrate Caps to Item
    if "caps" in char:
        caps_val = char.pop("caps")
        if isinstance(caps_val, int) and caps_val > 0:
            # Check if Caps item already exists
            if not any(i["name"] == "Caps" for i in inventory):
                inventory.append({"id": str(uuid.uuid4()), "name": "Caps", "description": "Currency", "weight": 0.0, "quantity": caps_val, "equipped": False, "location": "carried", "parent_id": None, "is_container": False})


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
        # Only apply modifiers if item is Carried (root)
        # Containers apply automatically if carried. Items must be equipped.
        is_carried_root = (item.get("location") == "carried" and item.get("parent_id") is None)
        
        if is_carried_root:
            if item.get("is_container", False) or item.get("equipped", False):
                full_text += f" {item.get('description', '')} "

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

    # 3. Effective Skills
    # Luck Bonus: Floor(Mod/2) if positive, else -1
    eff_luc = effective_stats.get("LUC", 5)
    luc_mod = eff_luc - 5
    luck_bonus = int(luc_mod // 2) if luc_mod >= 0 else -1

    effective_skills = {}
    for key, value in char.get("skills", {}).items():
        # Calculate Stat Bonus (Max of associated stats - 5)
        stat_bonus = 0
        if key in SKILL_MAP:
            stat_mods = [effective_stats.get(s, 5) - 5 for s in SKILL_MAP[key]]
            # For skills with multiple stats, use the one with the highest modifier
            stat_bonus = int(max(stat_mods))
        
        # Base = Ranks (value) + Stat Bonus + Luck Bonus
        derived_base = value + stat_bonus + luck_bonus
        
        # Apply external modifiers (Perks/Items) to the derived base
        effective_skills[key] = int(get_effective_value(derived_base, key))

    # Calculate Current Weight
    inventory = char.get("inventory", [])
    
    # Build Tree for recursive weight
    item_map = {item["id"]: item for item in inventory}
    children_map = {}
    for item in inventory:
        pid = item.get("parent_id")
        if pid:
            if pid not in children_map: children_map[pid] = []
            children_map[pid].append(item)

    def get_total_weight(item_id):
        item = item_map.get(item_id)
        if not item: return 0.0
        # Self weight
        w = float(item.get("weight", 0.0)) * item.get("quantity", 1)
        # Children weight
        for child in children_map.get(item_id, []):
            w += get_total_weight(child["id"])
        return w

    current_weight = 0.0
    carried_caps = 0

    for item in inventory:
        # Only count weight for root items in "carried"
        if item.get("parent_id") is None and item.get("location") == "carried":
            current_weight += get_total_weight(item["id"])
        
        # Count caps (anywhere in carried hierarchy)
        # We need to check if the item is effectively carried
        if item.get("name") == "Caps":
            # Traverse up to check if root is carried
            curr = item
            is_carried = False
            while True:
                if curr.get("parent_id") is None:
                    if curr.get("location") == "carried":
                        is_carried = True
                    break
                curr = item_map.get(curr.get("parent_id"))
                if not curr: break # Orphaned
            
            if is_carried:
                carried_caps += item.get("quantity", 0)
                # Caps weight: 50 caps = 1 Load
                # Note: If caps are inside a container, their weight is added via get_total_weight recursion above?
                # Wait, get_total_weight adds weight of children. 
                # If Caps have weight 0 in DB, we need to add their calculated weight.
                # But usually Caps item has 0 weight in definition.
                # So we add caps weight globally or per stack?
                # Let's add global caps weight to current_weight for simplicity, 
                # OR we assume the Caps item has 0 weight and we add (total_caps / 50) at the end.
                # The prompt says "caps... are not equipment... cant be equipped".
                # Let's add the calculated weight here.
    
    current_weight += carried_caps / 50.0
    
    char["current_weight"] = round(current_weight, 1)
    char["caps"] = carried_caps # Update display value

    # 4. Derived Stats
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

    return effective_health_max, effective_stamina_max, effective_armor_class, effective_stats, effective_skills

def roll_skill(stat_val, skill_val, name):
    """Rolls d100 against Stat + Skill."""
    target = int(stat_val + skill_val)
    roll = random.randint(1, 100)
    is_success = roll <= target
    result_text = "SUCCESS" if is_success else "FAILURE"
    return roll, target, result_text