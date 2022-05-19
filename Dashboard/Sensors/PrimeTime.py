from pathlib import Path
from os.path import exists

import pandas as pd
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objects as go

import datetime
import time
import numpy as np

class Timeline:
    def __init__(self,increment = 600):
        self.path = Path(__file__).parent.parent/"assets"
        self.commit = self.get_commit()
        self.now = time.time()

        # NO FEELING , Tense , Excited, Fatigued, Calm
        self.colors = ["#808080","#A30015","#7CB518","#2081C3","#FFDD00"]
        self.og = ["#808080","#A30015","#7CB518","#2081C3","#FFDD00"]

        self.df = self.get_df()
        self.timeline = self.fill_timeline()
    
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
        df["emotions"] = df["emotions"].astype(int)
        return df 

    def df_color(self,df,start,end):
        df = df[df["timestamps"].between(start,end)]
        if df.shape[0] == 0:
            mood = 0
        else:
            mood = df["emotions"].mode()[0]
        return int(mood)
        
    def fill_timeline(self):
        stamp = self.commit
        stamps = []
        emotions = []
        values = []
        while stamp < self.now:
            stamps.append(stamp)
            emotions.append(self.df_color(self.df,stamp,stamp+60))
            values.append(1)
            stamp += 60
        return pd.DataFrame({"timestamps":stamps,"emotions":emotions,"value":values})

    def segment(self,start,end,freq):
        df = self.timeline
        delta = int((end-start)//freq)
        stamps = []
        emotions = []
        values = []
        stamp = start
        while stamp < end:
            stamps.append(stamp)
            emotions.append(self.colors[self.df_color(df,stamp,stamp+delta)])
            values.append(1)
            stamp += delta
        df = pd.DataFrame({"timestamps":stamps,"emotions":emotions,"value":values})
        seconds = (df["timestamps"]%86400) + 7200
        stamps = []
        for i in range(freq):
            stamps.append(time.strftime("%H:%M",time.gmtime(seconds[i])))
        df["timestamps"] = stamps
        return df

    def fig(self,date,timerange=[0,24],freq=96):
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        unix = int(time.mktime(dt.timetuple()))
        start = unix + int(timerange[0])*3600
        end = unix + int(timerange[1])*3600
        df = self.segment(start,end,freq)
        fig = go.Figure(data=[go.Bar(
            x = df["timestamps"].to_list(),
            y = df["value"].to_list(),
            marker_color = df["emotions"].to_list()
        )])
        fig.update_yaxes(visible=False,showticklabels=False)
        return fig



