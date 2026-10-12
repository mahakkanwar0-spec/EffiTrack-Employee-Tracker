import streamlit as st
import requests
from styles import load_css

BACKEND_URL = st.secrets["BACKEND_URL"]
API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="EffiTrack",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(load_css(), unsafe_allow_html=True)

st.markdown("""
<style>
    [data-testid="stSidebarNav"]     { display: none !important; }
    [data-testid="stSidebarNavItems"]{ display: none !important; }
    header[data-testid="stHeader"]   { display: none !important; }
    #MainMenu { display: none !important; }
    footer    { display: none !important; }

    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 260px !important;
    }
    [data-testid="stSidebarContent"] {
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
    }
    .nav-section {
        font-size: 10px; letter-spacing: 1.5px;
        color: #555; font-weight: 700;
        margin: 18px 8px 6px;
    }
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: linear-gradient(90deg,rgba(233,69,96,0.18),rgba(15,52,96,0.05)) !important;
        border-left: 3px solid #e94560 !important;
        color: #fff !important; font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .stButton button[kind="secondary"] {
        background: transparent !important; border: none !important;
        color: #9a9ab0 !important;
    }
    [data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
        background: #13132a !important; color: #fff !important;
    }
    [data-testid="stSidebar"] .stButton button {
        border-radius: 8px !important; padding: 8px 12px !important;
        margin-bottom: 2px !important;
    }
    .sticky-logout {
        flex-shrink: 0; padding: 10px 8px 16px;
        background: #0f0f1e; border-top: 1px solid #1e1e3a;
    }
</style>
""", unsafe_allow_html=True)

ICON_COLORS = {
    "dashboard": "#e94560", "profile": "#4f8cff",
    "work_statistics": "#f2a900", "productivity": "#22c55e",
    "attendance": "#a855f7", "performance": "#06b6d4",
    "achievements": "#f59e0b", "projects": "#3b82f6",
    "burnout": "#ef4444", "wrapped": "#e94560",
}


def restore_session_from_query_params():
    """Persist the loaded employee across a hard browser refresh.

    st.session_state is wiped on a full page reload, but the URL's query
    string survives. We mirror uid/name/page into st.query_params after
    a successful upload, and on every fresh script start (before
    session_state is populated) we rehydrate session_state from it.
    """
    if st.session_state.get("uid"):
        return  # already have a live session, nothing to restore

    qp = st.query_params
    if qp.get("uid") and qp.get("name"):
        st.session_state.update({
            "uid":  qp.get("uid"),
            "name": qp.get("name"),
            "page": qp.get("page", "dashboard"),
        })


def render_sidebar():
    uid  = st.session_state.get("uid", "")
    name = st.session_state.get("name", "Employee")

    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 16px 12px; border-bottom:1px solid #1e1e3a;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="background:linear-gradient(135deg,#e94560,#0f3460);
                            border-radius:10px; width:36px; height:36px;
                            display:flex; align-items:center; justify-content:center;
                            font-size:18px; font-weight:900; color:#fff;">⚡</div>
                <div>
                    <div style="font-size:16px; font-weight:900; color:#fff;">EffiTrack</div>
                    <div style="font-size:9px; color:#444; letter-spacing:1px;">
                        PERFORMANCE ANALYTICS
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        initial = name[0].upper() if name else "?"
        st.markdown(f"""
        <div style="margin:12px 8px; padding:12px; background:#13132a;
                    border-radius:10px; border:1px solid #1e1e3a;
                    display:flex; align-items:center; gap:10px;">
            <div style="background:linear-gradient(135deg,#e94560,#0f3460);
                        border-radius:50%; width:36px; height:36px; min-width:36px;
                        display:flex; align-items:center; justify-content:center;
                        font-size:15px; color:#fff; font-weight:800;">{initial}</div>
            <div>
                <div style="font-size:13px; color:#fff; font-weight:600;">{name}</div>
                <div style="font-size:10px; color:#555;">Employee</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        current = st.session_state.get("page", "dashboard")

        nav_groups = {
            "MAIN": [
                ("🏠", "Dashboard",       "dashboard"),
                ("👤", "My Profile",      "profile"),
            ],
            "ANALYTICS": [
                ("📊", "Work Statistics", "work_statistics"),
                ("⚡", "Productivity",    "productivity"),
                ("🗓️", "Attendance",      "attendance"),
                ("🎯", "Performance",     "performance"),
            ],
            "INSIGHTS": [
                ("🏆", "Achievements",    "achievements"),
                ("📁", "Projects",        "projects"),
                ("🔥", "Burnout Risk",    "burnout"),
            ],
            "REPORT": [
                ("✨", "My Wrapped",      "wrapped"),
            ]
        }

        st.markdown('<div style="flex:1; overflow-y:auto;">', unsafe_allow_html=True)
        for group, items in nav_groups.items():
            st.markdown(f"<div class='nav-section'>{group}</div>", unsafe_allow_html=True)
            for icon, label, key in items:
                active = current == key
                if st.button(f"{icon}  {label}", key=f"btn_{key}",
                             use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state["page"] = key
                    # keep query params in sync so a refresh lands on the same page
                    st.query_params.update({"page": key})
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="sticky-logout">', unsafe_allow_html=True)
        if st.button("📤  Upload New File", key="upload_new", use_container_width=True):
            for key in ["uid", "name", "page"]:
                st.session_state.pop(key, None)
            st.query_params.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def show_upload():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        .block-container { padding-top: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.5, 1])[1]
    with col:
        st.markdown("""
        <div style="text-align:center; padding:48px 0 24px;">
            <div style="font-size:56px;">⚡</div>
            <div style="font-size:28px; font-weight:900; color:#fff; margin-top:8px;">
                EffiTrack
            </div>
            <div style="font-size:13px; color:#555; margin-top:6px;">
                AI-Powered Employee Performance Analytics
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#1a1a2e; border:1px solid #2a2a4a;
                    border-radius:16px; padding:28px; margin-bottom:16px;">
            <div style="font-size:16px; font-weight:700; color:#fff; margin-bottom:4px;">
                Upload Employee Data
            </div>
            <div style="font-size:12px; color:#666; margin-bottom:16px;">
                Upload your employee JSON file to view the full analytics dashboard
            </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Choose employee JSON file",
            type=["json"],
            label_visibility="collapsed"
        )

        if uploaded:
            with st.spinner("Processing employee data..."):
                res = requests.post(
                    f"{API_BASE}/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/json")}
                )

            if res.status_code == 200:
                d = res.json()
                st.session_state["uid"]  = d["uid"]
                st.session_state["name"] = d["name"]
                st.session_state["page"] = "dashboard"
                # mirror into the URL so a hard refresh doesn't bounce back to upload
                st.query_params.update({
                    "uid":  d["uid"],
                    "name": d["name"],
                    "page": "dashboard",
                })
                st.success(f"✅ Loaded: {d['name']}")
                st.rerun()
            else:
                st.error(f"Failed to process file: {res.json().get('detail', 'Unknown error')}")

        # st.markdown("""
        # <div style="text-align:center; margin-top:12px; font-size:12px; color:#444;">
        #     Supports both old and new employee JSON formats
        # </div>
        # """, unsafe_allow_html=True)


def main():
    restore_session_from_query_params()

    if not st.session_state.get("uid"):
        show_upload()
        return

    uid  = st.session_state["uid"]
    page = st.session_state.get("page", "dashboard")

    render_sidebar()

    if page == "dashboard":
        from pages.dashboard import show
    elif page == "profile":
        from pages.employee_page import show
    elif page == "work_statistics":
        from pages.work_statistics_page import show
    elif page == "productivity":
        from pages.productivity_page import show
    elif page == "attendance":
        from pages.attendance_page import show
    elif page == "performance":
        from pages.performance_page import show
    elif page == "achievements":
        from pages.achievement_page import show
    elif page == "projects":
        from pages.projects_page import show
    elif page == "burnout":
        from pages.burnout_page import show
    elif page == "wrapped":
        from pages.wrapped_page import show
    else:
        from pages.dashboard import show

    show(uid)


if __name__ == "__main__":
    main()