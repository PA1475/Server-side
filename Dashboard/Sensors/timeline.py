from pathlib import Path
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

import time
import datetime
import numpy as np

class timeline:
    def __init__(self,commit_stamp=None):
        self.df = self.get_df()
        if commit_stamp == None:
            """
            If no timestamp is provided it will look in emotions.csv for the first timestamp
            """
            commit_stamp = 1649245858
        self.stamp = commit_stamp
        self.days = self.dates()

    def get_df(self):
        df = pd.read_csv("emotions.csv")
        return df
    
    def dates(self):
        now = round(time.time())
        delta = np.ceil((now - self.stamp)/86400)
        dates = []
        for i in range(int(delta)):
            date = datetime.date.today() - datetime.timedelta(i)
            dates.append(date)
        return dates

    def filter_df(self,start,end):
        df = self.df
        df = df[df['timestamps'] > start]
        df = df[df['timestamps'] < end]
        return df

    def timeline(self,date):
        start = date.strftime("%s")
        end = date + 86400
        df = self.filter_df(start,end)


x = timeline()
print(x.days[0].strftime("%s"))