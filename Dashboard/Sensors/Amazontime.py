from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.subplots as sp

from datetime import date, datetime, timedelta
import time
import numpy as np


class Timeline:
    def __init__(self,commit = 1649245858,increment = 600):
        self.commit = commit
        self.increment = increment
        self.now = time.time()

        self.colors = ["gray","red","green","blue","yellow"]
        self.og = ["gray","red","green","blue","yellow"]

        self.df = self.get_df()
        self.timeline = self.create_timeline()
    
    def get_df(self):
        df = pd.read_csv(Path(__file__).parent/"emotions.csv")
        df = df[df["timestamps"].between(self.now,self.commit)]
        return df 

    def create_timeline(self):
        timeline = pd.DataFrame(columns=["timestamps","mood","value"])
        delta = int((self.now - self.commit)/self.increment)
        stamp = self.commit
        for i in range(delta):
            details = {"timestamp":stamp,"mood":self.average(stamp,stamp+self.increment),"value":1}
            segment = pd.DataFrame(details)
            timeline = pd.concat([timeline,segment],ignore_index=True)
            stamp += self.increment
        return timeline            
        
    def average(self,start,end):
        df = self.timeline
        df = df[df["timestamps"].between(start,end)]
        if df.shape[0] == 0:
            dominant = 0
        else:
            dominant = int(df["mood"].mode()[0])
        return self.colors[dominant]

    def figure(self,start,end):
        df = self.timeline
        df = df[df["timestamp"].between(start,end)]
        fig = px.bar(df,x="timestamp",y="value",color="mood")
        return fig

    def dates(self):
        now = self.now - self.now%86400
        then = self.commit - self.commit%86400
        delta = int((now-then)/86400)
        dates = []
        for i in range(delta):
            dates.append(date.today()-timedelta(i))



