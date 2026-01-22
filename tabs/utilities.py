import streamlit as st
# Importing from the new folder structure
from utils import range as utils_range
from utils import special as utils_special

def render() -> None:
#    Layout Manager for the Utilities Tab.
#    Loads sub-modules from tabs/utils/ into side-by-side columns.
    
    # Create the columns
    col_left, col_right = st.columns(2)

    # Load the Range Converter (tabs/utils/range.py)
    with col_left:
        utils_range.render()

    # Load the Special Calculator (tabs/utils/special.py)
    with col_right:
        utils_special.render()