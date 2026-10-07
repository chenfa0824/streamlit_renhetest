# Streamlit DEMO4 绘制地图

import streamlit as st
import pandas
import numpy
#绘制地图
map_data = pandas.DataFrame(
    numpy.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
    columns=['lat', 'lon'])
st.map(map_data)


