import streamlit as st
import streamlit.components.v1 as components
import random
import uuid
import re
import urllib.parse
from utils.dice import roll_dice, parse_and_roll_loot
from utils.data_manager import load_data, save_data
from utils.character_logic import calculate_stats
from utils.character_components import convert_nested_to_flat
from constants import BESTIARY_FILE, SAVED_FILE, CHARACTERS_FILE, ITEM_FILE

def _render_panel_settings(key_prefix, grid_context):
    """Helper to render the settings popover for a panel."""
    if not grid_context:
        return
    
    with st.popover("⚙️", use_container_width=True):
        st.markdown("**Panel Settings**")
        
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
            if "dm_grid_state" in st.session_state:
                st.session_state["dm_grid_state"][key_prefix] = "Empty"
                st.rerun()

def render_dice_roller(key_prefix, grid_context=None):
    c_title, c_conf = st.columns([5, 1], vertical_alignment="center")
    c_title.markdown("##### 🎲 Dice Roller")
    with c_conf:
        _render_panel_settings(key_prefix, grid_context)

    c1, c2 = st.columns([3, 1])
    formula = c1.text_input("Formula", value="1d20", key=f"{key_prefix}_formula", label_visibility="collapsed")
    if c2.button("Roll", key=f"{key_prefix}_roll"):
        result = roll_dice(formula)
        st.session_state[f"{key_prefix}_result"] = f"Result: {result}"
    
    if f"{key_prefix}_result" in st.session_state:
        st.info(st.session_state[f"{key_prefix}_result"])

def render_scratchpad(key_prefix, grid_context=None):
    c_title, c_conf = st.columns([5, 1], vertical_alignment="center")
    c_title.markdown("##### 📝 Notes")
    with c_conf:
        _render_panel_settings(key_prefix, grid_context)
    st.text_area("Scratchpad", height=150, key=f"{key_prefix}_notes", label_visibility="collapsed")

def render_quick_ref(key_prefix, grid_context=None):
    c_title, c_conf = st.columns([5, 1], vertical_alignment="center")
    c_title.markdown("##### 📖 Quick Ref")
    with c_conf:
        _render_panel_settings(key_prefix, grid_context)
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

def inject_dm_scripts():
    """Injects necessary JS for the DM screen. Should be called once outside fragments."""
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

def _apply_combat_change(entry, action_type, amount):
    """Helper to apply changes and sync to file if needed."""
    old_hp = entry.get('hp', 0)
    old_sp = entry.get('sp', 0)
    
    if action_type == "heal_hp":
        entry['hp'] = min(entry['max_hp'], entry['hp'] + amount)
    elif action_type == "heal_sp":
        entry['sp'] = min(entry['max_sp'], entry['sp'] + amount)
    elif action_type == "dmg_hp":
        entry['hp'] = max(0, entry['hp'] - amount)
    elif action_type == "dmg_all":
        dt = entry.get("dt", 0)
        actual_dmg = max(1, amount - dt) if amount > 0 else 0
        sp_loss = min(entry['sp'], actual_dmg)
        entry['sp'] -= sp_loss
        remaining = actual_dmg - sp_loss
        entry['hp'] = max(0, entry['hp'] - remaining)

    # Sync to file if player and values changed
    if entry.get("is_player") and (entry.get('hp') != old_hp or entry.get('sp') != old_sp):
        try:
            all_chars = load_data(CHARACTERS_FILE)
            c_name = entry.get("source_name", entry.get("name"))
            for c in all_chars:
                if c.get("name") == c_name:
                    c["hp_current"] = entry['hp']
                    c["stamina_current"] = entry['sp']
                    save_data(CHARACTERS_FILE, all_chars)
                    break
        except Exception:
            pass

def reroll_sequence_callback(entry, data_key, widget_key):
    roll = random.randint(1, 20)
    mod = entry.get('seq_mod', 0)
    entry['seq_roll'] = roll
    entry['seq'] = roll + mod
    st.session_state[widget_key] = entry['seq']
    st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)

@st.fragment(run_every=3)
def render_hp_bar(entry):
    # Sync if player
    if entry.get("is_player"):
        try:
            chars = load_data(CHARACTERS_FILE)
            c_name = entry.get("source_name", entry.get("name"))
            found = next((c for c in chars if c.get("name") == c_name), None)
            if found:
                calculate_stats(found)
                entry["hp"] = found.get("hp_current", entry["hp"])
                entry["max_hp"] = found.get("hp_max", entry["max_hp"])
        except Exception:
            pass

    hp = entry.get('hp', 0)
    max_hp = entry.get('max_hp', 1)
    hp_pct = min(100, max(0, (hp / max_hp) * 100)) if max_hp > 0 else 0
    st.markdown(f"""
    <div style="background-color: #333; width: 100%; height: 6px; border-radius: 2px; margin-top: 2px;">
        <div style="background-color: #ff4d4d; width: {hp_pct}%; height: 100%; border-radius: 2px;"></div>
    </div>
    <div style="font-size: 0.75em; text-align: center; color: #aaa;">{hp}/{max_hp} HP</div>
    """, unsafe_allow_html=True)

@st.fragment(run_every=3)
def render_sp_bar(entry):
    # Sync if player
    if entry.get("is_player"):
        try:
            chars = load_data(CHARACTERS_FILE)
            c_name = entry.get("source_name", entry.get("name"))
            found = next((c for c in chars if c.get("name") == c_name), None)
            if found:
                calculate_stats(found)
                entry["sp"] = found.get("stamina_current", entry["sp"])
                entry["max_sp"] = found.get("stamina_max", entry["max_sp"])
        except Exception:
            pass

    sp = entry.get('sp', 0)
    max_sp = entry.get('max_sp', 1)
    sp_pct = min(100, max(0, (sp / max_sp) * 100)) if max_sp > 0 else 0
    st.markdown(f"""
    <div style="background-color: #333; width: 100%; height: 6px; border-radius: 2px; margin-top: 2px;">
        <div style="background-color: #cccc00; width: {sp_pct}%; height: 100%; border-radius: 2px;"></div>
    </div>
    <div style="font-size: 0.75em; text-align: center; color: #aaa;">{sp}/{max_sp} SP</div>
    """, unsafe_allow_html=True)

@st.fragment(run_every=3)
def render_player_dt(entry):
    """Fragment to auto-update player DT in the edit menu."""
    dt_value = entry.get('dt', 0)
    if entry.get("is_player"):
        try:
            chars = load_data(CHARACTERS_FILE)
            c_name = entry.get("source_name", entry.get("name"))
            found = next((c for c in chars if c.get("name") == c_name), None)
            if found:
                calculate_stats(found)
                new_dt = found.get("dt", 0)
                entry["dt"] = new_dt
                dt_value = new_dt
        except Exception:
            pass
    st.metric("DT", value=dt_value)

def give_item_to_player(player_name, item_data):
    """Safely adds an item to a player character's inventory."""
    try:
        all_chars = load_data(CHARACTERS_FILE)
        target_idx = -1
        for i, c in enumerate(all_chars):
            if c.get("name") == player_name:
                target_idx = i
                break
                
        if target_idx != -1:
            char = all_chars[target_idx]
            if "inventory" not in char: char["inventory"] = []
            
            # Ensure ID
            if "id" not in item_data: item_data["id"] = str(uuid.uuid4())
            
            char["inventory"].append(item_data)
            all_chars[target_idx] = char
            save_data(CHARACTERS_FILE, all_chars)
            return True
    except Exception:
        return False
    return False

def render_combatant_row(entry, is_active, data_key, key_prefix):
    """Renders a single combatant row."""
    
    is_dead = entry.get('hp', 0) <= 0
    
    if is_active:
        bg_color = "rgba(255, 255, 0, 0.15)"
        border = "1px solid #ffff00"
    else:
        bg_color = "rgba(255, 255, 255, 0.05)"
        border = "1px solid #444"
    
    if "party" not in entry:
        entry["party"] = "Players" if entry.get("is_player") else "Enemies"

    party_colors = {
        "Players": "#4da6ff",
        "Enemies": "#ff4d4d",
        "Neutral": "#ffcc00",
        "Other": "#cc33ff"
    }

    if is_dead:
        name_color = "#666666"
    else:
        name_color = party_colors.get(entry.get("party"), "#ff4d4d")
    
    # Construct Popout Link
    source_name = entry.get("source_name", entry["name"])
    safe_name = urllib.parse.quote(source_name)
    current_theme = st.session_state.get("app_theme", "Default (Green)")
    safe_theme = urllib.parse.quote(current_theme)
    popout_url = f"?popout=statblock&id={safe_name}&theme={safe_theme}"
    window_name = f"sb_{safe_name.replace('%', '')}"
    
    seq_display = str(entry['seq'])
    if entry.get('seq_roll') is not None:
        mod = entry.get('seq_mod', 0)
        sign = "+" if mod >= 0 else ""
        seq_display += f" <span style='font-size:0.75em; color:#aaa; font-weight:normal;'>({entry['seq_roll']}{sign}{mod})</span>"

    st.markdown(f"""
    <div style="background-color: {bg_color}; border: {border}; padding: 5px; border-radius: 5px; margin-bottom: 5px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; font-size: 1.1em; min-width: 30px;">{seq_display}</span>
            <span style="flex-grow: 1; margin-left: 10px; color: {name_color}; font-weight: bold; { 'text-decoration: line-through;' if is_dead else '' }">{entry['name']}</span>
            <a href="#" class="statblock-popout" data-url="{popout_url}" data-name="{window_name}" style="text-decoration: none; margin-left: 10px;" title="Open Statblock">📄</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for active loot generator
    loot_gen_prefix = None
    if "dm_grid_state" in st.session_state:
        for k, v in st.session_state["dm_grid_state"].items():
            if v == "Loot Generator":
                loot_gen_prefix = k
                break

    if is_dead:
        # Dead Layout: Skip | HP | Loot (if avail) | Edit | Delete
        if loot_gen_prefix and not entry.get("is_player"):
            c_skip, c_hp, c_loot, c_edit, c_del = st.columns([0.6, 2.6, 0.6, 0.6, 0.6], vertical_alignment="center")
            with c_loot:
                pool_key = f"{loot_gen_prefix}_combat_loot"
                looted_key = f"{loot_gen_prefix}_looted_ids"
                
                if looted_key not in st.session_state: st.session_state[looted_key] = set()
                if isinstance(st.session_state[looted_key], list): st.session_state[looted_key] = set(st.session_state[looted_key])
                
                is_looted = entry['id'] in st.session_state[looted_key]
                
                if st.button("🎁", key=f"btn_loot_{entry['id']}", disabled=is_looted, help="Add loot to pool"):
                    bestiary = load_data(BESTIARY_FILE)
                    source_name = entry.get("source_name", entry["name"])
                    b_entry = bestiary.get(source_name)
                    new_loot = []
                    if b_entry:
                        loot_table = b_entry.get("loot", [])
                        for loot_str in loot_table:
                            name, qty, _, decay_val, _ = parse_and_roll_loot(loot_str)
                            new_loot.append({"name": name, "qty": qty, "decay": decay_val})
                    
                    if pool_key not in st.session_state: st.session_state[pool_key] = []
                    st.session_state[pool_key].extend(new_loot)
                    st.session_state[looted_key].add(entry['id'])
                    st.rerun()
        else:
            c_skip, c_hp, c_edit, c_del = st.columns([0.6, 3.2, 0.6, 0.6], vertical_alignment="center")
            
        with c_skip:
            is_skipped = entry.get("skip", True)
            icon = "⏭️" if is_skipped else "🛑"
            if st.button(icon, key=f"btn_skip_{entry['id']}", help="Toggle Turn Skipping"):
                entry["skip"] = not is_skipped
                st.rerun()
                
        with c_del:
            if st.button("🗑️", key=f"btn_dead_del_{entry['id']}", type="primary"):
                if entry in st.session_state[data_key]:
                    st.session_state[data_key].remove(entry)
                    st.rerun()
    else:
        c_hp, c_sp, c_edit = st.columns([2.5, 2.5, 0.6], vertical_alignment="center")
        with c_sp:
            render_sp_bar(entry)
    
    with c_hp:
        render_hp_bar(entry)
    
    with c_edit:
        with st.popover("✏️"):
            st.markdown("**Damage / Heal**")
            dmg_amount = st.number_input("Amount", min_value=0, step=1, key=f"dmg_val_{entry['id']}")
            
            c_h1, c_h2 = st.columns(2)
            if c_h1.button("Heal HP", key=f"btn_heal_hp_{entry['id']}", use_container_width=True):
                _apply_combat_change(entry, "heal_hp", dmg_amount)
                st.rerun()
                
            if c_h2.button("Heal SP", key=f"btn_heal_sp_{entry['id']}", use_container_width=True):
                _apply_combat_change(entry, "heal_sp", dmg_amount)
                st.rerun()

            c_d1, c_d2 = st.columns(2)
            if c_d1.button("Dmg HP", key=f"btn_dmg_hp_{entry['id']}", use_container_width=True, help="Direct HP Damage"):
                _apply_combat_change(entry, "dmg_hp", dmg_amount)
                st.rerun()
                
            if c_d2.button("Damage", key=f"btn_dmg_all_{entry['id']}", use_container_width=True, help="Damage SP then HP"):
                _apply_combat_change(entry, "dmg_all", dmg_amount)
                st.rerun()
                
            if not entry.get("is_player"):
                if st.button("Full Heal", key=f"btn_full_heal_{entry['id']}", use_container_width=True):
                    entry['hp'] = entry['max_hp']
                    entry['sp'] = entry['max_sp']
                    st.rerun()
                
                party_opts = ["Players", "Enemies", "Neutral", "Other"]
                curr_party = entry.get("party", "Enemies")
                if curr_party not in party_opts: curr_party = "Enemies"
                new_party = st.selectbox("Faction Color", party_opts, index=party_opts.index(curr_party), key=f"party_sel_{entry['id']}")
                if new_party != curr_party:
                    entry["party"] = new_party
                    st.rerun()
            
            st.divider()
            st.markdown("**Edit Status**")
            
            # Max Values
            if not entry.get("is_player"):
                entry['max_hp'] = st.number_input("Max HP", min_value=1, value=max(1, entry.get('max_hp', 10)), key=f"ed_max_hp_{entry['id']}")
                entry['max_sp'] = st.number_input("Max SP", min_value=0, value=entry.get('max_sp', 10), key=f"ed_max_sp_{entry['id']}")
                entry['dt'] = st.number_input("DT", min_value=0, value=entry.get('dt', 0), key=f"ed_dt_{entry['id']}")
            
                # Clamp current values
                if entry['hp'] > entry['max_hp']: entry['hp'] = entry['max_hp']
                if entry['sp'] > entry['max_sp']: entry['sp'] = entry['max_sp']
            
            else:
                render_player_dt(entry)

                # Give Item Section for Players
                with st.expander("Give Item"):
                    c_name, c_qty = st.columns([3, 1])
                    i_name = c_name.text_input("Item Name", key=f"give_name_{entry['id']}")
                    i_qty = c_qty.number_input("Qty", min_value=1, value=1, key=f"give_qty_{entry['id']}")
                    
                    if st.button("Give", key=f"btn_give_{entry['id']}", use_container_width=True):
                        if i_name:
                            new_item = {
                                "id": str(uuid.uuid4()),
                                "name": i_name,
                                "description": "Given by DM",
                                "weight": 0.0,
                                "quantity": i_qty,
                                "equipped": False,
                                "location": "carried",
                                "parent_id": None
                            }
                            if give_item_to_player(entry.get("source_name", entry["name"]), new_item):
                                st.toast(f"Gave {i_qty}x {i_name} to {entry['name']}")
                            else:
                                st.error("Failed to give item.")

            c_seq, c_roll = st.columns([3, 1], vertical_alignment="bottom")
            widget_key = f"ed_seq_{entry['id']}"
            entry['seq'] = c_seq.number_input("Sequence", value=entry['seq'], key=widget_key)
            c_roll.button("🎲", key=f"btn_reroll_{entry['id']}", help="Reroll Sequence", on_click=reroll_sequence_callback, args=(entry, data_key, widget_key))

            st.divider()
            if st.button("🗑️ Delete Combatant", key=f"{key_prefix}_del_{entry['id']}", type="primary", use_container_width=True):
                if entry in st.session_state[data_key]:
                    st.session_state[data_key].remove(entry)
                    st.rerun()

@st.fragment
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

    # --- HEADER & CONFIG ---
    c_title, c_conf = st.columns([5, 1], vertical_alignment="center")
    c_title.markdown("##### ⚔️ Combat")
    
    with c_conf:
        with st.popover("⚙️", use_container_width=True):
            st.markdown("**Manage Combat**")
            
            if st.button("🔄 Reroll All", key=f"{key_prefix}_reroll_all", use_container_width=True):
                for c in st.session_state[data_key]:
                    roll = random.randint(1, 20)
                    mod = c.get('seq_mod', 0)
                    c['seq_roll'] = roll
                    c['seq'] = roll + mod
                    w_key = f"ed_seq_{c['id']}"
                    if w_key in st.session_state:
                        st.session_state[w_key] = c['seq']
                st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                st.rerun()
            
            if st.button("🔢 Sort by Sequence", key=f"{key_prefix}_sort_seq", use_container_width=True):
                # Capture current active ID to preserve turn
                active_id = None
                if st.session_state[data_key] and st.session_state[turn_key] < len(st.session_state[data_key]):
                    active_id = st.session_state[data_key][st.session_state[turn_key]]["id"]
                
                st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                
                # Restore active index
                if active_id:
                    new_idx = next((i for i, c in enumerate(st.session_state[data_key]) if c["id"] == active_id), None)
                    if new_idx is not None:
                        st.session_state[turn_key] = new_idx
                st.rerun()
            
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
                        dt = b_stats.get("dt", 0)
                        
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
                                "dt": dt,
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
                            dt = char_data.get("dt", 0)
                            
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
                                "dt": dt,
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
                st.session_state[data_key].append({"name": name if name else "Unknown", "source_name": name if name else "Unknown", "seq": seq, "hp": hp_in, "max_hp": hp_in, "sp": sp_in, "max_sp": sp_in, "dt": 0, "is_player": False, "id": str(uuid.uuid4())})
                st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                st.rerun()

            st.divider()
            
            if st.button(" Clear Dead (0 HP)", key=f"{key_prefix}_clear_dead", use_container_width=True):
                # Capture current active ID
                active_id = None
                if st.session_state[data_key] and st.session_state[turn_key] < len(st.session_state[data_key]):
                    active_id = st.session_state[data_key][st.session_state[turn_key]]["id"]

                st.session_state[data_key] = [c for c in st.session_state[data_key] if c.get("hp", 0) > 0]
                
                # Restore active index
                new_idx = next((i for i, c in enumerate(st.session_state[data_key]) if c["id"] == active_id), None) if active_id else None
                if new_idx is not None:
                    st.session_state[turn_key] = new_idx
                else:
                    st.session_state[turn_key] = min(st.session_state[turn_key], max(0, len(st.session_state[data_key]) - 1))
                st.rerun()
            
            if st.button("🗑️ Clear All", key=f"{key_prefix}_clear", use_container_width=True):
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
        # Render the row in its own fragment
        render_combatant_row(entry, is_active, data_key, key_prefix)

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
        if not combatants:
            pass
        else:
            start_idx = st.session_state[turn_key]
            curr_idx = start_idx
            
            # Loop to find next living
            for _ in range(len(combatants) + 1):
                curr_idx += 1
                
                if curr_idx >= len(combatants):
                    curr_idx = 0
                    st.session_state[round_key] += 1
                
                c = combatants[curr_idx]
                is_alive = c.get('hp', 0) > 0
                is_skipped = c.get('skip', True)
                
                if is_alive or not is_skipped:
                    st.session_state[turn_key] = curr_idx
                    break
                
                if curr_idx == start_idx:
                    break
        st.rerun()

def render_monster_lookup(key_prefix, grid_context=None):
    c_title, c_conf = st.columns([5, 1], vertical_alignment="center")
    c_title.markdown("##### 👹 Bestiary Lookup")
    with c_conf:
        _render_panel_settings(key_prefix, grid_context)

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

def _render_loot_list(loot_list, players, key_prefix, suffix, pool_key):
    """Helper to render a list of loot items with 'Give' buttons."""
    if not loot_list:
        st.caption("No loot generated.")
        return

    for i, item in enumerate(loot_list):
        c1, c2, c3 = st.columns([2.5, 1.5, 1], vertical_alignment="center")
        
        decay_txt = f" (Decay: {item.get('decay', 0)})" if item.get('decay', 0) > 0 else ""
        c1.write(f"{item['qty']}x {item['name']}{decay_txt}")
        
        target_p = c2.selectbox("Player", players, key=f"{key_prefix}_give_{suffix}_{i}", label_visibility="collapsed")
        if c3.button("Give", key=f"{key_prefix}_btn_{suffix}_{i}", use_container_width=True):
            # Try to find in DB for weight/desc/type
            new_item = {}
            try:
                db = load_data(ITEM_FILE)
                # Simple name match (strip decay info for lookup)
                clean_name = item['name'].split(' (Decay')[0].strip()
                # Improved Search
                # 1. Exact Match
                db_item = next((x for x in db if x.get("name") == clean_name), None)
                # 2. Case Insensitive
                if not db_item:
                    db_item = next((x for x in db if x.get("name", "").lower() == clean_name.lower()), None)
                # 3. Plural/Singular check (simple 's' removal)
                if not db_item and clean_name.lower().endswith('s'):
                    single_name = clean_name[:-1]
                    db_item = next((x for x in db if x.get("name", "").lower() == single_name.lower()), None)
                
                if db_item:
                    # Use the robust converter from character components
                    new_item = convert_nested_to_flat(db_item)
                else:
                    # Generic fallback
                    new_item = {
                        "name": item["name"],
                        "description": "Item not found in database.",
                        "weight": 0.0,
                        "cost": 0,
                        "item_type": "Misc",
                        "category": "gear"
                    }
            except Exception:
                pass
            
            # Apply Instance Properties
            new_item["id"] = str(uuid.uuid4())
            new_item["quantity"] = item["qty"]
            new_item["decay"] = item.get("decay", 0)
            new_item["equipped"] = False
            new_item["location"] = "carried"
            new_item["parent_id"] = None
            
            if give_item_to_player(target_p, new_item):
                st.toast(f"Gave {item['qty']}x {item['name']} to {target_p}")
                # Remove from pool
                if pool_key in st.session_state:
                    st.session_state[pool_key].pop(i)
                    st.rerun()
            else:
                st.error("Failed to give item.")

def render_loot_generator(key_prefix, grid_context=None):
    c_title, c_conf = st.columns([5, 1], vertical_alignment="center")
    c_title.markdown("##### 💰 Loot Generator")
    with c_conf:
        with st.popover("⚙️", use_container_width=True):
            st.markdown("**Loot Tools**")
            if st.button("Reset Loot Tracking", key=f"{key_prefix}_rst_track", use_container_width=True):
                if f"{key_prefix}_looted_ids" in st.session_state:
                    del st.session_state[f"{key_prefix}_looted_ids"]
                st.toast("Loot tracking reset.")
                st.rerun()
            if st.button("Clear Loot Pool", key=f"{key_prefix}_rst_pool", use_container_width=True):
                st.session_state[f"{key_prefix}_combat_loot"] = []
                st.rerun()
            
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
    
    # Load Players for "Give" functionality
    players = []
    try:
        chars = load_data(CHARACTERS_FILE)
        players = [c["name"] for c in chars]
    except Exception:
        pass

    tab_rand, tab_log, tab_combat = st.tabs(["🎲 Random", "📜 Log", "⚔️ Combat"])

    with tab_rand:
        level = st.number_input("Level / CR", min_value=1, value=1, key=f"{key_prefix}_loot_lvl")
        if st.button("Generate Random Loot", key=f"{key_prefix}_gen_rand", use_container_width=True):
            caps = roll_dice(f"{level}d20")
            loot = [{"name": "Cap", "qty": caps}]
            
            # Add random items from DB
            try:
                db_items = load_data(ITEM_FILE)
                if db_items:
                    num_items = random.randint(1, 3)
                    for _ in range(num_items):
                        item = random.choice(db_items)
                        loot.append({"name": item.get("name", "Unknown"), "qty": 1, "decay": 0})
            except Exception:
                pass
            st.session_state[f"{key_prefix}_rand_loot"] = loot
        
        if f"{key_prefix}_rand_loot" in st.session_state:
            _render_loot_list(st.session_state[f"{key_prefix}_rand_loot"], players, key_prefix, "rand", f"{key_prefix}_rand_loot")

    with tab_log:
        saved_logs = load_data(SAVED_FILE)
        if not saved_logs:
            st.info("No encounter logs found.")
        else:
            # Reverse to show newest first
            options = {f"{i}: {e.get('date')} - {e.get('biome')}": e for i, e in enumerate(saved_logs[::-1])}
            sel_log = st.selectbox("Select Encounter", list(options.keys()), key=f"{key_prefix}_log_sel")
            
            if sel_log:
                encounter = options[sel_log]
                loot_dict = encounter.get("loot", {})
                # Convert dict {name: qty} to list [{"name": name, "qty": qty}]
                loot_list = [{"name": k, "qty": v, "decay": 0} for k, v in loot_dict.items()]
                _render_loot_list(loot_list, players, key_prefix, "log", f"{key_prefix}_log_loot_dummy") # Log loot isn't depleted usually

    with tab_combat:
        # Find ACTIVE combat trackers from grid state, respecting spans to avoid duplicates
        active_trackers = []
        if "dm_grid_state" in st.session_state:
            grid_state = st.session_state["dm_grid_state"]
            spans = st.session_state.get("dm_grid_spans", {})
            
            # Track covered cells to skip hidden modules
            covered_cells = set()
            
            # Sort keys to process in order (row, then col)
            def get_rc(k):
                try:
                    parts = k.replace('panel_', '').split('_')
                    return int(parts[0]), int(parts[1])
                except:
                    return 999, 999
            
            sorted_panels = sorted(grid_state.keys(), key=get_rc)
            
            for p_key in sorted_panels:
                if p_key in covered_cells:
                    continue
                
                # Get span dimensions
                r, c = get_rc(p_key)
                span_key = f"span_{r}_{c}"
                span_data = spans.get(span_key, {'w': 1, 'h': 1})
                if isinstance(span_data, int): span_data = {'w': span_data, 'h': 1}
                w = span_data.get('w', 1)
                h = span_data.get('h', 1)
                
                # Mark covered neighbors
                for i in range(r, r + h):
                    for j in range(c, c + w):
                        if i == r and j == c: continue
                        covered_cells.add(f"panel_{i}_{j}")
                
                # Check if this is a combat tracker
                if grid_state[p_key] == "Combat Sequence":
                    data_k = f"{p_key}_data"
                    if data_k in st.session_state:
                        active_trackers.append(data_k)
        
        if not active_trackers:
            st.info("No active combat trackers found.")
        else:
            def format_tracker_name(key):
                # Convert "panel_0_0_data" -> "Combat (Row 1, Col 1)"
                try:
                    parts = key.replace('_data', '').replace('panel_', '').split('_')
                    r = int(parts[0]) + 1
                    c = int(parts[1]) + 1
                    return f"Combat (Row {r}, Col {c})"
                except:
                    return key

            target_key = active_trackers[0]
            if len(active_trackers) > 1:
                target_key = st.selectbox("Select Combat Tracker", active_trackers, format_func=format_tracker_name, key=f"{key_prefix}_combat_sel")
            
            # Initialize looted IDs tracker
            looted_key = f"{key_prefix}_looted_ids"
            # Ensure set if loaded from JSON as list
            if looted_key in st.session_state and isinstance(st.session_state[looted_key], list):
                st.session_state[looted_key] = set(st.session_state[looted_key])
            
            if looted_key not in st.session_state:
                st.session_state[looted_key] = set()
            
            if st.button("Pull Loot from Dead (0 HP)", key=f"{key_prefix}_pull_combat", use_container_width=True):
                combat_data = st.session_state[target_key]
                # Filter dead monsters that haven't been looted yet
                dead_monsters = [c for c in combat_data if c.get("hp", 0) <= 0 and not c.get("is_player", False) and c["id"] not in st.session_state[looted_key]]
                
                new_loot = []
                bestiary = load_data(BESTIARY_FILE)
                
                for m in dead_monsters:
                    source_name = m.get("source_name", m["name"])
                    b_entry = bestiary.get(source_name)
                    if b_entry:
                        loot_table = b_entry.get("loot", [])
                        for loot_str in loot_table:
                            name, qty, _, decay_val, _ = parse_and_roll_loot(loot_str)
                            new_loot.append({"name": name, "qty": qty, "decay": decay_val})
                    
                    # Mark as looted
                    st.session_state[looted_key].add(m["id"])
                
                # Add to existing pool or create new
                pool_key = f"{key_prefix}_combat_loot"
                if pool_key not in st.session_state:
                    st.session_state[pool_key] = []
                
                st.session_state[pool_key].extend(new_loot)
                
                # Aggregate duplicates in pool? Maybe not, to keep decay distinct.
                # We'll keep them separate for now as decay varies.
                
                if not dead_monsters:
                    st.warning("No new dead monsters found in tracker.")
                elif not new_loot:
                    st.info("Dead monsters had no loot.")
                st.rerun()
            
            if f"{key_prefix}_combat_loot" in st.session_state:
                 _render_loot_list(st.session_state[f"{key_prefix}_combat_loot"], players, key_prefix, "combat", f"{key_prefix}_combat_loot")

# Registry of available panels
PANEL_REGISTRY = {
    "Empty": None,
    "Dice Roller": render_dice_roller,
    "Scratchpad": render_scratchpad,
    "Quick Ref": render_quick_ref,
    "Combat Sequence": render_combat_sequence_tracker,
    "Monster Lookup": render_monster_lookup,
    "Loot Generator": render_loot_generator
}