import streamlit as st
import random
from typing import List, Dict, Any
from datetime import datetime
from utils.statblock import render_statblock, view_statblock_dialog, calculate_cr, get_creature_role
from utils.data_manager import load_data, save_data
from constants import BESTIARY_FILE, SAVED_FILE, CHARACTERS_FILE
from utils.dice import parse_and_roll_loot

# --- UI: SCANNER MODE ---
def render_scanner() -> None:
    bestiary = load_data(BESTIARY_FILE)
    if not bestiary:
        st.error("Bestiary data not found.")
        return

    if "current_encounter" not in st.session_state:
        st.session_state.current_encounter = []

    col_builder, col_viewer = st.columns([1, 1.5])

    with col_builder:
        st.markdown("### 📡 Signal Source")
        
        # Filters
        with st.expander("Signal Filters", expanded=True):
            if st.button("Clear All Filters", key="scanner_clear_filters", use_container_width=True):
                st.session_state.scanner_search = ""
                st.session_state.scanner_level = (0, 50)
                st.session_state.scanner_types = []
                st.session_state.scanner_biomes = []
                st.session_state.scanner_sites = []
                st.session_state.scanner_factions = []
                st.rerun()

            if "scanner_level" not in st.session_state:
                st.session_state.scanner_level = (0, 50)

            search = st.text_input("Search Frequency", placeholder="Creature Name...", key="scanner_search")
            min_lvl, max_lvl = st.slider("Threat Level", 0, 50, key="scanner_level")
            
            # Type Filter
            all_types = sorted(list(set(c.get("type", "Unknown") for c in bestiary.values() if isinstance(c, dict))))
            selected_types = st.multiselect("Signal Type", all_types, key="scanner_types")
            
            all_biomes = sorted({b for item in bestiary.values() if isinstance(item, dict) for b in item.get("biomes", [])})
            selected_biomes = st.multiselect("Biome", all_biomes, key="scanner_biomes")
            
            all_sites = sorted({s for item in bestiary.values() if isinstance(item, dict) for s in item.get("sites", [])})
            selected_sites = st.multiselect("Site", all_sites, key="scanner_sites")
            
            all_factions = sorted({f for item in bestiary.values() if isinstance(item, dict) for f in item.get("factions", [])})
            selected_factions = st.multiselect("Faction", all_factions, key="scanner_factions")

        # Filter Logic
        candidates = []
        for name, stats in bestiary.items():
            if not isinstance(stats, dict): continue
            
            if search.lower() in name.lower():
                lvl = stats.get("level", 0)
                if min_lvl <= lvl <= max_lvl:
                    if not selected_types or stats.get("type") in selected_types:
                        # Biome Check
                        if selected_biomes and not set(stats.get("biomes", [])).intersection(selected_biomes):
                            continue
                        # Site Check
                        if selected_sites and not set(stats.get("sites", [])).intersection(selected_sites):
                            continue
                        # Faction Check
                        if selected_factions and not set(stats.get("factions", [])).intersection(selected_factions):
                            continue
                        
                        candidates.append(name)
        
        candidates.sort()
               
        # --- BUDGET GENERATOR ---
        st.markdown("#### 💰 Budget Mode")
        
        c_adv1, c_adv2 = st.columns(2)
        with c_adv1:
            enable_ap_multiplier = st.checkbox("Action Economy Tax (WIP)", value=True, help="Adjusts Action Points (AP) weight towards CR more heavily.")
            enable_group_multiplier = st.checkbox("Group Multiplier", value=True, help="Applies a mild tax for larger groups of enemies.")
        with c_adv2:
            enable_weight_bias = st.checkbox("Prefer Stronger Enemies", value=True, help="If enabled, the generator is more likely to pick higher CR enemies to fill the budget. If disabled, selection is purely random.")
            enable_role_synergy_tax = st.checkbox("Role Synergy Tax (WIP)", value=False, help="Applies a bonus cost when complementary roles (e.g., Tank + Striker) are present in the encounter.")

        # Calculate Party CR for Presets
        party_data = load_data(CHARACTERS_FILE)
        party_cr = 0
        if isinstance(party_data, list) and party_data:
            
            # Helper to format display labels dynamically
            def get_party_label(index):
                if index < 0 or index >= len(party_data): return "Unknown"
                c = party_data[index]
                c_stats = {
                    "level": c.get("level", 1),
                    "hp": c.get("hp_max", 10),
                    "sp": c.get("stamina_max", 10),
                    "ac": c.get("ac", 10),
                    "dt": 0, 
                    "ap": c.get("action_points", 10),
                    "special": c.get("stats", {})
                }
                indiv_cr = calculate_cr(c_stats, use_ap_multiplier=enable_ap_multiplier)
                return f"{index+1}. {c.get('name', 'Unnamed')} (Lvl {c.get('level', 1)}) [CR: {indiv_cr}]"

            party_indices = list(range(len(party_data)))
            
            # Initialize selection to all if not set
            if "scanner_party_selection" not in st.session_state:
                st.session_state.scanner_party_selection = party_indices
            
            # Handle migration from old string-based selection to indices
            if st.session_state.scanner_party_selection and isinstance(st.session_state.scanner_party_selection[0], str):
                 st.session_state.scanner_party_selection = party_indices
            
            # Filter out invalid selections (e.g. deleted characters)
            st.session_state.scanner_party_selection = [x for x in st.session_state.scanner_party_selection if x in party_indices]

            selected_indices = st.multiselect(
                "Active Party Members", 
                options=party_indices, 
                format_func=get_party_label,
                key="scanner_party_selection"
            )
            
            for i, index in enumerate(selected_indices):
                char = party_data[index]
                # Map character data to statblock format for CR calculation
                c_stats = {
                    "level": char.get("level", 1),
                    "hp": char.get("hp_max", 10),
                    "sp": char.get("stamina_max", 10),
                    "ac": char.get("ac", 10),
                    "dt": 0, 
                    "ap": char.get("action_points", 10),
                    "special": char.get("stats", {})
                }
                
                member_cr = calculate_cr(c_stats, use_ap_multiplier=enable_ap_multiplier)
                if enable_group_multiplier:
                    member_cr *= (1.0 + (i * 0.08))
                
                party_cr += int(member_cr)

        if party_cr > 0:
            c_preset, c_info = st.columns([2, 1])
            with c_preset:
                # Track previous preset to detect changes
                if "scanner_diff_prev" not in st.session_state:
                    st.session_state.scanner_diff_prev = "Custom"
                
                difficulty = st.selectbox("Difficulty Preset", ["Custom", "Easy", "Medium", "Hard", "Deadly"], key="scanner_diff_preset")
                
                if difficulty != "Custom" and difficulty != st.session_state.scanner_diff_prev:
                    multipliers = {"Easy": 0.5, "Medium": 1.0, "Hard": 1.5, "Deadly": 2.0}
                    st.session_state.scanner_budget = int(party_cr * multipliers[difficulty])
                
                st.session_state.scanner_diff_prev = difficulty

            with c_info:
                st.metric("Party CR", party_cr)

        def on_budget_change():
            st.session_state.scanner_diff_preset = "Custom"

        if "scanner_budget" not in st.session_state:
            st.session_state.scanner_budget = 100
            
        budget = st.number_input("Threat Budget", min_value=10, step=10, key="scanner_budget", on_change=on_budget_change, help="The target CR budget for the encounter.")
        
        enable_budget_variation = st.checkbox("Enable Budget Variation (±10%)", value=True, help="Adds a random ±10% to the target budget for more unpredictable encounters.")
        
        # Calculate actual budget with variation
        actual_budget = budget
        if enable_budget_variation:
            variation = budget * 0.10
            actual_budget = random.randint(int(budget - variation), int(budget + variation))
        #    st.info(f"Actual Budget (with variation): {actual_budget}")
        
        # Overflow allowance (15%) to help fill the budget completely
        overflow_allowance = int(actual_budget * 0.15)
        
        if st.button("⚡ Generate from Budget", use_container_width=True):
            if not candidates:
                st.warning("No candidates available with current filters.")
            else:
                # 1. Calculate CR for all candidates
                pool = []
                for name in candidates:
                    stats = bestiary.get(name, {})
                    cr = calculate_cr(stats, use_ap_multiplier=enable_ap_multiplier)
                    role = get_creature_role(stats) if enable_role_synergy_tax else "Generic"
                    pool.append({"name": name, "cr": cr, "role": role})
                
                # 2. Fill Budget
                best_generated = []
                best_remaining = actual_budget
                
                # Try up to 10 times to get a good fill (> 70%)
                for _ in range(10):
                    current_budget = actual_budget
                    generated = []
                    attempts = 0
                    
                    # Try to fill the budget
                    while current_budget > 0 and attempts < 50:
                        # Find creatures that fit in remaining budget
                        # In advanced mode, costs are dynamic, so we filter by base CR first as a rough check
                        affordable = [x for x in pool if x["cr"] <= (current_budget + overflow_allowance)]
                        
                        if not affordable:
                            break
                            
                        if enable_weight_bias:
                            # Bias towards higher CR enemies
                            weights = [item["cr"] for item in affordable]
                            pick = random.choices(affordable, weights=weights, k=1)[0]
                        else:
                            pick = random.choice(affordable)

                        pick_name = pick["name"]
                        pick_cr = pick["cr"]
                        pick_role = pick["role"]
                        
                        final_cost = pick_cr
                        
                        # --- ADVANCED LOGIC ---
                        if enable_group_multiplier:
                            # Group Multiplier (Tax for diverse groups)
                            total_enemies_so_far = sum(item['count'] for item in generated)
                            if total_enemies_so_far > 0:
                                # Mild Group Multiplier: +2% cost per existing creature in the encounter
                                final_cost *= (1.0 + (total_enemies_so_far * 0.08))
                            
                        if enable_role_synergy_tax:
                            # Role Synergy Tax
                            # Check if complementary roles exist in generated list
                            roles_present = set()
                            for gen_item in generated:
                                # Find role from pool data
                                p_data = next((p for p in pool if p["name"] == gen_item["name"]), None)
                                if p_data: roles_present.add(p_data["role"])
                            
                            if (pick_role == "Striker" and "Tank" in roles_present) or \
                               (pick_role == "Tank" and "Striker" in roles_present):
                                final_cost *= 1.15 # +15% Synergy Tax

                        # Check affordability again with final cost
                        if final_cost > (current_budget + overflow_allowance):
                            attempts += 1
                            continue
                        
                        # Add to list
                        existing = next((x for x in generated if x["name"] == pick_name), None)
                        if existing:
                            existing["count"] += 1
                        else:
                            generated.append({"name": pick_name, "count": 1})
                        
                        current_budget -= int(final_cost)
                        attempts += 1
                    
                    # Check fill ratio
                    filled = actual_budget - current_budget
                    ratio = filled / actual_budget if actual_budget > 0 else 0
                    
                    # Keep track of best attempt (most filled)
                    if filled > (actual_budget - best_remaining):
                        best_generated = generated
                        best_remaining = current_budget
                    
                    # If we hit > 70%, we are good
                    if ratio >= 0.70:
                        break
                
                if best_generated:
                    st.session_state.current_encounter = best_generated
                    st.toast(f"Generated encounter! Remaining Budget: {best_remaining}", icon="⚡")
                    st.rerun()
                else:
                    st.warning("Could not generate encounter. Budget might be too low for selected creatures.")

        st.caption(f"Detected Signals: {len(candidates)}")
        
        # Quick Add
        selected_add = st.selectbox("Select Target", [""] + candidates, label_visibility="collapsed")
        
        if st.button("➕ Add Selected", use_container_width=True):
            if selected_add:
                existing = next((x for x in st.session_state.current_encounter if x["name"] == selected_add), None)
                if existing:
                    existing["count"] += 1
                else:
                    st.session_state.current_encounter.append({"name": selected_add, "count": 1})
                st.rerun()

        st.markdown("---")

 # --- RANDOM SCENARIO GENERATOR ---
        if st.button("🎲 Random Encounter", use_container_width=True, help="Spawns a random creature matching your selected filters (Biome, Faction, etc.)."):
            if candidates:
                pick = random.choice(candidates)
                existing = next((x for x in st.session_state.current_encounter if x["name"] == pick), None)
                if existing:
                    existing["count"] += 1
                else:
                    st.session_state.current_encounter.append({"name": pick, "count": 1})
                st.toast(f"Spawned: {pick}", icon="🎲")
                st.rerun()
            else:
                st.warning("No creatures match your current filters. Adjust your search or tags.")

    with col_viewer:
        st.markdown("### ⚠️ Current Threats")
        
        if not st.session_state.current_encounter:
            st.info("No threats detected. Scanner idle.")
        else:
            total_xp = 0
            total_cr_cost = 0
            
            # Pre-calculate roles present for synergy display if synergy tax is on
            roles_present = set()
            if enable_role_synergy_tax:
                for entry in st.session_state.current_encounter:
                    stats = bestiary.get(entry["name"], {})
                    if stats: # Ensure stats exist before trying to get role
                        roles_present.add(get_creature_role(stats))
            
            for i, entry in enumerate(st.session_state.current_encounter):
                name = entry["name"]
                count = entry["count"]
                stats = bestiary.get(name, {})
                lvl = stats.get("level", 1)
                
                # XP Calculation
                xp = lvl * 10 * count
                total_xp += xp
                
                # CR Cost Calculation for Display
                base_cr = calculate_cr(stats, use_ap_multiplier=enable_ap_multiplier)
                entry_cost = 0
                breakdown_text = ""
                
                role = "Generic" # Default role for display
                if enable_role_synergy_tax:
                    role = get_creature_role(stats)

                unit_cost = base_cr
                
                if enable_group_multiplier:
                    total_enemies_in_encounter = sum(e['count'] for e in st.session_state.current_encounter)
                    # Approximate the group tax by using an average position in the encounter
                    # This is an estimation for display purposes, as the exact generation order is not stored.
                    avg_position_multiplier = (total_enemies_in_encounter - 1) / 2
                    avg_group_tax = 1.0 + (avg_position_multiplier * 0.05)
                    unit_cost *= avg_group_tax
                
                if enable_role_synergy_tax:
                    # Synergy Tax
                    if (role == "Striker" and "Tank" in roles_present) or \
                        (role == "Tank" and "Striker" in roles_present):
                        unit_cost *= 1.15
                
                entry_cost = unit_cost * count # Total cost for this entry
                
                base_total_cr = base_cr * count
                role_text = f" (Role: {role})" if enable_role_synergy_tax else ""

                if int(entry_cost) != int(base_total_cr):
                    breakdown_text = f"CR Cost: {int(base_total_cr)} → **{int(entry_cost)}**{role_text}"
                else:
                    breakdown_text = f"CR Cost: {int(entry_cost)}{role_text}"
                
                total_cr_cost += entry_cost

                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([3.5, 1, 0.8, 0.8, 0.8], vertical_alignment="center")
                    c1.markdown(f"**{name}** (Lvl {lvl})")
                    c1.caption(breakdown_text)
                    c2.markdown(f"**x{count}**")
                    
                    if c3.button("📋", key=f"dup_{i}", help="Duplicate (Add another)"):
                        entry["count"] += 1
                        st.rerun()

                    if c4.button("📄", key=f"view_{i}"):
                        view_statblock_dialog(name, stats)
                    
                    if c5.button("❌", key=f"rem_{i}"):
                        st.session_state.current_encounter.pop(i)
                        st.rerun()

            st.divider()
            st.markdown(f"**Total XP:** {total_xp} | **Total CR Cost:** {int(total_cr_cost)}")
            
            c_save, c_clear = st.columns([3, 1])
            with c_save:
                if st.button("💾 Log Encounter", type="primary", use_container_width=True):
                    saved_logs = load_data(SAVED_FILE)
                    if not isinstance(saved_logs, list): saved_logs = []
                    
                    # Generate Loot Summary with Aggregation
                    temp_loot = {}
                    for entry in st.session_state.current_encounter:
                        name = entry["name"]
                        count = entry["count"]
                        b_loot = bestiary.get(name, {}).get("loot", [])
                        # Roll for each individual creature to ensure variance
                        for _ in range(count):
                            for item_str in b_loot:
                                item_name, item_qty, qty_str, decay_val, decay_str = parse_and_roll_loot(item_str)
                                
                                if decay_str:
                                    # Decay Item: Keep distinct based on rolled decay value
                                    # Format: Name (Decay: X) [Original Strings]
                                    key = f"{item_name} (Decay: {decay_val})"
                                    extras = []
                                    if qty_str and qty_str != "1": extras.append(qty_str)
                                    extras.append(f"{decay_str} levels of decay")
                                    key += f" [{', '.join(extras)}]"
                                    
                                    if key not in temp_loot: temp_loot[key] = {'qty': 0, 'dice': set(), 'is_decay': True}
                                    temp_loot[key]['qty'] += item_qty
                                else:
                                    # Condense non-decay items
                                    key = item_name
                                    if key not in temp_loot: temp_loot[key] = {'qty': 0, 'dice': set(), 'is_decay': False}
                                    temp_loot[key]['qty'] += item_qty
                                    if qty_str: temp_loot[key]['dice'].add(qty_str)
                    
                    loot_summary = {}
                    for key, data in temp_loot.items():
                        if data['is_decay']:
                            loot_summary[key] = data['qty']
                        else:
                            dice_strs = sorted(list(data['dice']))
                            dice_suffix = f" [{', '.join(dice_strs)}]" if dice_strs else ""
                            loot_summary[f"{key}{dice_suffix}"] = data['qty']
                    
                    log_entry = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "biome": "Manual Scan",
                        "threats": {e["name"]: e["count"] for e in st.session_state.current_encounter},
                        "loot": loot_summary,
                        "cost": int(total_cr_cost)
                    }
                    
                    saved_logs.append(log_entry)
                    save_data(SAVED_FILE, saved_logs)
                    st.success("Encounter logged!")
                    st.session_state.current_encounter = []
                    st.rerun()
            
            with c_clear:
                if st.button("🗑️", use_container_width=True):
                    st.session_state.current_encounter = []
                    st.rerun()