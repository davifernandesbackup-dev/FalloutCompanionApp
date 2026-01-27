import streamlit as st
import streamlit.components.v1 as components
import random
import uuid
import re
import urllib.parse
from utils.dice import roll_dice
from utils.data_manager import load_data
from constants import BESTIARY_FILE, SAVED_FILE, CHARACTERS_FILE

def render_dice_roller(key_prefix):
    st.markdown("##### 🎲 Dice Roller")
    c1, c2 = st.columns([3, 1])
    formula = c1.text_input("Formula", value="1d20", key=f"{key_prefix}_formula", label_visibility="collapsed")
    if c2.button("Roll", key=f"{key_prefix}_roll"):
        result = roll_dice(formula)
        st.session_state[f"{key_prefix}_result"] = f"Result: {result}"
    
    if f"{key_prefix}_result" in st.session_state:
        st.info(st.session_state[f"{key_prefix}_result"])

def render_scratchpad(key_prefix):
    st.markdown("##### 📝 Notes")
    st.text_area("Scratchpad", height=150, key=f"{key_prefix}_notes", label_visibility="collapsed")

def render_quick_ref(key_prefix):
    st.markdown("##### 📖 Quick Ref")
    topic = st.selectbox("Topic", ["Conditions", "Actions", "Cover"], key=f"{key_prefix}_topic", label_visibility="collapsed")
    
    if topic == "Conditions":
        st.caption("**Blinded**: Disadvantage on attacks, attacks against have advantage.")
        st.caption("**Charmed**: Can't attack charmer, charmer has advantage on social.")
        st.caption("**Deafened**: Can't hear, auto-fail hearing checks.")
    elif topic == "Actions":
        st.caption("**Attack**: Melee or Ranged attack.")
        st.caption("**Dash**: Double movement speed.")
        st.caption("**Disengage**: No opportunity attacks.")
        st.caption("**Dodge**: Attacks against you have disadvantage.")
    elif topic == "Cover":
        st.caption("**1/2 Cover**: +2 AC/Dex Saves.")
        st.caption("**3/4 Cover**: +5 AC/Dex Saves.")
        st.caption("**Total Cover**: Can't be targeted directly.")

def render_combat_sequence_tracker(key_prefix, grid_context=None):
    # Data structure: list of dicts {'name': str, 'seq': int, 'hp': int, 'max_hp': int, 'sp': int, 'max_sp': int, 'is_player': bool}
    data_key = f"{key_prefix}_data"
    if data_key not in st.session_state:
        st.session_state[data_key] = []
        
    # Turn/Round State
    turn_key = f"{key_prefix}_turn"
    round_key = f"{key_prefix}_round"
    if turn_key not in st.session_state: st.session_state[turn_key] = 0
    if round_key not in st.session_state: st.session_state[round_key] = 1

    # Inject JS for popouts
    components.html("""
    <script>
        function setupStatblockPopouts() {
            const links = window.parent.document.querySelectorAll('a.statblock-popout');
            links.forEach(link => {
                if (link.dataset.hasListener !== 'true') {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        const url = this.dataset.url;
                        const name = this.dataset.name || 'statblock';
                        window.open(url, name, 'width=700,height=600,menubar=no,toolbar=no,location=no,status=no,scrollbars=yes,resizable=yes');
                    });
                    link.dataset.hasListener = 'true';
                }
            });
        }
        setInterval(setupStatblockPopouts, 1000);
    </script>
    """, height=0, width=0)

    # --- HEADER & CONFIG ---
    c_title, c_conf = st.columns([5, 1], vertical_alignment="center")
    c_title.markdown("##### ⚔️ Combat")
    
    with c_conf:
        with st.popover("⚙️", use_container_width=True):
            st.markdown("**Manage Combat**")
            
            # Load Encounter
            st.caption("Load Encounter")
            saved_encounters = load_data(SAVED_FILE)
            if not isinstance(saved_encounters, list):
                saved_encounters = []
                
            if not saved_encounters:
                st.info("No saved encounters.")
            else:
                saved_encounters_rev = saved_encounters[::-1]
                options = {f"{i+1}. {e.get('date', '?')} - {e.get('biome', '?')}": e for i, e in enumerate(saved_encounters_rev)}
                selected_key = st.selectbox("Select Encounter", list(options.keys()), key=f"{key_prefix}_enc_sel")
                
                if st.button("Import Threats", key=f"{key_prefix}_import"):
                    encounter = options[selected_key]
                    threats = encounter.get("threats", {})
                    bestiary = load_data(BESTIARY_FILE)
                    if not isinstance(bestiary, dict): bestiary = {}
                    
                    for name, count in threats.items():
                        # Get stats for initiative bonus
                        b_stats = bestiary.get(name, {})
                        
                        # Calculate Combat Sequence: PER - 5
                        # Or use pre-calculated if available, but bestiary usually has raw stats
                        special = b_stats.get("special", {})
                        if isinstance(special, dict):
                            per = special.get("PER", 5)
                        else:
                            per = 5
                        
                        base_seq = per - 5
                        hp = b_stats.get("hp", 10)
                        sp = b_stats.get("sp", 10)
                        
                        for i in range(count):
                            # Roll Sequence: d20 + Base Seq
                            roll = random.randint(1, 20)
                            seq_val = roll + base_seq
                            display_name = f"{name} {i+1}" if count > 1 else name
                            st.session_state[data_key].append({
                                "name": display_name, 
                                "source_name": name,
                                "seq": seq_val, 
                                "seq_roll": roll,
                                "seq_mod": base_seq,
                                "hp": hp, 
                                "max_hp": hp, 
                                "sp": sp,
                                "max_sp": sp,
                                "is_player": False,
                                "id": str(uuid.uuid4())
                            })
                    
                    st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                    st.rerun()

            # Load Party
            st.caption("Load Party")
            saved_chars = load_data(CHARACTERS_FILE)
            if not saved_chars:
                st.info("No saved characters.")
            else:
                # Multi-select for party members
                char_options = [c.get("name", "Unnamed") for c in saved_chars]
                selected_chars = st.multiselect("Select Characters", char_options, key=f"{key_prefix}_party_sel")
                
                if st.button("Add Party", key=f"{key_prefix}_add_party"):
                    existing_players = {c["name"] for c in st.session_state[data_key] if c.get("is_player")}
                    added_any = False
                    
                    for char_name in selected_chars:
                        if char_name in existing_players:
                            continue
                        
                        char_data = next((c for c in saved_chars if c.get("name") == char_name), None)
                        if char_data:
                            # Use pre-calculated combat_sequence if available, else calc
                            base_seq = char_data.get("combat_sequence", 0)
                            if base_seq == 0:
                                per = char_data.get("stats", {}).get("PER", 5)
                                base_seq = per - 5
                            
                            roll = random.randint(1, 20)
                            seq_val = roll + base_seq
                            hp = char_data.get("hp_current", 10)
                            max_hp = char_data.get("hp_max", 10)
                            sp = char_data.get("stamina_current", 10)
                            max_sp = char_data.get("stamina_max", 10)
                            
                            st.session_state[data_key].append({
                                "name": char_name,
                                "source_name": char_name,
                                "seq": seq_val,
                                "seq_roll": roll,
                                "seq_mod": base_seq,
                                "hp": hp,
                                "max_hp": max_hp,
                                "sp": sp,
                                "max_sp": max_sp,
                                "is_player": True,
                                "id": str(uuid.uuid4())
                            })
                            added_any = True
                    
                    if added_any:
                        st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                        st.rerun()
                    else:
                        st.toast("Selected party members are already in combat.", icon="ℹ️")
            
            st.divider()
            st.caption("Add Custom Combatant")
            name = st.text_input("Name", key=f"{key_prefix}_name", placeholder="Name")
            c_seq, c_hp, c_sp = st.columns(3)
            seq = c_seq.number_input("Seq", value=0, step=1, key=f"{key_prefix}_val", help="Combat Sequence")
            hp_in = c_hp.number_input("HP", value=10, step=1, key=f"{key_prefix}_hp_in", help="Hit Points")
            sp_in = c_sp.number_input("SP", value=10, step=1, key=f"{key_prefix}_sp_in", help="Stamina Points")
            
            if st.button("➕ Add Custom", key=f"{key_prefix}_add"):
                st.session_state[data_key].append({"name": name if name else "Unknown", "source_name": name if name else "Unknown", "seq": seq, "hp": hp_in, "max_hp": hp_in, "sp": sp_in, "max_sp": sp_in, "is_player": False, "id": str(uuid.uuid4())})
                st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                st.rerun()

            st.divider()
            
            if st.button("🗑️ Clear All", key=f"{key_prefix}_clear"):
                st.session_state[data_key] = []
                st.session_state[turn_key] = 0
                st.session_state[round_key] = 1
                st.rerun()

            # --- GRID SETTINGS (Merged) ---
            if grid_context:
                st.divider()
                with st.expander("Panel Settings", expanded=False):
                    r, c = grid_context['r'], grid_context['c']
                    max_w, curr_w = grid_context['max_w'], grid_context['curr_w']
                    max_h, curr_h = grid_context['max_h'], grid_context['curr_h']
                    span_key = f"span_{r}_{c}"
                    
                    c_w, c_h = st.columns(2)
                    new_w = c_w.number_input("Width", min_value=1, max_value=max_w, value=curr_w, key=f"width_{key_prefix}")
                    new_h = c_h.number_input("Height", min_value=1, max_value=max_h, value=curr_h, key=f"height_{key_prefix}")
                    
                    if new_w != curr_w or new_h != curr_h:
                        st.session_state["dm_grid_spans"][span_key] = {'w': new_w, 'h': new_h}
                        st.rerun()
                    
                    if st.button("Reset Module", key=f"rst_mod_{key_prefix}"):
                        st.session_state["dm_grid_state"][key_prefix] = "Empty"
                        st.rerun()

    # --- LIST ---
    for i, entry in enumerate(st.session_state[data_key]):
        if "id" not in entry:
            entry["id"] = str(uuid.uuid4())
        if "sp" not in entry: entry["sp"] = 10
        if "max_sp" not in entry: entry["max_sp"] = 10
        if "max_hp" not in entry: entry["max_hp"] = max(1, entry.get("hp", 10))
            
        is_active = (i == st.session_state[turn_key])
        
        if is_active:
            bg_color = "rgba(255, 255, 0, 0.15)"
            border = "1px solid #ffff00"
        else:
            bg_color = "rgba(255, 255, 255, 0.05)"
            border = "1px solid #444"
        
        # Player vs Enemy styling
        name_color = "#4da6ff" if entry.get("is_player") else "#ff4d4d"
        
        # Construct Popout Link
        source_name = entry.get("source_name", entry["name"])
        safe_name = urllib.parse.quote(source_name)
        current_theme = st.session_state.get("app_theme", "Default (Green)")
        safe_theme = urllib.parse.quote(current_theme)
        popout_url = f"?popout=statblock&id={safe_name}&theme={safe_theme}"
        window_name = f"sb_{safe_name.replace('%', '')}"
        
        with st.container():
            seq_display = str(entry['seq'])
            if entry.get('seq_roll') is not None:
                mod = entry.get('seq_mod', 0)
                sign = "+" if mod >= 0 else ""
                seq_display += f" <span style='font-size:0.75em; color:#aaa; font-weight:normal;'>({entry['seq_roll']}{sign}{mod})</span>"

            st.markdown(f"""
            <div style="background-color: {bg_color}; border: {border}; padding: 5px; border-radius: 5px; margin-bottom: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 1.1em; min-width: 30px;">{seq_display}</span>
                    <span style="flex-grow: 1; margin-left: 10px; color: {name_color}; font-weight: bold;">{entry['name']}</span>
                    <a href="#" class="statblock-popout" data-url="{popout_url}" data-name="{window_name}" style="text-decoration: none; margin-left: 10px;" title="Open Statblock">📄</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c_hp, c_sp, c_edit, c_del = st.columns([2, 2, 0.6, 0.6], vertical_alignment="center")
            
            with c_hp:
                hp = entry.get('hp', 0)
                max_hp = entry.get('max_hp', 1)
                hp_pct = min(100, max(0, (hp / max_hp) * 100)) if max_hp > 0 else 0
                st.markdown(f"""
                <div style="background-color: #333; width: 100%; height: 6px; border-radius: 2px; margin-top: 2px;">
                    <div style="background-color: #ff4d4d; width: {hp_pct}%; height: 100%; border-radius: 2px;"></div>
                </div>
                <div style="font-size: 0.75em; text-align: center; color: #aaa;">{hp}/{max_hp} HP</div>
                """, unsafe_allow_html=True)

            with c_sp:
                sp = entry.get('sp', 0)
                max_sp = entry.get('max_sp', 1)
                sp_pct = min(100, max(0, (sp / max_sp) * 100)) if max_sp > 0 else 0
                st.markdown(f"""
                <div style="background-color: #333; width: 100%; height: 6px; border-radius: 2px; margin-top: 2px;">
                    <div style="background-color: #cccc00; width: {sp_pct}%; height: 100%; border-radius: 2px;"></div>
                </div>
                <div style="font-size: 0.75em; text-align: center; color: #aaa;">{sp}/{max_sp} SP</div>
                """, unsafe_allow_html=True)
            
            # Edit Stats
            with c_edit:
                with st.popover("✏️"):
                    st.markdown("**Damage / Heal**")
                    dmg_amount = st.number_input("Amount", min_value=0, step=1, key=f"dmg_val_{entry['id']}")
                    
                    c_h1, c_h2 = st.columns(2)
                    if c_h1.button("Heal HP", key=f"btn_heal_hp_{entry['id']}", use_container_width=True):
                        entry['hp'] = min(entry['max_hp'], entry['hp'] + dmg_amount)
                        # Sync widgets to prevent overwrite
                        st.session_state[f"ed_hp_{entry['id']}"] = entry['hp']
                        st.rerun()
                        
                    if c_h2.button("Heal SP", key=f"btn_heal_sp_{entry['id']}", use_container_width=True):
                        entry['sp'] = min(entry['max_sp'], entry['sp'] + dmg_amount)
                        # Sync widgets to prevent overwrite
                        st.session_state[f"ed_sp_{entry['id']}"] = entry['sp']
                        st.rerun()

                    c_d1, c_d2 = st.columns(2)
                    if c_d1.button("Damage HP", key=f"btn_dmg_hp_{entry['id']}", use_container_width=True, help="Direct HP Damage (Ignores SP)"):
                        entry['hp'] = max(0, entry['hp'] - dmg_amount)
                        st.session_state[f"ed_hp_{entry['id']}"] = entry['hp']
                        st.rerun()

                    if c_d2.button("Damage", key=f"btn_dmg_all_{entry['id']}", use_container_width=True, help="Damage SP then HP"):
                        sp_loss = min(entry['sp'], dmg_amount)
                        entry['sp'] -= sp_loss
                        remaining = dmg_amount - sp_loss
                        entry['hp'] = max(0, entry['hp'] - remaining)
                        # Sync widgets to prevent overwrite
                        st.session_state[f"ed_sp_{entry['id']}"] = entry['sp']
                        st.session_state[f"ed_hp_{entry['id']}"] = entry['hp']
                        st.rerun()
                    
                    st.divider()
                    st.markdown("**Edit Status**")
                    
                    # Max Values
                    entry['max_hp'] = st.number_input("Max HP", min_value=1, value=max(1, entry.get('max_hp', 10)), key=f"ed_max_hp_{entry['id']}")
                    entry['max_sp'] = st.number_input("Max SP", min_value=0, value=entry.get('max_sp', 10), key=f"ed_max_sp_{entry['id']}")
                    
                    # Current Values (Clamped)
                    entry['hp'] = st.number_input("Current HP", min_value=0, max_value=entry['max_hp'], value=min(entry['hp'], entry['max_hp']), key=f"ed_hp_{entry['id']}")
                    entry['sp'] = st.number_input("Current SP", min_value=0, max_value=entry['max_sp'], value=min(entry['sp'], entry['max_sp']), key=f"ed_sp_{entry['id']}")
                    
                    entry['seq'] = st.number_input("Sequence", value=entry['seq'], key=f"ed_seq_{entry['id']}")
                    
                    if st.button("Update Sort", key=f"btn_sort_{entry['id']}"):
                        # Clear breakdown if manually changed to mismatch
                        current_roll = entry.get('seq_roll')
                        current_mod = entry.get('seq_mod', 0)
                        if current_roll is not None:
                            if entry['seq'] != (current_roll + current_mod):
                                entry['seq_roll'] = None
                                entry['seq_mod'] = None
                        st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                        st.rerun()
            
            if c_del.button("❌", key=f"{key_prefix}_del_{entry['id']}"):
                st.session_state[data_key].pop(i)
                # Adjust turn index if needed
                if i < st.session_state[turn_key]:
                    st.session_state[turn_key] -= 1
                st.rerun()

    # --- TURN CONTROLS ---
    combatants = st.session_state[data_key]
    c_prev, c_round, c_next = st.columns([1, 1.1, 1], vertical_alignment="center")
    
    if c_prev.button("⬅️ Prev", key=f"{key_prefix}_prev", use_container_width=True):
        st.session_state[turn_key] = (st.session_state[turn_key] - 1) % len(combatants) if combatants else 0
        st.rerun()
        
    with c_round:
        with st.popover(f"Round {st.session_state[round_key]}", use_container_width=True):
            st.markdown("**Round Management**")
            new_r = st.number_input("Current Round", min_value=1, value=st.session_state[round_key], key=f"{key_prefix}_round_input")
            if st.button("Update", key=f"{key_prefix}_round_update", use_container_width=True):
                st.session_state[round_key] = new_r
                st.rerun()
            if st.button("Reset to 1", key=f"{key_prefix}_round_reset", use_container_width=True):
                st.session_state[round_key] = 1
                st.rerun()
    
    if c_next.button("Next ➡️", key=f"{key_prefix}_next", use_container_width=True):
        new_turn = st.session_state[turn_key] + 1
        if new_turn >= len(combatants):
            st.session_state[turn_key] = 0
            st.session_state[round_key] += 1
        else:
            st.session_state[turn_key] = new_turn
        st.rerun()

def render_monster_lookup(key_prefix):
    st.markdown("##### 👹 Bestiary Lookup")
    bestiary = load_data(BESTIARY_FILE)
    if not bestiary:
        st.error("No Data")
        return
        
    names = sorted(list(bestiary.keys()))
    selection = st.selectbox("Creature", names, key=f"{key_prefix}_sel", label_visibility="collapsed")
    
    if selection:
        data = bestiary[selection]
        with st.expander("Stats"):
            st.markdown(f"**HP**: {data.get('hp')} | **AC**: {data.get('ac')}")
            st.markdown(f"**Speed**: {data.get('speed', '30 ft.')}")
            st.caption(data.get('description', ''))

# Registry of available panels
PANEL_REGISTRY = {
    "Empty": None,
    "Dice Roller": render_dice_roller,
    "Scratchpad": render_scratchpad,
    "Quick Ref": render_quick_ref,
    "Combat Sequence": render_combat_sequence_tracker,
    "Monster Lookup": render_monster_lookup
}