from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.subplots as sp

from datetime import date, datetime
import time
import numpy as np


class Timeline:
    def __init__(self,increment = 600,commit = 1649245858):
        self.commit = commit
        self.now = time.time()
        self.increment = increment
        self.og_colors = ["grey","red","yellow","green","blue"]
        self.colors = ["grey","red","yellow","green","blue"]


        self.df = self.get_df()
        self.timeline = self.create_timeline()

    def get_time(self):
        return self.now
    
    def check_time(self,time):
        if time < self.commit:
            return self.commit
        if time > (self.get_time - self.get_time()%86400)():
            return (self.get_time() - self.get_time()%86400)
        else:
            return time


    def change_color(self,color):
        if self.colors[self.og_colors.index(color)] == self.og_colors[self.og_colors.index(color)]:
            self.color[self.og_colors.index(color)] = "gray"
        else:
            self.color[self.og_colors.index(color)] = color

    def restart(self):
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
            dominant = (segment["mood"].mode())[0]
        return self.colors[dominant]

    def create_timeline(self,now = None):
        timeline = pd.DataFrame(columns=["timestamps","mood"])
        self.now = int(time.time())


        end = self.now + (86400-self.now%86400)
        start = self.commit - self.commit%86400
        if end-start < 86400*8:
            start = end - 86400*8
        """
        IF statement makes sure the timeline always is 7 days long
        """


        days = int((end-start)/86400)
        for i in range(days*int(86400/self.increment)):
            details = {"timestamps":[start],"mood":[self.get_dominant(start)]}
            segment = pd.DataFrame(details)
            timeline = pd.concat([timeline,segment],ignore_index=True)
            start += self.increment
        return timeline 

    def get_segment(self,start,end=None):
        if end is None:
            end = start + 86400
        df = self.timeline[self.timeline["timestamps"].between(start,end)]
        return df

    def day(self,start):
        df = self.get_segment(start)
        fig = px.histogram(df,x="timestamps",color = "mood",nbins = int(86400/self.increment))
        return fig
    

