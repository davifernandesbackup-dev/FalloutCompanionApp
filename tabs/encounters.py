import streamlit as st
import random
from datetime import datetime
from utils.data_manager import load_data, save_data
from constants import BESTIARY_FILE, SAVED_FILE
from utils.statblock import view_statblock_dialog

def render() -> None:
    st.subheader("☢️ Encounter Scanner")
    
    tab_scan, tab_logs = st.tabs(["📡 Scanner", "🗃️ Logs"])
    
    # --- SCANNER TAB ---
    with tab_scan:
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
            search = st.text_input("Search Frequency", placeholder="Creature Name...")
            min_lvl, max_lvl = st.slider("Threat Level", 0, 50, (0, 50))
            
            # Type Filter
            all_types = sorted(list(set(c.get("type", "Unknown") for c in bestiary.values() if isinstance(c, dict))))
            selected_types = st.multiselect("Signal Type", all_types)

            # Filter Logic
            candidates = []
            for name, stats in bestiary.items():
                if not isinstance(stats, dict): continue
                
                if search.lower() in name.lower():
                    lvl = stats.get("level", 0)
                    if min_lvl <= lvl <= max_lvl:
                        if not selected_types or stats.get("type") in selected_types:
                            candidates.append(name)
            
            candidates.sort()
            
            st.caption(f"Detected Signals: {len(candidates)}")
            
            # Quick Add
            selected_add = st.selectbox("Select Target", [""] + candidates, label_visibility="collapsed")
            
            c_add, c_rand = st.columns(2)
            with c_add:
                if st.button("➕ Add", use_container_width=True):
                    if selected_add:
                        existing = next((x for x in st.session_state.current_encounter if x["name"] == selected_add), None)
                        if existing:
                            existing["count"] += 1
                        else:
                            st.session_state.current_encounter.append({"name": selected_add, "count": 1})
                        st.rerun()
            with c_rand:
                if st.button("🎲 Random", use_container_width=True, disabled=not candidates):
                    if candidates:
                        pick = random.choice(candidates)
                        existing = next((x for x in st.session_state.current_encounter if x["name"] == pick), None)
                        if existing:
                            existing["count"] += 1
                        else:
                            st.session_state.current_encounter.append({"name": pick, "count": 1})
                        st.rerun()

        with col_viewer:
            st.markdown("### ⚠️ Current Threats")
            
            if not st.session_state.current_encounter:
                st.info("No threats detected. Scanner idle.")
            else:
                total_xp = 0
                
                for i, entry in enumerate(st.session_state.current_encounter):
                    name = entry["name"]
                    count = entry["count"]
                    stats = bestiary.get(name, {})
                    lvl = stats.get("level", 1)
                    xp = lvl * 10 * count
                    total_xp += xp
                    
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([4, 1, 1, 1], vertical_alignment="center")
                        c1.markdown(f"**{name}** (Lvl {lvl})")
                        c2.markdown(f"**x{count}**")
                        
                        if c3.button("📄", key=f"view_{i}"):
                            view_statblock_dialog(name, stats)
                        
                        if c4.button("❌", key=f"rem_{i}"):
                            st.session_state.current_encounter.pop(i)
                            st.rerun()

                st.divider()
                st.markdown(f"**Total XP Estimate:** {total_xp}")
                
                c_save, c_clear = st.columns([3, 1])
                with c_save:
                    if st.button("💾 Log Encounter", type="primary", use_container_width=True):
                        saved_logs = load_data(SAVED_FILE)
                        if not isinstance(saved_logs, list): saved_logs = []
                        
                        # Generate Loot Summary
                        loot_summary = {}
                        for entry in st.session_state.current_encounter:
                            name = entry["name"]
                            count = entry["count"]
                            b_loot = bestiary.get(name, {}).get("loot", [])
                            for item_str in b_loot:
                                loot_summary[item_str] = loot_summary.get(item_str, 0) + count
                        
                        log_entry = {
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "biome": "Manual Scan",
                            "threats": {e["name"]: e["count"] for e in st.session_state.current_encounter},
                            "loot": loot_summary
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

    # --- LOGS TAB ---
    with tab_logs:
        saved_data = load_data(SAVED_FILE)
        if not saved_data:
            st.info("No saved encounters found.")
        else:
            for i, enc in enumerate(reversed(saved_data)):
                # Use reversed index for deletion logic
                real_idx = len(saved_data) - 1 - i
                
                date = enc.get("date", "?")
                threats = enc.get("threats", {})
                
                with st.expander(f"📁 {date} - {len(threats)} Threats"):
                    st.markdown("**Threats:**")
                    for t_name, t_count in threats.items():
                        st.markdown(f"- {t_count}x {t_name}")
                    
                    st.markdown("**Loot:**")
                    loot = enc.get("loot", {})
                    if loot:
                        for l_name, l_count in loot.items():
                            st.markdown(f"- {l_count}x {l_name}")
                    else:
                        st.caption("No loot recorded.")
                    
                    if st.button("🗑️ Delete Log", key=f"del_log_{real_idx}"):
                        saved_data.pop(real_idx)
                        save_data(SAVED_FILE, saved_data)
                        st.rerun()
