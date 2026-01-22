import streamlit as st
import random
from typing import List, Dict, Any
from datetime import datetime
from tabs.bestiary import render_statblock, view_statblock_dialog
from utils.data_manager import load_data, save_data
from constants import THREAT_FILE, LOOT_FILE, BESTIARY_FILE, SAVED_FILE
from utils.dice import roll_dice

# --- LOGIC: POOL GENERATOR ---
def generate_pool(items: List[Dict[str, Any]], target_budget: int, variance: float = 0.1, luck_mod: int = 0, is_threat: bool = False) -> Dict[str, int]:
    if not items:
        return {}

    target_budget = int(target_budget)
    var_amount = int(target_budget * variance)
    low_end = target_budget - var_amount
    high_end = target_budget + var_amount
    
    if low_end > high_end:
        low_end, high_end = high_end, low_end
        
    actual_budget = random.randint(low_end, max(1, high_end))
    
    if luck_mod > 0 and not is_threat:
        luck_map = {
            1: -0.10, 2: -0.03, 3: -0.02, 4: -0.01, 5: 0.00,
            6: 0.01, 7: 0.02, 8: 0.03, 9: 0.04, 10: 0.10
        }
        mod_percent = luck_map.get(luck_mod, 0.0)
        actual_budget = int(actual_budget * (1 + mod_percent))

    results = {}
    attempts = 0
    max_attempts = 50 

    while actual_budget > 0 and attempts < max_attempts:
        affordable_threshold = max(actual_budget * 1.1, 5) 
        
        valid_items = [
            i for i in items 
            if i.get('cost', 5) <= affordable_threshold
        ]
        
        if not valid_items:
            break

        if is_threat and actual_budget > 40:
             weights = [item.get('weight', 10) * item.get('cost', 5) for item in valid_items]
        else:
             weights = [item.get('weight', 10) for item in valid_items]

        selection = random.choices(valid_items, weights=weights, k=1)[0]
        
        unit_cost = selection.get('cost', 5) 
        qty_roll = roll_dice(selection['count'])
        
        if not is_threat and luck_mod > 0:
            crit_chance = luck_mod / 100.0
            if random.random() < crit_chance:
                qty_roll *= 2
        
        base_total_cost = unit_cost * qty_roll
        
        final_deduction_cost = base_total_cost
        if is_threat:
            existing_count = results.get(selection['name'], 0)
            if existing_count > 0:
                swarm_tax = 1.0 + (existing_count * 0.05)
                final_deduction_cost = int(base_total_cost * swarm_tax)

        if base_total_cost <= (actual_budget * 1.1) or (actual_budget == target_budget and base_total_cost <= target_budget * 1.5):
            name = selection['name']
            if name in results:
                results[name] += qty_roll
            else:
                results[name] = qty_roll
            
            actual_budget -= final_deduction_cost
            attempts = 0 
        else:
            attempts += 1 
            
    return results

# --- UI: SCANNER MODE ---
def render_scanner() -> None:
    # Renders the scanner mode UI
    threat_data = load_data(THREAT_FILE)
    loot_data = load_data(LOOT_FILE)
    bestiary_data = load_data(BESTIARY_FILE)

    if not threat_data and not loot_data:
        st.error("Database not found. Please add data in the 'Database Editor' tab.")
        return

    all_biomes = sorted(list(set(threat_data.keys()) | set(loot_data.keys())))
    diff_map = {"Easy": 20, "Medium": 50, "Hard": 100, "Deadly": 200}

    # --- INITIALIZE STATE ---
    if "scan_results" not in st.session_state or st.session_state.scan_results is None:
        st.session_state.scan_results = {
            "biome": "Manual",
            "threats": {},
            "loot": {},
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    # --- CALLBACK ---
    def update_budget_from_preset():
        selected_name = st.session_state.get("scanner_preset_select", "Medium")
        if selected_name in diff_map:
            st.session_state.scanner_budget_input = diff_map[selected_name]

    # --- LAYOUT ---
    st.subheader("Scan Parameters")
    c1, c2, c3 = st.columns([2, 1, 1])
    
    with c1:
        biome = st.selectbox("Sector Biome:", all_biomes, key="scanner_biome_select")
    with c2:
        st.selectbox(
            "Difficulty Preset:", 
            options=list(diff_map.keys()),
            index=1, # Default to Medium
            key="scanner_preset_select",
            on_change=update_budget_from_preset
        )
    with c3:
        luck = st.number_input("Party Luck:", 1, 10, 5)

    # Use a separate key for the budget input
    if "scanner_budget_input" not in st.session_state:
        st.session_state.scanner_budget_input = diff_map["Medium"]
        
    budget = st.number_input(
        "Threat Budget (Pts):", 
        min_value=1, 
        key="scanner_budget_input",
        help="Determines the 'cost' of enemies spawned. Higher is more dangerous."
    )

    st.divider()

    # --- SCAN BUTTON ---
    if st.button("☢️ SCAN SECTOR", use_container_width=True, type="primary"):
        threat_list = threat_data.get(biome, [])
        loot_list = loot_data.get(biome, [])
        
        threat_results = generate_pool(threat_list, budget, is_threat=True)
        loot_budget = int((budget * 0.6) + (luck * 2))
        loot_results = generate_pool(loot_list, loot_budget, luck_mod=luck)
        
        st.session_state.scan_results = {
            "biome": biome,
            "threats": threat_results,
            "loot": loot_results,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        st.rerun()

    st.divider()

    # --- ENCOUNTER BUILDER UI ---
    st.subheader("Encounter Builder")
    
    # Flatten data for library views
    all_threats = {}
    for biome_items in threat_data.values():
        for item in biome_items:
            all_threats[item['name']] = item
            
    all_loot = {}
    for biome_items in loot_data.values():
        for item in biome_items:
            all_loot[item['name']] = item

    # Layout: Library (Left) | Builder (Right)
    col_lib, col_build = st.columns([1, 1])

    # --- LEFT COLUMN: LIBRARY ---
    with col_lib:
        st.markdown("#### 📚 Library")
        search_q = st.text_input("Search Library...", key="lib_search", label_visibility="collapsed", placeholder="Search...").lower()
        lib_tab1, lib_tab2 = st.tabs(["Threats", "Loot"])

        # --- CALLBACKS ---
        def increment_qty(cat, name):
            res = st.session_state.scan_results
            curr = res[cat].get(name, 0)
            res[cat][name] = curr + 1
            
        def decrement_qty(cat, name):
            res = st.session_state.scan_results
            curr = res[cat].get(name, 0)
            if curr > 0:
                new_val = curr - 1
                if new_val <= 0:
                    if name in res[cat]:
                        del res[cat][name]
                else:
                    res[cat][name] = new_val

        def render_library_list(source_dict, category):
            # Filter items
            filtered_names = [name for name in source_dict.keys() if search_q in name.lower()]
            filtered_names.sort()

            if not filtered_names:
                st.caption("No items found.")
                return

            # Render list
            for name in filtered_names:
                current_qty = st.session_state.scan_results.get(category, {}).get(name, 0)
                
                # Dynamic Layout based on category (Loot doesn't need 'View' button)
                if category == "threats":
                    # Name | View | - | +
                    c_name, c_view, c_min, c_plus = st.columns([4, 1, 1, 1], vertical_alignment="center")
                else:
                    # Name | - | +
                    c_name, c_min, c_plus = st.columns([5, 1, 1], vertical_alignment="center")
                    c_view = None
                
                display_name = f"**{name}**" if current_qty > 0 else name
                if current_qty > 0:
                    display_name += f" `x{current_qty}`"
                
                c_name.markdown(display_name, help=name) # Tooltip for truncated names
                
                if category == "threats" and c_view and name in bestiary_data:
                    if c_view.button("📄", key=f"lib_view_{category}_{name}", help="View Statblock"):
                        view_statblock_dialog(name, bestiary_data.get(name))

                c_min.button("➖", key=f"lib_min_{category}_{name}", on_click=decrement_qty, args=(category, name))
                
                c_plus.button("➕", key=f"lib_plus_{category}_{name}", on_click=increment_qty, args=(category, name))

        with lib_tab1:
            render_library_list(all_threats, "threats")
        
        with lib_tab2:
            render_library_list(all_loot, "loot")

    # --- RIGHT COLUMN: CURRENT ENCOUNTER ---
    with col_build:
        st.markdown("#### ⚔️ Active Encounter")
        res = st.session_state.scan_results

        # Threats List
        st.caption("Threats")
        if res['threats']:
            for name, qty in list(res['threats'].items()):
                c_info, c_btn = st.columns([0.85, 0.15])
                c_info.info(f"**{qty}x** {name}")
                if c_btn.button("📄", key=f"pop_{name}", help="View Statblock", use_container_width=True):
                    view_statblock_dialog(name, bestiary_data.get(name))
        else:
            st.markdown("*No threats added.*")

        st.divider()

        # Loot List
        st.caption("Loot")
        if res['loot']:
            for name, qty in list(res['loot'].items()):
                st.success(f"**{qty}x** {name}")
        else:
            st.markdown("*No loot added.*")

        st.divider()
        
        # --- SAVE BUTTON ---
        if st.button("💾 Save Encounter to Log", use_container_width=True):
            current_saves = load_data(SAVED_FILE)
            if not isinstance(current_saves, list):
                current_saves = []
            
            # Prepend to make newest appear first
            current_saves.insert(0, res) 
            save_data(SAVED_FILE, current_saves)
            st.toast("Encounter Saved!", icon="💾")
            # Clear results after saving
            st.session_state.scan_results = None
            st.rerun()
            
        # --- REMOVE ALL BUTTON ---
        if st.button("🗑️ Remove All", use_container_width=True, type="secondary"):
            st.session_state.scan_results["threats"] = {}
            st.session_state.scan_results["loot"] = {}
            st.rerun()