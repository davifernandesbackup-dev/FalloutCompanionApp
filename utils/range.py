import streamlit as st
import streamlit.components.v1 as components
import math

# --- JAVASCRIPT HACK ---
def inject_focus_hack() -> None:
    """Injects JS to force 'Select All' on input focus."""
    js_code = """
    <script>
        function addSelectEvent() {
            const inputs = window.parent.document.querySelectorAll('input[type="number"]');
            inputs.forEach(input => {
                if (!input.dataset.hasSelectListener) {
                    input.addEventListener('focus', function() {
                        this.select();
                    });
                    input.dataset.hasSelectListener = 'true';
                }
            });
        }
        setInterval(addSelectEvent, 500);
    </script>
    """
    components.html(js_code, height=0, width=0)

# --- CALLBACKS (MOVEMENT MODULE) ---
def update_from_feet() -> None:
    ratio = st.session_state.get("feet_per_ap", 5)
    feet = st.session_state.feet_input
    raw_meters = feet * 0.3
    st.session_state.meters_input = round(raw_meters * 2) / 2
    if feet > 0:
        st.session_state.ap_input = math.ceil(feet / ratio)
    else:
        st.session_state.ap_input = 0

def update_from_meters() -> None:
    ratio = st.session_state.get("feet_per_ap", 5)
    meters = st.session_state.meters_input
    raw_feet = meters / 0.3
    rounded_feet = float(round(raw_feet))
    st.session_state.feet_input = rounded_feet
    if rounded_feet > 0:
        st.session_state.ap_input = math.ceil(rounded_feet / ratio)
    else:
        st.session_state.ap_input = 0

def update_from_ap() -> None:
    ratio = st.session_state.get("feet_per_ap", 5)
    ap = st.session_state.ap_input
    new_feet = float(ap * ratio)
    st.session_state.feet_input = new_feet
    raw_meters = new_feet * 0.3
    st.session_state.meters_input = round(raw_meters * 2) / 2

# --- RENDERER ---
def render() -> None:
    st.subheader("📏 Range Tools")
    
    inject_focus_hack()
    
    # 1. Mode Selection
    mode = st.radio(
        "Select Mode:", 
        ["Movement", "Weapon Range"], 
        horizontal=True, 
        label_visibility="collapsed"
    )
    
    st.divider() # Visual separation line

    # --- MODE A: MOVEMENT ---
    if mode == "Movement":
        # Initialize State
        if "feet_input" not in st.session_state:
            st.session_state.feet_input = 0.0
        if "meters_input" not in st.session_state:
            st.session_state.meters_input = 0.0
        if "ap_input" not in st.session_state:
            st.session_state.ap_input = 0
        if "feet_per_ap" not in st.session_state:
            st.session_state.feet_per_ap = 5

        st.caption("Convert Distances & AP")
        
        # Inputs
        st.number_input("Feet per 1 AP:", min_value=1, key="feet_per_ap", on_change=update_from_ap)
        st.number_input("Feet:", step=1.0, min_value=0.0, key="feet_input", on_change=update_from_feet, format="%g")
        st.number_input("Meters:", step=0.5, min_value=0.0, key="meters_input", on_change=update_from_meters, format="%g")
        st.number_input("Action Points (AP):", step=1, min_value=0, key="ap_input", on_change=update_from_ap, format="%d")
        
        ratio = st.session_state.feet_per_ap
        st.caption(f"1 AP = {ratio} Feet | {round(ratio * 0.3, 2)} Meters")

    # --- MODE B: WEAPON RANGE ---
    else:
        st.caption("Calculate Ballistic Ranges")
        
        # Agility Input
        agility = st.number_input("Agility Score:", min_value=1, max_value=10, value=5)
        
        # Multipliers in columns
        c1, c2 = st.columns(2)
        with c1:
            mult_norm = st.number_input("Normal (x):", value=8, help="Multiplier for Normal Range")
        with c2:
            mult_long = st.number_input("Long (y):", value=12, help="Multiplier for Long Range (Disadvantage)")

        # Logic
        range_norm_ft = agility * mult_norm
        range_long_ft = agility * mult_long
        
        # Meters Conversion (Same 0.3 factor)
        range_norm_m = round(range_norm_ft * 0.3, 1)
        range_long_m = round(range_long_ft * 0.3, 1)

        # Display Results
        st.success(f"**Normal: {range_norm_m} m** ({range_norm_ft} ft)")
        st.warning(f"**Long: {range_long_m} m** ({range_long_ft} ft) \n\n *(Disadvantage)*")