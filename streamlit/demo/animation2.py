import streamlit as st
import pandas as pd
import numpy as np
import time

chart_placeholder = st.empty()
df = pd.DataFrame(columns=["value"])

for i in range(20):
    new_row = pd.DataFrame([{"value": np.random.randn()}])
    df = pd.concat([df, new_row], ignore_index=True)
    chart_placeholder.line_chart(df)
    time.sleep(0.2)
