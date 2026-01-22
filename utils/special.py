import streamlit as st

def render() -> None:
    st.subheader("🧠 Stat Modifier")
    
    score = st.slider("Attribute Score", 1, 10, 5, key="input_score")
    
    modifier = score - 5
    mod_str = f"+{modifier}" if modifier > 0 else f"{modifier}"
    
    st.metric(label="Modifier", value=mod_str)
    st.caption(f"Based on Score: {score}")