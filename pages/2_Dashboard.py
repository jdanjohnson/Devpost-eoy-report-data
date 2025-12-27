import streamlit as st

st.set_page_config(
    page_title="Dashboard - Hackathon Analysis",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def get_aggregator():
    """Lazily initialize data aggregator."""
    from app.aggregate import DataAggregator
    return DataAggregator()

@st.cache_resource
def get_chart_generator():
    """Lazily initialize chart generator."""
    from app.visualize import ChartGenerator
    return ChartGenerator()

def inject_css():
    """Lazily inject global CSS."""
    from app.ui import inject_global_css
    inject_global_css()

inject_css()

st.title("📊 Analytics Dashboard")
st.markdown("---")

aggregator = get_aggregator()
chart_gen = get_chart_generator()

if not aggregator.data_exists():
    st.warning("⚠️ No data available. Please upload and process files first.")
    st.info("👉 Navigate to the **Upload** page to get started!")
    st.stop()

summary = aggregator.get_summary_statistics()

st.subheader("📈 Summary Statistics")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Total Submissions",
        value=f"{summary['total_submissions']:,}"
    )

with col2:
    st.metric(
        label="Total Registrants",
        value=f"{summary['total_registrants']:,}"
    )

with col3:
    st.metric(
        label="Unique Hackathons",
        value=f"{summary['unique_hackathons']:,}"
    )

with col4:
    st.metric(
        label="Unique Organizations",
        value=f"{summary['unique_organizations']:,}"
    )

with col5:
    st.metric(
        label="Avg Team Size",
        value=f"{summary['avg_team_size']}"
    )

st.markdown("---")

col6, col7, col8 = st.columns(3)

with col6:
    if summary['most_popular_technology']:
        st.info(f"🔧 **Most Popular Technology**: {summary['most_popular_technology']}")

with col7:
    if summary['most_popular_skill']:
        st.info(f"💡 **Most Popular Skill**: {summary['most_popular_skill']}")

with col8:
    if summary['top_country']:
        st.info(f"🌍 **Top Country**: {summary['top_country']}")

if summary['date_range']['start'] and summary['date_range']['end']:
    st.markdown(f"📅 **Data Range**: {summary['date_range']['start']} to {summary['date_range']['end']}")

st.markdown("---")

st.subheader("📊 Interactive Visualizations")

tab1, tab2, tab3, tab4 = st.tabs([
    "Technologies & Skills",
    "Hackathons & Teams",
    "Demographics",
    "Time Trends"
])

with tab1:
    st.markdown("### 🔧 Technologies")
    
    top_n_tech = st.slider("Number of technologies to display:", 10, 50, 20, key="tech_slider")
    
    tech_df_chart = aggregator.get_top_technologies(limit=top_n_tech)
    
    if not tech_df_chart.empty:
        fig_tech = chart_gen.create_bar_chart(
            tech_df_chart,
            x='Technology',
            y='Count',
            title=f'Top {top_n_tech} Technologies',
            orientation='h'
        )
        st.plotly_chart(fig_tech, width='stretch')
        
        with st.expander("📋 View Data Table (Full Dataset)"):
            tech_df_full = aggregator.get_top_technologies(limit=None)
            st.dataframe(tech_df_full, width='stretch')
    else:
        st.info("No technology data available")
    
    st.markdown("---")
    
    st.markdown("### 💡 Skills")
    
    top_n_skills = st.slider("Number of skills to display:", 10, 50, 20, key="skills_slider")
    
    skills_df_chart = aggregator.get_top_skills(limit=top_n_skills)
    
    if not skills_df_chart.empty:
        fig_skills = chart_gen.create_bar_chart(
            skills_df_chart,
            x='Skill',
            y='Count',
            title=f'Top {top_n_skills} Skills',
            orientation='h'
        )
        st.plotly_chart(fig_skills, width='stretch')
        
        with st.expander("📋 View Data Table (Full Dataset)"):
            skills_df_full = aggregator.get_top_skills(limit=None)
            st.dataframe(skills_df_full, width='stretch')
    else:
        st.info("No skills data available")

with tab2:
    st.markdown("### 🏆 Submissions by Hackathon")
    
    hackathon_df = aggregator.get_submissions_by_hackathon()
    
    if not hackathon_df.empty:
        top_n_hackathons = st.slider("Number of hackathons to display:", 10, 50, 20, key="hackathon_slider")
        
        fig_hackathons = chart_gen.create_bar_chart(
            hackathon_df.head(top_n_hackathons),
            x='Hackathon',
            y='Submissions',
            title=f'Top {top_n_hackathons} Hackathons by Submissions',
            orientation='h'
        )
        st.plotly_chart(fig_hackathons, width='stretch')
        
        with st.expander("📋 View Data Table (Full Dataset)"):
            st.dataframe(hackathon_df, width='stretch')
    else:
        st.info("No hackathon data available")
    
    st.markdown("---")
    
    st.markdown("### 👥 Team Size Distribution")
    
    team_size_df = aggregator.get_team_size_distribution()
    
    if not team_size_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_team_pie = chart_gen.create_pie_chart(
                team_size_df,
                values='Count',
                names='Team Size',
                title='Team Size Distribution'
            )
            st.plotly_chart(fig_team_pie, width='stretch')
        
        with col2:
            st.markdown("#### Statistics")
            st.dataframe(team_size_df, width='stretch')
    else:
        st.info("No team size data available")

with tab3:
    st.markdown("### 🌍 Country Distribution")
    
    top_n_countries = st.slider("Number of countries to display:", 10, 50, 20, key="country_slider")
    
    country_df_chart = aggregator.get_country_distribution(limit=top_n_countries)
    
    if not country_df_chart.empty:
        fig_countries = chart_gen.create_bar_chart(
            country_df_chart,
            x='Country',
            y='Count',
            title=f'Top {top_n_countries} Countries',
            orientation='h'
        )
        st.plotly_chart(fig_countries, width='stretch')
        
        with st.expander("📋 View Data Table (Full Dataset)"):
            country_df_full = aggregator.get_country_distribution(limit=None)
            st.dataframe(country_df_full, width='stretch')
    else:
        st.info("No country data available")
    
    st.markdown("---")
    
    st.markdown("### 💼 Occupation Breakdown")
    
    top_n_occupations = st.slider("Number of occupations to display:", 10, 50, 15, key="occupation_slider")
    
    occupation_df_chart = aggregator.get_occupation_breakdown(limit=top_n_occupations)
    
    if not occupation_df_chart.empty:
        fig_occupations = chart_gen.create_bar_chart(
            occupation_df_chart,
            x='Occupation',
            y='Count',
            title=f'Top {top_n_occupations} Occupations',
            orientation='h'
        )
        st.plotly_chart(fig_occupations, width='stretch')
        
        with st.expander("📋 View Data Table (Full Dataset)"):
            occupation_df_full = aggregator.get_occupation_breakdown(limit=None)
            st.dataframe(occupation_df_full, width='stretch')
    else:
        st.info("No occupation data available")
    
    st.markdown("---")
    
    st.markdown("### 🎓 Student vs Professional")
    
    specialty_df = aggregator.get_specialty_distribution()
    
    if not specialty_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_specialty = chart_gen.create_pie_chart(
                specialty_df,
                values='Count',
                names='Specialty',
                title='Student vs Professional Distribution'
            )
            st.plotly_chart(fig_specialty, width='stretch')
        
        with col2:
            st.markdown("#### Statistics")
            st.dataframe(specialty_df, width='stretch')
    else:
        st.info("No specialty data available")
    
    st.markdown("---")
    
    st.markdown("### 💼 Work Experience Distribution")
    
    work_exp_df = aggregator.get_work_experience_distribution()
    
    if not work_exp_df.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_work_exp = chart_gen.create_pie_chart(
                work_exp_df,
                values='Count',
                names='Experience Range',
                title='Work Experience Distribution'
            )
            st.plotly_chart(fig_work_exp, width='stretch')
        
        with col2:
            st.markdown("#### Statistics")
            st.dataframe(work_exp_df, width='stretch')
    else:
        st.info("No work experience data available")

with tab4:
    st.markdown("### 📅 Submissions Over Time")
    
    period = st.selectbox(
        "Select time period:",
        ["daily", "weekly", "monthly"],
        index=1
    )
    
    time_trends_df = aggregator.get_time_trends(period=period)
    
    if not time_trends_df.empty:
        fig_time = chart_gen.create_line_chart(
            time_trends_df,
            x='Date',
            y='Submissions',
            title=f'Submissions Over Time ({period.capitalize()})',
            y2='Cumulative'
        )
        st.plotly_chart(fig_time, width='stretch')
        
        with st.expander("📋 View Data Table (Full Dataset)"):
            st.dataframe(time_trends_df, width='stretch')
    else:
        st.info("No time trend data available")

st.markdown("---")

st.info("💡 **Tip**: Hover over charts for detailed information. Use the controls to zoom, pan, and download charts as images.")
