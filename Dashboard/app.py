import datetime
import dash
import os
from datetime import datetime, timedelta, date
import numpy as np
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from Sensors.Amazontime import Timeline

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
timeline = Timeline()

time_fig = dcc.Graph(id="timeline")
dates_list = timeline.dates()
dates = html.Col(
    [
        
    ]
)

header = dbc.Row(
            dbc.Container(
                [
                    html.H1("Emotional Aware Dashboard")
                ]
            ),
            className="text-white h-200 bg-dark",
            style={
                'padding' : 20,
                'textAlign': 'center'
            }
        )



app.layout = html.Div(
        [
            header
        ]
            )

if __name__ == '__main__':
    app.run_server(host='localhost', debug=True)