from pathlib import Path
import pandas as pd
import plotly.express as px

from datetime import date, datetime
import time
import numpy as np

class Timeline:
    def __init__(self,increment = 600,commit = 1649245858):
        self.commit = commit
        self.now = int(time.time())
        self.increment = increment

        self.df = self.get_df()
        self.timeline = self.create_timeline()
    
    def get_df(self):
        df = pd.read_csv(Path(__file__).parent/"emotions.csv")
        df = df[df["timestamps"].between(self.now,self.commit)]
        return df

    def get_dominant(self,start):
        df = self.df
        segment = df[df["timestamps"].between(start,start+self.increment)]
        if segment.shape[0] == 0:
            dominant = 0
        else:
            dominant = (segment["mood"].mode())
        return dominant

    def create_timeline(self):
        timeline = pd.DataFrame(columns=["timestamps","mood"])

        start = self.commit - self.commit%86400
        end = self.now + (86400-self.now%86400)

        days = int((end-start)/86400)
        for i in range(days*int(86400/self.increment)):
            print(i)
            details = {"timestamps":[start],"mood":[self.get_dominant(start)]}
            segment = pd.DataFrame(details)
            timeline = pd.concat([timeline,segment],ignore_index=True, sort=False)
            start += self.increment
        return timeline 

    def get_segment(self,start,end=None):
        if end is None:
            end = start + 86400
        df = self.timeline[self.timeline["timestamps"].between(start,end)]
        return df

    def figure(self,start):
        df = self.get_segment(start)
        fig = px.bar(df,x="timestamps",y="mood",color ="mood",height=200)
        fig.show()

    
timeline = Timeline()
