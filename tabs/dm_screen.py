import streamlit as st
from utils.dm_screen_components import PANEL_REGISTRY
from utils.data_manager import load_data, save_data
from constants import DM_SCREEN_FILE

def render() -> None:
    
    # --- INITIALIZATION ---
    if "dm_screen_initialized" not in st.session_state:
        saved_data = load_data(DM_SCREEN_FILE)
        if saved_data:
            st.session_state["dm_rows"] = saved_data.get("rows", 2)
            st.session_state["dm_cols"] = saved_data.get("cols", 3)
            st.session_state["dm_grid_state"] = saved_data.get("grid_state", {})
            
            # Restore module content
            for k, v in saved_data.get("module_content", {}).items():
                # Exclude booleans (buttons) to prevent StreamlitValueAssignmentNotAllowedError
                if not isinstance(v, bool):
                    st.session_state[k] = v
        
        st.session_state["dm_screen_initialized"] = True
    
    # --- CONFIGURATION ---
    with st.expander("⚙️ Screen Layout Configuration", expanded=False):
        c1, c2, c3 = st.columns([1, 1, 1], vertical_alignment="bottom")
        rows = c1.number_input("Rows", min_value=1, max_value=8, value=2, key="dm_rows")
        cols = c2.number_input("Columns", min_value=1, max_value=4, value=3, key="dm_cols")
        
        with c3:
            if st.button("💾 Save Layout", use_container_width=True):
                # Collect module content from session state (keys starting with panel_)
                module_content = {}
                for k, v in st.session_state.items():
                    if isinstance(k, str) and k.startswith("panel_"):
                        # Exclude booleans (buttons) to prevent StreamlitValueAssignmentNotAllowedError on reload
                        if not isinstance(v, bool):
                            module_content[k] = v
                
                data_to_save = {
                    "rows": rows,
                    "cols": cols,
                    "grid_state": st.session_state.get("dm_grid_state", {}),
                    "module_content": module_content
                }
                save_data(DM_SCREEN_FILE, data_to_save)
                st.toast("DM Screen layout saved!", icon="💾")
        
        # Initialize grid state if size changes or not set
        grid_state_key = "dm_grid_state"
        if grid_state_key not in st.session_state:
            st.session_state[grid_state_key] = {}
            
    # --- RENDER GRID ---
    # We iterate rows and columns to create the layout
    for r in range(rows):
        cols_obj = st.columns(cols)
        for c in range(cols):
            cell_key = f"panel_{r}_{c}"
            
            # Ensure default state
            if cell_key not in st.session_state[grid_state_key]:
                st.session_state[grid_state_key][cell_key] = "Empty"
            
            with cols_obj[c]:
                with st.container(border=True):
                    current_panel = st.session_state[grid_state_key][cell_key]
                    
                    if current_panel == "Empty":
                        # Dropdown to select content
                        options = list(PANEL_REGISTRY.keys())
                        new_selection = st.selectbox(
                            "Select Module", 
                            options, 
                            index=options.index("Empty"), 
                            key=f"sel_{cell_key}", 
                            label_visibility="collapsed"
                        )
                        
                        if new_selection != "Empty":
                            st.session_state[grid_state_key][cell_key] = new_selection
                            st.rerun()
                            
                        st.caption("Empty Slot")
                    else:
                        # Render Content
                        render_func = PANEL_REGISTRY.get(current_panel)
                        if render_func:
                            render_func(cell_key)

    # --- RESET MODULES ---
    st.divider()
    with st.expander("🔄 Manage Active Modules", expanded=False):
        active_modules = []
        for r in range(rows):
            for c in range(cols):
                cell_key = f"panel_{r}_{c}"
                module = st.session_state[grid_state_key].get(cell_key, "Empty")
                if module != "Empty":
                    active_modules.append((r, c, cell_key, module))
        
        if not active_modules:
            st.info("No active modules.")
        else:
            for r, c, key, mod in active_modules:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**Row {r+1}, Col {c+1}:** {mod}")
                if c2.button("Reset", key=f"reset_{key}"):
                    st.session_state[grid_state_key][key] = "Empty"
                    st.rerun()