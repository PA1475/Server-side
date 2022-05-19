from importlib.resources import path
from pathlib import Path
from os.path import exists
from sqlite3 import Time
import pandas as pd
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objects as go

import datetime
import time
import numpy as np

class Timeline():
    def __init__(self):
        self.path = Path(__file__).parent.parent/"assets"

        # NO FEELING , Tense , Excited, Fatigued, Calm
        self.colors = ["gray","#A30015","#7CB518","#2081C3","#FFDD00"]
        self.og = ["gray","#A30015","#7CB518","#2081C3","#FFDD00"]

        self.now = time.time()
        self.commit = self.get_commit()
        self.df = self.get_df()
    
    def get_commit(self):
        if exists(f"{self.path}/time.txt"):
            with open(f"{self.path}/time") as f:
                commit = int(f.readline().rstrip())

        elif exists(f"{self.path}/emotions.csv"):
            df = pd.read_csv(f"{self.path}/emotions.csv")
            commit = df.iloc[0]["timestamps"]
        else:
            commit = self.now
        return commit
    
    def get_df(self):
        if exists(f"{self.path}/emotions.csv"):
            df = pd.read_csv(f"{self.path}/emotions.csv")
        else:
            df = pd.DataFrame(columns=["timestamps","emotions"])
        df = df[df["timestamps"].between(self.commit,self.now)]
        return df
    
    def mood(self,df,start,end):
        df = df[df["timestamps"].between(start,end)]
        if df.shape[0] == 0:
            mood = 0
        else:
            mood = df["emotions"].mode()[0]
        return int(mood)

    def segment(self,start,end,nbins):
        diff = int((end-start)/nbins)
        df = self.df
        df = df[df["timestamps"].between(start,end)]
        clock = start
        values = []
        coĺors = []
        timestamps = []
        while clock < end:
            timestamps.append(clock)
            values.append(1)
            coĺors.append(self.colors[self.mood(df,start,end)])
            clock += diff
        details = {"timestamps":timestamps,"colors":coĺors,"values":values}
        df = pd.DataFrame(details)
        return df

    def fig(self,nbins,date,timerange):
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        unix = int(time.mktime(dt.timetuple()))
        start = unix + int(timerange[0])*3600
        end = unix + int(timerange[1])*3600
        df = self.segment(start,end,nbins)
        fig = go.Figure(data=[go.Bar(
            x = df["timestamps"].to_list(),
            y = df["values"].to_list(),
            marker_color = df["colors"].to_list()
        )])
        return fig
