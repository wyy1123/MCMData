# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import plotly.graph_objs as go

df = pd.read_csv('SPTickTool.csv')
df['PriceLevel']= np.empty(df.shape[0])

#generates the signal dfs
seller_exhaustion_df = df[df['Content'].apply(lambda x: 'seller Exhaustion' in x)]
buyer_exhaustion_df = df[df['Content'].apply(lambda x: 'buyer Exhaustion' in x)]

def add_price_levels(df):
    
    df['PriceLevel']= np.empty(df.shape[0])
    for i in range(df.shape[0]):
        df.iloc[i,-1]=float(df['Content'].iloc[i].split('at: ')[1])
    return df

#adds the price levels and timestamps for signals
buyer_exhaustion_df = add_price_levels(buyer_exhaustion_df)
seller_exhaustion_df = add_price_levels(seller_exhaustion_df)

#loads SP minute frequency data
SPData = pd.read_csv('minfrequencySP.csv')


#generates the plot
fig = go.Figure(data =go.Scatter(x=seller_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=seller_exhaustion_df['PriceLevel']*100, mode='markers',name='Seller Exhaustion',marker = {'color':'red'}))
fig.add_trace(go.Scatter(x=SPData['Time'].apply(lambda x: pd.Timestamp(x)), y=SPData['Price'], mode='lines',name='SP500',fillcolor='blue',line = {'color':'blue'}))
fig.add_trace(go.Scatter(x=buyer_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=buyer_exhaustion_df['PriceLevel']*100, mode='markers',name='Buyer Exhaustion'))
st.plotly_chart(fig,width=800,height=500)