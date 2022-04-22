
from calendar import month
from time import time
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
from Sensors.PrimeTime import Timeline





timeline = Timeline()
timelines = dcc.Graph(id="timelines")
days = f"{date.today()} --- {date.today()-timedelta(7)}"


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

colors = dbc.Row(
    [
        dbc.Col(html.Button("Blue",id="blue",n_clicks=0,style={"width":"300"})),
        dbc.Col(html.Button("Green",id="green",n_clicks=0,style={"width":"auto"})),
        dbc.Col(html.Button("Yellow",id="yellow",n_clicks=0,style={"width":"auto"})),
        dbc.Col(html.Button("Red",id="red",n_clicks=0,style={"width":"auto"})),
        dbc.Col(html.Button("Restart",id="restart",n_clicks=0,style={"width":"auto"}))
    ]
)

pick_date = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.Button("-",id="lower date",style={'width':30,"align":"right"})),
                dbc.Col(html.H2(f"{days}",style={'width':400,"align":"center"})),
                dbc.Col(html.Button("+",id="increase date",style={'width':30,"align":"left"}))  
            ]
                )

    ]
)

dates = html.Div(
    [
        timelines
    ]
)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div(
        [
            header,
            colors,
            pick_date,
            dates

        ]
            )
        
@app.callback(
    Input("blue","n_clicks"),
)
def update_color():
    timeline.change_color("blue")

@app.callback(
    Input("green","n_clicks")
)
def update_color():
    timeline.change_color("green")

@app.callback(
    Input("yellow","n_clicks")
)
def update_color():
    timeline.change_color("yellow")

@app.callback(
    Input("red","n_clicks")
)
def update_color():
    timeline.change_color("red")

@app.callback(
    Output("timeline","graph"),
    Input("restart","n_clicks")
)
def update_timelines():
    pass

if __name__ == '__main__':
    app.run_server(host='localhost', debug=True)