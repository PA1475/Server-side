from pathlib import Path
import pandas as pd
import plotly.express as px

from datetime import date, datetime, timedelta
import time
import datetime
import numpy as np
start = 1649245858
now = time.time()

df = pd.read_csv(Path(__file__).parent/"emotions.csv")

day = f"{date.today()} --- {date.today()-timedelta(7)}"
print(day)