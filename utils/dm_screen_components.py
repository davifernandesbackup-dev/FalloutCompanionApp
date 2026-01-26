import streamlit as st
import random
import uuid
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

def render_combat_sequence_tracker(key_prefix):
    st.markdown("##### ⚔️ Combat Sequence")
    
    # Data structure: list of dicts {'name': str, 'seq': int, 'hp': int, 'max_hp': int, 'sp': int, 'max_sp': int, 'is_player': bool}
    data_key = f"{key_prefix}_data"
    if data_key not in st.session_state:
        st.session_state[data_key] = []
        
    # Turn/Round State
    turn_key = f"{key_prefix}_turn"
    round_key = f"{key_prefix}_round"
    if turn_key not in st.session_state: st.session_state[turn_key] = 0
    if round_key not in st.session_state: st.session_state[round_key] = 1

    # --- CONTROLS ---
    c_round, c_turn = st.columns(2)
    c_round.metric("Round", st.session_state[round_key])
    
    combatants = st.session_state[data_key]
    
    with st.expander("📂 Load Encounter"):
        saved_encounters = load_data(SAVED_FILE)
        if not isinstance(saved_encounters, list):
            saved_encounters = []
            
        if not saved_encounters:
            st.caption("No saved encounters.")
        else:
            # Reverse to show newest first
            saved_encounters_rev = saved_encounters[::-1]
            # Create options map with index to ensure uniqueness
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
                        seq_val = random.randint(1, 20) + base_seq
                        display_name = f"{name} {i+1}" if count > 1 else name
                        st.session_state[data_key].append({
                            "name": display_name, 
                            "seq": seq_val, 
                            "hp": hp, 
                            "max_hp": hp, 
                            "sp": sp,
                            "max_sp": sp,
                            "is_player": False,
                            "id": str(uuid.uuid4())
                        })
                
                st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                st.rerun()

    with st.expander("👥 Load Party"):
        saved_chars = load_data(CHARACTERS_FILE)
        if not saved_chars:
            st.caption("No saved characters.")
        else:
            # Multi-select for party members
            char_options = [c.get("name", "Unnamed") for c in saved_chars]
            selected_chars = st.multiselect("Select Characters", char_options, key=f"{key_prefix}_party_sel")
            
            if st.button("Add Party", key=f"{key_prefix}_add_party"):
                for char_name in selected_chars:
                    char_data = next((c for c in saved_chars if c.get("name") == char_name), None)
                    if char_data:
                        # Use pre-calculated combat_sequence if available, else calc
                        base_seq = char_data.get("combat_sequence", 0)
                        if base_seq == 0:
                            per = char_data.get("stats", {}).get("PER", 5)
                            base_seq = per - 5
                        
                        seq_val = random.randint(1, 20) + base_seq
                        hp = char_data.get("hp_current", 10)
                        max_hp = char_data.get("hp_max", 10)
                        sp = char_data.get("stamina_current", 10)
                        max_sp = char_data.get("stamina_max", 10)
                        
                        st.session_state[data_key].append({
                            "name": char_name,
                            "seq": seq_val,
                            "hp": hp,
                            "max_hp": max_hp,
                            "sp": sp,
                            "max_sp": max_sp,
                            "is_player": True,
                            "id": str(uuid.uuid4())
                        })
                
                st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                st.rerun()

    # Manual Add
    c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
    name = c1.text_input("Name", key=f"{key_prefix}_name", label_visibility="collapsed", placeholder="Name")
    seq = c2.number_input("Seq", value=0, step=1, key=f"{key_prefix}_val", label_visibility="collapsed", help="Combat Sequence")
    hp_in = c3.number_input("HP", value=10, step=1, key=f"{key_prefix}_hp_in", label_visibility="collapsed", help="Hit Points")
    sp_in = c4.number_input("SP", value=10, step=1, key=f"{key_prefix}_sp_in", label_visibility="collapsed", help="Stamina Points")
    if c5.button("Add", key=f"{key_prefix}_add"):
        st.session_state[data_key].append({"name": name, "seq": seq, "hp": hp_in, "max_hp": hp_in, "sp": sp_in, "max_sp": sp_in, "is_player": False, "id": str(uuid.uuid4())})
        st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
        st.rerun()

    # --- TURN CONTROLS ---
    c_prev, c_next = st.columns(2)
    if c_prev.button("⬅️ Prev", key=f"{key_prefix}_prev"):
        st.session_state[turn_key] = (st.session_state[turn_key] - 1) % len(combatants) if combatants else 0
        st.rerun()
    if c_next.button("Next ➡️", key=f"{key_prefix}_next"):
        new_turn = st.session_state[turn_key] + 1
        if new_turn >= len(combatants):
            st.session_state[turn_key] = 0
            st.session_state[round_key] += 1
        else:
            st.session_state[turn_key] = new_turn
        st.rerun()

    # --- LIST ---
    for i, entry in enumerate(st.session_state[data_key]):
        if "id" not in entry:
            entry["id"] = str(uuid.uuid4())
        if "sp" not in entry: entry["sp"] = 10
        if "max_sp" not in entry: entry["max_sp"] = 10
            
        is_active = (i == st.session_state[turn_key])
        bg_color = "rgba(255, 255, 0, 0.1)" if is_active else "transparent"
        border = "2px solid #ffff00" if is_active else "1px solid #333"
        
        # Player vs Enemy styling
        name_color = "#4da6ff" if entry.get("is_player") else "#ff4d4d"
        
        with st.container():
            st.markdown(f"""
            <div style="background-color: {bg_color}; border: {border}; padding: 5px; border-radius: 5px; margin-bottom: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 1.1em; min-width: 30px;">{entry['seq']}</span>
                    <span style="flex-grow: 1; margin-left: 10px; color: {name_color}; font-weight: bold;">{entry['name']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c_hp, c_sp, c_edit, c_del = st.columns([1.5, 1.5, 1, 1])
            new_hp = c_hp.number_input("HP", value=entry['hp'], key=f"{key_prefix}_hp_{entry['id']}", label_visibility="collapsed")
            if new_hp != entry['hp']:
                entry['hp'] = new_hp
                # No rerun needed, updates on next interaction
            
            new_sp = c_sp.number_input("SP", value=entry['sp'], key=f"{key_prefix}_sp_{entry['id']}", label_visibility="collapsed")
            if new_sp != entry['sp']:
                entry['sp'] = new_sp
            
            # Edit Seq
            with c_edit:
                with st.popover("✏️"):
                    new_seq = st.number_input("Seq", value=entry['seq'], key=f"{key_prefix}_edit_seq_{entry['id']}")
                    if st.button("Update", key=f"{key_prefix}_upd_{entry['id']}"):
                        entry['seq'] = new_seq
                        st.session_state[data_key].sort(key=lambda x: x['seq'], reverse=True)
                        st.rerun()
            
            if c_del.button("❌", key=f"{key_prefix}_del_{entry['id']}"):
                st.session_state[data_key].pop(i)
                # Adjust turn index if needed
                if i < st.session_state[turn_key]:
                    st.session_state[turn_key] -= 1
                st.rerun()
            
    if st.button("Clear", key=f"{key_prefix}_clear"):
        st.session_state[data_key] = []
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