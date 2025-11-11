import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from app.hackathon_source import HackathonSource
from app.visualize import ChartGenerator
from app.ui import inject_global_css

st.set_page_config(
    page_title="Timeline Analysis - Hackathon Analysis",
    page_icon="📈",
    layout="wide"
)

inject_global_css()

st.title("📈 Timeline & Trend Analysis")
st.markdown("---")

source = HackathonSource()

if not source.is_loaded():
    st.error("⚠️ Hackathon source data not found. Please ensure 'hackathons_source.xlsx' is in the data directory.")
    st.info("📁 Expected location: `./data/hackathons_source.xlsx`")
    st.stop()

chart_gen = ChartGenerator()

date_range = source.get_date_range()
if date_range[0] and date_range[1]:
    st.success(f"✅ Data loaded: {date_range[0].strftime('%B %Y')} to {date_range[1].strftime('%B %Y')}")
else:
    st.warning("⚠️ No date information available in source data.")

st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Time Trends",
    "📅 Year-over-Year",
    "🌡️ Seasonal Patterns",
    "🏢 Organizer Timeline",
    "🔍 Date Range Filter"
])

with tab1:
    st.markdown("### 📊 Hackathon Activity Over Time")
    st.markdown("View how hackathon activity has evolved over time with different aggregation periods.")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        period = st.selectbox(
            "Aggregation Period:",
            options=['monthly', 'quarterly', 'yearly'],
            index=0,
            help="Choose how to group the data"
        )
    
    with col2:
        st.markdown("&nbsp;")
    
    with st.spinner("Loading time trends..."):
        trends_df = source.get_time_trends(period=period)
        
        if not trends_df.empty:
            st.markdown(f"#### Hackathon Count Over Time ({period.capitalize()})")
            
            fig = px.line(
                trends_df,
                x='Period',
                y='Hackathon Count',
                title=f'Number of Hackathons per {period.capitalize()} Period',
                markers=True
            )
            fig.update_layout(
                xaxis_title='Period',
                yaxis_title='Number of Hackathons',
                hovermode='x unified'
            )
            st.plotly_chart(fig, width='stretch')
            
            st.markdown(f"#### Participation Metrics Over Time ({period.capitalize()})")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_participants = px.line(
                    trends_df,
                    x='Period',
                    y='Total Participants',
                    title='Total Participants per Period',
                    markers=True
                )
                fig_participants.update_layout(
                    xaxis_title='Period',
                    yaxis_title='Total Participants',
                    hovermode='x unified'
                )
                st.plotly_chart(fig_participants, width='stretch')
            
            with col2:
                fig_submissions = px.line(
                    trends_df,
                    x='Period',
                    y='Total Submissions',
                    title='Total Submissions per Period',
                    markers=True
                )
                fig_submissions.update_layout(
                    xaxis_title='Period',
                    yaxis_title='Total Submissions',
                    hovermode='x unified'
                )
                st.plotly_chart(fig_submissions, width='stretch')
            
            st.markdown(f"#### Organizer Activity Over Time ({period.capitalize()})")
            
            fig_orgs = px.bar(
                trends_df,
                x='Period',
                y='Unique Organizers',
                title='Number of Unique Organizers per Period'
            )
            fig_orgs.update_layout(
                xaxis_title='Period',
                yaxis_title='Unique Organizers',
                hovermode='x unified'
            )
            st.plotly_chart(fig_orgs, width='stretch')
            
            with st.expander("📋 View Data Table"):
                st.dataframe(trends_df, width='stretch', hide_index=True)
        else:
            st.warning("No trend data available.")

with tab2:
    st.markdown("### 📅 Year-over-Year Comparison")
    st.markdown("Compare hackathon metrics across different years to identify growth trends.")
    
    with st.spinner("Loading year-over-year comparison..."):
        yoy_df = source.get_year_over_year_comparison()
        
        if not yoy_df.empty:
            st.markdown("#### Key Metrics by Year")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                latest_year = yoy_df['Year'].max()
                latest_hackathons = yoy_df[yoy_df['Year'] == latest_year]['Hackathon Count'].values[0]
                growth = yoy_df[yoy_df['Year'] == latest_year]['Hackathon Growth %'].values[0]
                
                st.metric(
                    f"Hackathons in {int(latest_year)}",
                    f"{int(latest_hackathons)}",
                    f"{growth:.1f}% vs prev year" if not pd.isna(growth) else None
                )
            
            with col2:
                latest_participants = yoy_df[yoy_df['Year'] == latest_year]['Total Participants'].values[0]
                participant_growth = yoy_df[yoy_df['Year'] == latest_year]['Participant Growth %'].values[0]
                
                st.metric(
                    f"Participants in {int(latest_year)}",
                    f"{int(latest_participants):,}",
                    f"{participant_growth:.1f}% vs prev year" if not pd.isna(participant_growth) else None
                )
            
            with col3:
                latest_submissions = yoy_df[yoy_df['Year'] == latest_year]['Total Submissions'].values[0]
                submission_growth = yoy_df[yoy_df['Year'] == latest_year]['Submission Growth %'].values[0]
                
                st.metric(
                    f"Submissions in {int(latest_year)}",
                    f"{int(latest_submissions):,}",
                    f"{submission_growth:.1f}% vs prev year" if not pd.isna(submission_growth) else None
                )
            
            st.markdown("---")
            st.markdown("#### Growth Trends")
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=yoy_df['Year'],
                y=yoy_df['Hackathon Count'],
                name='Hackathon Count',
                marker_color='lightblue'
            ))
            
            fig.update_layout(
                title='Hackathon Count by Year',
                xaxis_title='Year',
                yaxis_title='Number of Hackathons',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, width='stretch')
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_participants = px.bar(
                    yoy_df,
                    x='Year',
                    y='Total Participants',
                    title='Total Participants by Year'
                )
                st.plotly_chart(fig_participants, width='stretch')
            
            with col2:
                fig_submissions = px.bar(
                    yoy_df,
                    x='Year',
                    y='Total Submissions',
                    title='Total Submissions by Year'
                )
                st.plotly_chart(fig_submissions, width='stretch')
            
            st.markdown("---")
            st.markdown("#### Average Metrics per Hackathon")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_avg_participants = px.line(
                    yoy_df,
                    x='Year',
                    y='Avg Participants per Hackathon',
                    title='Average Participants per Hackathon',
                    markers=True
                )
                st.plotly_chart(fig_avg_participants, width='stretch')
            
            with col2:
                fig_avg_submissions = px.line(
                    yoy_df,
                    x='Year',
                    y='Avg Submissions per Hackathon',
                    title='Average Submissions per Hackathon',
                    markers=True
                )
                st.plotly_chart(fig_avg_submissions, width='stretch')
            
            with st.expander("📋 View Full Year-over-Year Data"):
                display_df = yoy_df.copy()
                
                for col in ['Hackathon Growth %', 'Participant Growth %', 'Submission Growth %']:
                    display_df[col] = display_df[col].round(1)
                
                display_df['Avg Participants per Hackathon'] = display_df['Avg Participants per Hackathon'].round(1)
                display_df['Avg Submissions per Hackathon'] = display_df['Avg Submissions per Hackathon'].round(1)
                
                st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.warning("No year-over-year data available.")

with tab3:
    st.markdown("### 🌡️ Seasonal Patterns")
    st.markdown("Identify which months are most popular for hackathons and how participation varies by season.")
    
    with st.spinner("Loading seasonal patterns..."):
        seasonal_df = source.get_seasonal_patterns()
        
        if not seasonal_df.empty:
            st.markdown("#### Hackathon Activity by Month")
            
            fig = px.bar(
                seasonal_df,
                x='Month Name',
                y='Hackathon Count',
                title='Number of Hackathons by Month (All Years Combined)',
                color='Hackathon Count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                xaxis_title='Month',
                yaxis_title='Total Hackathons',
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch')
            
            st.markdown("#### Average Participation by Month")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_participants = px.line(
                    seasonal_df,
                    x='Month Name',
                    y='Avg Participants',
                    title='Average Participants per Hackathon by Month',
                    markers=True
                )
                fig_participants.update_layout(
                    xaxis_title='Month',
                    yaxis_title='Avg Participants'
                )
                st.plotly_chart(fig_participants, width='stretch')
            
            with col2:
                fig_submissions = px.line(
                    seasonal_df,
                    x='Month Name',
                    y='Avg Submissions',
                    title='Average Submissions per Hackathon by Month',
                    markers=True
                )
                fig_submissions.update_layout(
                    xaxis_title='Month',
                    yaxis_title='Avg Submissions'
                )
                st.plotly_chart(fig_submissions, width='stretch')
            
            st.markdown("---")
            st.markdown("#### Insights")
            
            peak_month = seasonal_df.loc[seasonal_df['Hackathon Count'].idxmax(), 'Month Name']
            peak_count = seasonal_df['Hackathon Count'].max()
            
            low_month = seasonal_df.loc[seasonal_df['Hackathon Count'].idxmin(), 'Month Name']
            low_count = seasonal_df['Hackathon Count'].min()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Peak Month", peak_month, f"{int(peak_count)} hackathons")
            
            with col2:
                st.metric("Slowest Month", low_month, f"{int(low_count)} hackathons")
            
            with col3:
                avg_per_month = seasonal_df['Hackathon Count'].mean()
                st.metric("Average per Month", f"{avg_per_month:.1f}")
            
            with st.expander("📋 View Seasonal Data Table"):
                display_df = seasonal_df[['Month Name', 'Hackathon Count', 'Avg Participants', 'Avg Submissions']].copy()
                display_df['Avg Participants'] = display_df['Avg Participants'].round(1)
                display_df['Avg Submissions'] = display_df['Avg Submissions'].round(1)
                st.dataframe(display_df, width='stretch', hide_index=True)
        else:
            st.warning("No seasonal pattern data available.")

with tab4:
    st.markdown("### 🏢 Organizer Timeline")
    st.markdown("View the timeline of hackathons for a specific organizer to see their evolution over time.")
    
    organizers = source.get_all_organizers()
    
    if organizers:
        organizer_options = [""] + [org['canonical_name'] for org in organizers[:50]]
        
        selected_organizer = st.selectbox(
            "Select Organizer:",
            options=organizer_options,
            help="Choose an organizer to view their timeline"
        )
        
        if selected_organizer:
            with st.spinner(f"Loading timeline for {selected_organizer}..."):
                timeline_df = source.get_organizer_timeline(selected_organizer)
                
                if not timeline_df.empty:
                    st.markdown(f"#### Timeline for {selected_organizer}")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Hackathons", len(timeline_df))
                    
                    with col2:
                        total_participants = timeline_df['Participants'].sum()
                        st.metric("Total Participants", f"{int(total_participants):,}")
                    
                    with col3:
                        total_submissions = timeline_df['Submissions'].sum()
                        st.metric("Total Submissions", f"{int(total_submissions):,}")
                    
                    st.markdown("---")
                    
                    timeline_df['Date_str'] = pd.to_datetime(timeline_df['Date']).dt.strftime('%Y-%m-%d')
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=timeline_df['Date'],
                        y=timeline_df['Participants'],
                        mode='lines+markers',
                        name='Participants',
                        text=timeline_df['Hackathon'],
                        hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Participants: %{y}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=f'Participant Count Over Time - {selected_organizer}',
                        xaxis_title='Date',
                        yaxis_title='Participants',
                        hovermode='closest'
                    )
                    
                    st.plotly_chart(fig, width='stretch')
                    
                    fig_submissions = go.Figure()
                    
                    fig_submissions.add_trace(go.Scatter(
                        x=timeline_df['Date'],
                        y=timeline_df['Submissions'],
                        mode='lines+markers',
                        name='Submissions',
                        text=timeline_df['Hackathon'],
                        hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Submissions: %{y}<extra></extra>',
                        marker_color='orange'
                    ))
                    
                    fig_submissions.update_layout(
                        title=f'Submission Count Over Time - {selected_organizer}',
                        xaxis_title='Date',
                        yaxis_title='Submissions',
                        hovermode='closest'
                    )
                    
                    st.plotly_chart(fig_submissions, width='stretch')
                    
                    with st.expander("📋 View Timeline Data"):
                        display_df = timeline_df.copy()
                        display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
                        st.dataframe(display_df, width='stretch', hide_index=True)
                else:
                    st.warning(f"No timeline data available for {selected_organizer}.")
    else:
        st.warning("No organizers found in source data.")

with tab5:
    st.markdown("### 🔍 Filter Hackathons by Date Range")
    st.markdown("Select a custom date range to view hackathons and their metrics.")
    
    if date_range[0] and date_range[1]:
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date:",
                value=date_range[0],
                min_value=date_range[0],
                max_value=date_range[1],
                help="Select the start date for filtering"
            )
        
        with col2:
            end_date = st.date_input(
                "End Date:",
                value=date_range[1],
                min_value=date_range[0],
                max_value=date_range[1],
                help="Select the end date for filtering"
            )
        
        if st.button("🔍 Apply Date Filter", type="primary"):
            with st.spinner("Filtering hackathons..."):
                filtered_df = source.get_hackathons_by_date_range(
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                
                if not filtered_df.empty:
                    st.markdown(f"#### Results: {len(filtered_df)} hackathons found")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Hackathons", len(filtered_df))
                    
                    with col2:
                        total_participants = filtered_df['Total participant count'].sum()
                        st.metric("Total Participants", f"{int(total_participants):,}")
                    
                    with col3:
                        total_submissions = filtered_df['Total valid submissions (excluding spam)'].sum()
                        st.metric("Total Submissions", f"{int(total_submissions):,}")
                    
                    with col4:
                        unique_orgs = filtered_df['Organization name'].nunique()
                        st.metric("Unique Organizers", unique_orgs)
                    
                    st.markdown("---")
                    st.markdown("#### Hackathons in Date Range")
                    
                    display_df = filtered_df[[
                        'Hackathon published date',
                        'Hackathon name',
                        'Organization name',
                        'Total participant count',
                        'Total valid submissions (excluding spam)',
                        'In person vs virtual'
                    ]].copy()
                    
                    display_df.columns = [
                        'Date',
                        'Hackathon',
                        'Organizer',
                        'Participants',
                        'Submissions',
                        'Event Type'
                    ]
                    
                    display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
                    
                    st.dataframe(display_df, width='stretch', hide_index=True)
                    
                    st.markdown("---")
                    st.markdown("#### Top Organizers in Date Range")
                    
                    top_orgs = filtered_df.groupby('Organization name').agg({
                        'Hackathon name': 'count',
                        'Total participant count': 'sum',
                        'Total valid submissions (excluding spam)': 'sum'
                    }).reset_index()
                    
                    top_orgs.columns = ['Organizer', 'Hackathons', 'Total Participants', 'Total Submissions']
                    top_orgs = top_orgs.sort_values('Hackathons', ascending=False).head(10)
                    
                    fig = px.bar(
                        top_orgs,
                        x='Organizer',
                        y='Hackathons',
                        title='Top 10 Organizers by Hackathon Count in Date Range'
                    )
                    st.plotly_chart(fig, width='stretch')
                    
                else:
                    st.warning("No hackathons found in the selected date range.")
    else:
        st.warning("Date information not available in source data.")

st.markdown("---")

with st.expander("ℹ️ About Timeline Analysis"):
    st.markdown("""
    **Timeline & Trend Analysis**
    
    This feature provides comprehensive time-based analysis of hackathon data from the source of truth.
    
    **Features:**
    
    1. **Time Trends** - View hackathon activity aggregated by month, quarter, or year
       - Hackathon count over time
       - Total participants and submissions per period
       - Number of unique organizers per period
    
    2. **Year-over-Year Comparison** - Compare metrics across different years
       - Growth percentages for hackathons, participants, and submissions
       - Average metrics per hackathon by year
       - Identify long-term trends
    
    3. **Seasonal Patterns** - Discover which months are most popular
       - Total hackathons by month (all years combined)
       - Average participation by month
       - Peak and slowest months
    
    4. **Organizer Timeline** - Track individual organizer evolution
       - Chronological view of all hackathons by an organizer
       - Participant and submission trends over time
       - Identify organizer growth patterns
    
    5. **Date Range Filter** - Custom date filtering
       - Filter hackathons by any date range
       - View aggregated metrics for the period
       - Identify top organizers in specific timeframes
    
    **Use Cases:**
    - Identify growth trends and patterns
    - Plan hackathon timing based on seasonal patterns
    - Track organizer performance over time
    - Compare year-over-year performance
    - Analyze specific time periods
    """)
