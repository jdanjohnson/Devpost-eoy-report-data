import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional


class ChartGenerator:
    def __init__(self):
        self.color_scheme = px.colors.qualitative.Set3
        self.template = "plotly_white"
    
    def create_bar_chart(
        self, 
        df: pd.DataFrame, 
        x: str, 
        y: str, 
        title: str,
        orientation: str = 'h',
        limit: int = 20
    ) -> go.Figure:
        if df.empty:
            return self._create_empty_chart(title)
        
        plot_df = df.head(limit).copy()
        
        if orientation == 'h':
            plot_df = plot_df.sort_values(y, ascending=True)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=plot_df[y],
                    y=plot_df[x],
                    orientation='h',
                    marker=dict(
                        color=self.color_scheme[0],
                        line=dict(color='rgba(0,0,0,0.1)', width=1)
                    ),
                    text=plot_df[y],
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=dict(text=title, font=dict(size=20, color='#333')),
                xaxis_title=y,
                yaxis_title=x,
                template=self.template,
                height=max(400, len(plot_df) * 25),
                margin=dict(l=200, r=50, t=80, b=50),
                showlegend=False
            )
        else:
            plot_df = plot_df.sort_values(y, ascending=False)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=plot_df[x],
                    y=plot_df[y],
                    marker=dict(
                        color=self.color_scheme[0],
                        line=dict(color='rgba(0,0,0,0.1)', width=1)
                    ),
                    text=plot_df[y],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=dict(text=title, font=dict(size=20, color='#333')),
                xaxis_title=x,
                yaxis_title=y,
                template=self.template,
                height=500,
                margin=dict(l=50, r=50, t=80, b=100),
                showlegend=False
            )
            
            fig.update_xaxes(tickangle=-45)
        
        return fig
    
    def create_pie_chart(
        self, 
        df: pd.DataFrame, 
        values: str, 
        names: str, 
        title: str,
        limit: int = 10
    ) -> go.Figure:
        if df.empty:
            return self._create_empty_chart(title)
        
        plot_df = df.head(limit).copy()
        
        if len(df) > limit:
            other_count = df.iloc[limit:][values].sum()
            other_row = pd.DataFrame({names: ['Other'], values: [other_count]})
            plot_df = pd.concat([plot_df, other_row], ignore_index=True)
        
        fig = go.Figure(data=[
            go.Pie(
                labels=plot_df[names],
                values=plot_df[values],
                hole=0.3,
                marker=dict(
                    colors=self.color_scheme,
                    line=dict(color='white', width=2)
                ),
                textposition='auto',
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            template=self.template,
            height=500,
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        return fig
    
    def create_line_chart(
        self, 
        df: pd.DataFrame, 
        x: str, 
        y: str, 
        title: str,
        y2: Optional[str] = None
    ) -> go.Figure:
        if df.empty:
            return self._create_empty_chart(title)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df[x],
            y=df[y],
            mode='lines+markers',
            name=y,
            line=dict(color=self.color_scheme[0], width=3),
            marker=dict(size=6, color=self.color_scheme[0]),
            hovertemplate='<b>%{x}</b><br>' + y + ': %{y}<extra></extra>'
        ))
        
        if y2 and y2 in df.columns:
            fig.add_trace(go.Scatter(
                x=df[x],
                y=df[y2],
                mode='lines+markers',
                name=y2,
                line=dict(color=self.color_scheme[1], width=3, dash='dash'),
                marker=dict(size=6, color=self.color_scheme[1]),
                hovertemplate='<b>%{x}</b><br>' + y2 + ': %{y}<extra></extra>',
                yaxis='y2'
            ))
            
            fig.update_layout(
                yaxis2=dict(
                    title=y2,
                    overlaying='y',
                    side='right',
                    showgrid=False
                )
            )
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            xaxis_title=x,
            yaxis_title=y,
            template=self.template,
            height=500,
            margin=dict(l=50, r=50, t=80, b=100),
            hovermode='x unified',
            showlegend=True if y2 else False
        )
        
        fig.update_xaxes(tickangle=-45)
        
        return fig
    
    def create_grouped_bar_chart(
        self,
        df: pd.DataFrame,
        x: str,
        y_columns: list,
        title: str
    ) -> go.Figure:
        if df.empty:
            return self._create_empty_chart(title)
        
        fig = go.Figure()
        
        for idx, col in enumerate(y_columns):
            fig.add_trace(go.Bar(
                x=df[x],
                y=df[col],
                name=col,
                marker=dict(color=self.color_scheme[idx % len(self.color_scheme)]),
                hovertemplate='<b>%{x}</b><br>' + col + ': %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            xaxis_title=x,
            yaxis_title='Count',
            template=self.template,
            height=500,
            margin=dict(l=50, r=50, t=80, b=100),
            barmode='group',
            showlegend=True
        )
        
        fig.update_xaxes(tickangle=-45)
        
        return fig
    
    def _create_empty_chart(self, title: str) -> go.Figure:
        fig = go.Figure()
        
        fig.add_annotation(
            text="No data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color='#999')
        )
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=20, color='#333')),
            template=self.template,
            height=400,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        
        return fig
    
    def apply_chart_styling(self, fig: go.Figure) -> go.Figure:
        fig.update_layout(
            font=dict(family="Arial, sans-serif", size=12, color='#333'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial, sans-serif"
            )
        )
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)',
            showline=True,
            linewidth=1,
            linecolor='rgba(0,0,0,0.2)'
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)',
            showline=True,
            linewidth=1,
            linecolor='rgba(0,0,0,0.2)'
        )
        
        return fig
