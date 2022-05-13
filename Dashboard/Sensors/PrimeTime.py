from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objects as go

import datetime
import time
import numpy as np

class Timeline:
    def __init__(self,commit = 1649245858,increment = 600):
        self.commit = commit
        self.now = 1649324368
        #self.now = time.time()

        self.colors = ["gray","#A30015","#7CB518","#2081C3","#FFDD00"]
        # NO FEELING , Tense , Excited, Fatigued, Calm
        self.og = ["gray","red","yellow","blue","green"]

        self.df = self.get_df()
        self.timeline = self.fill_timeline()
    
    def get_df(self):
        df = pd.read_csv(Path(__file__).parent/"emotions.csv")
        df = df[df["timestamps"].between(self.commit,self.now)]
        return df 

    def df_color(self,df,start,end):
        df = df[df["timestamps"].between(start,end)]
        if df.shape[0] == 0:
            mood = 0
        else:
            mood = df["emotions"].mode()[0]
        return mood
        
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
        df = df[df["timestamps"].between(start,end)]
        delta = int((end-start)/freq)
        stamps = []
        emotions = []
        values = []
        clock = 0
        for i in range(freq):
            stamps.append(clock)
            emotions.append(self.colors[self.df_color(df,start,start+delta)])
            values.append(1)
            start += delta
            clock += delta
        return pd.DataFrame({"timestamps":stamps,"emotions":emotions,"value":values})

    def fig(self,date,timerange=[0,24],freq=48):
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        unix = time.mktime(dt.timetuple())
        start = unix + int(timerange[0])*3600
        end = unix + int(timerange[1])*3600
        df = self.segment(start,end,freq)
        fig_ = go.Figure(data=[go.Bar(
            x = df["timestamps"].to_list(),
            y = df["value"].to_list(),
            marker_color = df["emotions"].to_list()
        )])
        hours = (end-start)/3600
        fig_.update_yaxes(visible=False, showticklabels=False)
        """fig_.update_xaxes(
            tickangle=45,
            tickmode="array",
            tickvals=clock)"""
        return fig_


