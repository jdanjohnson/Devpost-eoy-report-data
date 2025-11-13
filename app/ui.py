import streamlit as st


def inject_global_css():
    """
    Inject global CSS to fix tooltip and sidebar message width issues.
    Call this function at the top of each page after st.set_page_config().
    """
    st.markdown(
        """
        <style>
        /* 1) Sidebar message boxes (st.sidebar.success/info/warning use stAlert inside sidebar) */
        section[data-testid="stSidebar"] div[role="alert"] {
            width: 100% !important;
            max-width: 100% !important;
            white-space: normal !important;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        section[data-testid="stSidebar"] div[role="alert"] p {
            white-space: normal !important;
            overflow-wrap: anywhere;
            word-break: break-word;
            margin: 0;
        }

        /* 2) Tooltips produced by `help=` (BaseWeb tooltips) */
        /* BaseWeb tooltip container */
        div[data-baseweb="tooltip"] {
            max-width: 320px !important;
            white-space: normal !important;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        /* Some Streamlit versions render the tooltip via role="tooltip" */
        div[role="tooltip"] {
            max-width: 320px !important;
            white-space: normal !important;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        /* 3) General safeguard for Markdown text in sidebar */
        section[data-testid="stSidebar"] .stMarkdown {
            white-space: normal !important;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
