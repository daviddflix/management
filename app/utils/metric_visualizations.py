import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict
import pandas as pd

class MetricVisualizer:
    @staticmethod
    def create_burndown_chart(sprint_data: Dict) -> Dict:
        """Create sprint burndown chart"""
        df = pd.DataFrame(sprint_data['burndown_data'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['ideal'],
            name='Ideal Burndown',
            line=dict(color='rgba(0,128,0,0.5)', dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['actual'],
            name='Actual Burndown',
            line=dict(color='blue')
        ))
        
        return fig.to_dict()

    @staticmethod
    def create_velocity_trend(velocity_data: List[Dict]) -> Dict:
        """Create velocity trend chart"""
        df = pd.DataFrame(velocity_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['sprint'],
            y=df['velocity'],
            name='Sprint Velocity'
        ))
        fig.add_trace(go.Scatter(
            x=df['sprint'],
            y=df['average_velocity'],
            name='Average Velocity',
            line=dict(color='red', dash='dash')
        ))
        
        return fig.to_dict()

    @staticmethod
    def create_quality_dashboard(quality_data: Dict) -> Dict:
        """Create quality metrics dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Code Review Time',
                'Defect Density',
                'Rework Rate',
                'Test Coverage'
            )
        )
        
        # Add individual metric visualizations
        # ... Implementation details ...
        
        return fig.to_dict() 