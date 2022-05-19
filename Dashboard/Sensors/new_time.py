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

class Timeline:
    def __init__(self):
        self.path = Path(__file__).parent.parent/"assets"

        # NO FEELING , Tense , Excited, Fatigued, Calm
        self.colors = ["gray","#A30015","#7CB518","#2081C3","#FFDD00"]
        self.og = ["gray","#A30015","#7CB518","#2081C3","#FFDD00"]

        self.now = time.time()
        self.commit = self.get_commit()
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
    
    def fill_timeline(self):
        if exists(f"{self.path}/emotions.csv"):
            df = pd.read_csv(f"{self.path}/emotions.csv")
        else:
            df = pd.DataFrame(columns=["timestamps","emotions"])
        start = self.commit
        end = start + 60
        stamps = []
        emotions = []
        values = []
        while start < self.now:
            stamps.append(start)
            values.append(1)
            emotions.append(self.mood(df,start,start+60))
            start += 60
        details = {"timestamps":stamps,"emotions":emotions,"value":values}
        return pd.DataFrame(details)
        
    def mood(self,df,start,end):
        df = df[df["timestamps"].between(start,end)]
        if df.shape[0] == 0:
            mood = 0
        else:
            mood = df["emotions"].mode()[0]
        return int(mood)
    
    def fig(self,date,timerange=[0,24],freq=48):
        df = self.segment(date,timerange,freq)
        fig = go.Figure(data=[go.Bar(
            x = df["timestamps"].to_list(),
            y = df["value"].to_list(),
            marker_color = df["emotions"].to_list()
        )])
        return fig
    
    def segment(self,date,timerange,freq):
        dt = datetime.datetime.strptime(date, '%Y-%m-%d')
        unix = int(time.mktime(dt.timetuple()))
        start = unix + int(timerange[0])*3600
        end = unix + int(timerange[1])*3600
        diff = int((end-start)/freq)
        clock = np.arange(start,end,diff)
        emotions = []
        values = []
        for i in range(diff):
            values.append(1)
            emotions.append(self.colors[self.mood(self.timeline,start,start+diff)])
            start += diff

        for x in clock:
            x = datetime.datetime.fromtimestamp(x).strftime("%H")

        """
        convert clock from unixtime to hours/minuts
        """
        details = {"timestamps":clock,"emotions":emotions,"values":values}
        return pd.DataFrame(details)    
