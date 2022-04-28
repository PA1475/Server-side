from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objects as go

from datetime import date, datetime, timedelta
import time
import numpy as np

class Screen:
    def get_date(self,value):
        day = date.today()-timedelta(value)
        return day.strftime('%m/%d/%Y')

    def get_unix(self,value):
        day = date.today()-timedelta(value)
        return int(day.strftime("%s"))


class Timeline:
    def __init__(self,commit = 1649245858,increment = 600):
        self.commit = commit
        self.now = 1649324368
        #self.now = time.time()

        self.colors = ["gray","red","green","blue","yellow"]
        self.og = ["gray","red","green","blue","yellow"]

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
        print(pd.unique(df["emotions"]))
        for i in range(freq):
            stamps.append(clock)
            emotions.append(self.colors[self.df_color(df,start,start+delta)])
            values.append(1)
            start += delta
            clock += delta
        df = pd.DataFrame({"timestamps":stamps,"emotions":emotions,"value":values})

        return df
    def fig(self,start,end,freq=48):
        df = self.segment(start,end,freq)
        fig = go.Figure(data=[go.Bar(
            x = df["timestamps"].to_list(),
            y = df["value"].to_list(),
            marker_color = df["emotions"].to_list()
        )])
        fig.show()

plot = Timeline()        
plot.fig(1649276548,1649276548+86400)


