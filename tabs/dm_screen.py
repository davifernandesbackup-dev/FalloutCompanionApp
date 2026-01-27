import streamlit as st
from utils.dm_screen_components import PANEL_REGISTRY
from utils.data_manager import load_data, save_data
from constants import DM_SCREEN_FILE

def render() -> None:
    
    # --- INITIALIZATION ---
    if "dm_screen_initialized" not in st.session_state or "dm_rows" not in st.session_state:
        saved_data = load_data(DM_SCREEN_FILE)
        
        # Defaults
        init_rows = 2
        init_cols = 3
        
        if saved_data:
            loaded_rows = int(saved_data.get("rows", 2))
            loaded_cols = int(saved_data.get("cols", 3))
            # Clamp to widget limits to prevent errors
            init_rows = max(1, min(8, loaded_rows))
            init_cols = max(1, min(4, loaded_cols))
            
            if "dm_grid_state" not in st.session_state:
                st.session_state["dm_grid_state"] = saved_data.get("grid_state", {})
            
            if "dm_grid_spans" not in st.session_state:
                st.session_state["dm_grid_spans"] = saved_data.get("grid_spans", {})
            
            # Restore module content
            for k, v in saved_data.get("module_content", {}).items():
                # Exclude booleans (buttons) to prevent StreamlitValueAssignmentNotAllowedError
                if not isinstance(v, bool):
                    if k not in st.session_state:
                        st.session_state[k] = v
        
        # Set session state values to avoid widget default value conflict
        st.session_state["dm_rows"] = init_rows
        st.session_state["dm_cols"] = init_cols
        
        st.session_state["dm_screen_initialized"] = True
    
    # Ensure spans dict exists if not initialized above
    if "dm_grid_spans" not in st.session_state:
        st.session_state["dm_grid_spans"] = {}
    
    # --- HEADER & SETTINGS ---
    c_back, c_title, c_conf = st.columns([1, 5, 1], vertical_alignment="center")
    
    with c_back:
        def go_home():
            st.session_state["navigation"] = "🏠 Home"
            
        st.button("⬅️ Back", key="dm_back_home", use_container_width=True, on_click=go_home)

    with c_title:
        st.subheader("🖥️ DM Screen")
    
    with c_conf:
        with st.popover("⚙️ Settings", use_container_width=True):
            st.markdown("**Layout Configuration**")
            st.number_input("Rows", min_value=1, max_value=8, key="dm_rows")
            st.number_input("Columns", min_value=1, max_value=4, key="dm_cols")
            
            st.divider()
            
            if st.button("💾 Save Layout", use_container_width=True):
                module_content = {k: v for k, v in st.session_state.items() 
                                  if isinstance(k, str) and k.startswith("panel_") and not isinstance(v, bool)}
                
                data_to_save = {
                    "rows": st.session_state.get("dm_rows", 2),
                    "cols": st.session_state.get("dm_cols", 3),
                    "grid_state": st.session_state.get("dm_grid_state", {}),
                    "grid_spans": st.session_state.get("dm_grid_spans", {}),
                    "module_content": module_content
                }
                save_data(DM_SCREEN_FILE, data_to_save)
                st.toast("DM Screen layout saved!", icon="💾")

    # Ensure defaults are available for the grid loop
    try:
        rows = int(st.session_state.get("dm_rows", 2))
        cols = int(st.session_state.get("dm_cols", 3))
    except (ValueError, TypeError):
        rows = 2
        cols = 3
        
    # Initialize grid state if size changes or not set
    grid_state_key = "dm_grid_state"
    if grid_state_key not in st.session_state:
        st.session_state[grid_state_key] = {}
            
    # --- RENDER GRID ---
    # 1. Identify Column Groups (Connected Components based on horizontal spans)
    # This allows independent columns to flow vertically without waiting for neighbors.
    
    # Union-Find initialization
    parent = list(range(cols))
    def find(i):
        if parent[i] == i: return i
        parent[i] = find(parent[i])
        return parent[i]
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j: parent[root_i] = root_j

    # Check all active spans to link columns
    for r in range(rows):
        for c in range(cols):
            span_key = f"span_{r}_{c}"
            span_data = st.session_state["dm_grid_spans"].get(span_key, {'w': 1, 'h': 1})
            if isinstance(span_data, int):
                span_data = {'w': span_data, 'h': 1}
            w = span_data.get('w', 1)
            
            if w > 1:
                # Clamp width to grid boundaries
                actual_w = min(w, cols - c)
                # Link all columns covered by this span
                for k in range(1, actual_w):
                    union(c, c + k)

    # Group columns
    col_groups = {}
    for c in range(cols):
        root = find(c)
        if root not in col_groups: col_groups[root] = []
        col_groups[root].append(c)
    
    # Sort groups by first column index
    sorted_groups = sorted(col_groups.values(), key=lambda g: g[0])
    
    # Create top-level layout for groups
    # We use the number of columns in each group as the relative width weight
    group_weights = [len(g) for g in sorted_groups]
    top_level_cols = st.columns(group_weights)
    
    # Render each group
    for g_idx, group_cols in enumerate(sorted_groups):
        with top_level_cols[g_idx]:
            # Determine bounds for this group
            c_min = min(group_cols)
            c_max = max(group_cols)
            
            # Track vertical coverage within this group
            covered_map = {} # (r, c) -> width
            
            for r in range(rows):
                # Calculate layout for this row within the group
                row_specs = []
                cells_info = []
                
                c = c_min
                while c <= c_max:
                    # Check vertical coverage
                    if (r, c) in covered_map:
                        width = covered_map[(r, c)]
                        row_specs.append(width)
                        cells_info.append({'type': 'placeholder'})
                        c += width
                        continue

                    cell_key = f"panel_{r}_{c}"
                    span_key = f"span_{r}_{c}"
                    
                    # Ensure default state
                    if cell_key not in st.session_state[grid_state_key]:
                        st.session_state[grid_state_key][cell_key] = "Empty"
                    
                    # Get span data
                    span_data = st.session_state["dm_grid_spans"].get(span_key, {'w': 1, 'h': 1})
                    if isinstance(span_data, int): span_data = {'w': span_data, 'h': 1}
                    w = span_data.get('w', 1)
                    h = span_data.get('h', 1)
                    
                    # Clamp width to group boundaries
                    if c + w > c_max + 1:
                        w = c_max + 1 - c
                    
                    # Register vertical coverage
                    if h > 1:
                        for nr in range(r + 1, min(r + h, rows)):
                            covered_map[(nr, c)] = w
                    
                    row_specs.append(w)
                    cells_info.append({'type': 'content', 'w': w, 'h': h, 'key': cell_key, 'c': c})
                    c += w
                
                # Render the row for this group
                if row_specs:
                    cols_obj = st.columns(row_specs)
                    for idx, info in enumerate(cells_info):
                        with cols_obj[idx]:
                            if info['type'] == 'placeholder':
                                continue
                            
                            cell_key = info['key']
                            w = info['w']
                            h = info['h']
                            c_start = info['c']
                            
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
                                    
                                    # Span control for empty slot
                                    with st.popover("⚙️", use_container_width=True):
                                        st.markdown("**Panel Settings**")
                                        c_w, c_h = st.columns(2)
                                        new_w = c_w.number_input("Width", min_value=1, max_value=cols-c_start, value=w, key=f"width_{cell_key}")
                                        new_h = c_h.number_input("Height", min_value=1, max_value=rows-r, value=h, key=f"height_{cell_key}")
                                        
                                        if new_w != w or new_h != h:
                                            st.session_state["dm_grid_spans"][f"span_{r}_{c_start}"] = {'w': new_w, 'h': new_h}
                                            st.rerun()
                                else:
                                    # Render Content
                                    render_func = PANEL_REGISTRY.get(current_panel)
                                    
                                    if current_panel == "Combat Sequence":
                                        # Pass grid context to Combat Sequence to merge settings
                                        grid_ctx = {
                                            'r': r, 
                                            'c': c_start, 
                                            'max_w': cols - c_start + (w - 1),
                                            'curr_w': w,
                                            'max_h': rows - r + (h - 1),
                                            'curr_h': h
                                        }
                                        if render_func:
                                            render_func(cell_key, grid_context=grid_ctx)
                                    else:
                                        # Generic Settings Gear for other modules
                                        c_fill, c_gear = st.columns([10, 1])
                                        with c_gear:
                                            with st.popover("⚙️", use_container_width=True):
                                                st.markdown("**Panel Settings**")
                                                c_w, c_h = st.columns(2)
                                                new_w = c_w.number_input("Width", min_value=1, max_value=cols-c_start + (w - 1), value=w, key=f"width_{cell_key}")
                                                new_h = c_h.number_input("Height", min_value=1, max_value=rows-r + (h - 1), value=h, key=f"height_{cell_key}")
                                                
                                                if new_w != w or new_h != h:
                                                    st.session_state["dm_grid_spans"][f"span_{r}_{c_start}"] = {'w': new_w, 'h': new_h}
                                                    st.rerun()
                                                
                                                if st.button("Reset Module", key=f"rst_mod_{cell_key}"):
                                                    st.session_state[grid_state_key][cell_key] = "Empty"
                                                    st.rerun()

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