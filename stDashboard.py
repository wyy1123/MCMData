# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objs as go
import datetime


def to_timedelta(date): 
    date = pd.to_datetime(date)
    try:
        date_start = datetime.datetime(date.year, date.month, date.day, 0, 0)
    except TypeError:
        return pd.NaT # to keep dtype of series; Alternative: pd.Timedelta(0)
    return date - date_start


#sidebar where we get user input variables
with st.sidebar:
    start_date = st.date_input('select a start date for data',datetime.date(2021,7,1))
    start_date = pd.to_datetime(start_date)
    end_date = st.date_input('select an end date for data',datetime.date(2021,10,1))
    end_date = pd.to_datetime(end_date)
    look_at_buy_exhaustions = st.checkbox('plot buyer exhaustion signals separately')
    if look_at_buy_exhaustions:
        buy_6minMA = st.checkbox('6min MA convergence as metric to measure buyer exhaustion signal')
        buy_percentile = st.number_input("buyer exhaustion percentile threshold")
    look_at_sell_exhaustions = st.checkbox('plot seller exhaustion signals separately')
    if look_at_sell_exhaustions:
        sell_6minMA = st.checkbox('6min MA convergence as metric to measure seller exhaustion signal')
        sell_percentile = st.number_input("seller exhaustion percentile threshold")
    #TODO: add filtering for market open
    filter_out_by_time= st.checkbox('Filter out signals from a certain period in a day(EST)')
    if filter_out_by_time:
        st.write('Please enter in the format of Hour:Minute, e.g. 19:40, 8:30')
        filter_start_time = st.text_input("start time","9:30")
        filter_end_time = st.text_input("end time","10:00")
        filter_start_time = to_timedelta(filter_start_time+':00')
        filter_end_time = to_timedelta(filter_end_time+':00')

        if filter_end_time < filter_start_time:
            st.write('Please enter a start time that\'s earlier than the end time')

        



df = pd.read_csv('SPTickTool.csv')
df['Timestamp'] = df['Timestamp'].apply(lambda x: pd.Timestamp(x))
df = df[np.logical_and(df['Timestamp']>=start_date,df['Timestamp']<=end_date)]
df['PriceLevel']= np.empty(df.shape[0])

#generates the signal dfs
seller_exhaustion_df = pd.read_csv('seller_exhaustion_evaluated.csv')
buyer_exhaustion_df = pd.read_csv('buyer_exhaustion_evaluated.csv')
# seller_exhaustion_df= seller_exhaustion_df.reset_index()
# buyer_exhaustion_df= buyer_exhaustion_df.reset_index()
buyer_exhaustion_df['Timestamp'] = buyer_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x))
seller_exhaustion_df['Timestamp'] = seller_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x))
if filter_out_by_time:
    # st.write(buyer_exhaustion_df['Timestamp'].apply(lambda x: to_timedelta(x)))
    buyer_exhaustion_df = buyer_exhaustion_df[np.logical_or(buyer_exhaustion_df['Timestamp'].apply(lambda x: to_timedelta(x)<filter_start_time), buyer_exhaustion_df['Timestamp'].apply(lambda x: to_timedelta(x)>filter_end_time))]
    seller_exhaustion_df= seller_exhaustion_df[np.logical_or(seller_exhaustion_df['Timestamp'].apply(lambda x: to_timedelta(x)<filter_start_time), seller_exhaustion_df['Timestamp'].apply(lambda x: to_timedelta(x)>filter_end_time))]
#     buyer_exhaustion_df = buyer_exhaustion_df.between_time(filter_end_time, filter_start_time)
#     seller_exhaustion_df = seller_exhaustion_df.between_time(filter_end_time, filter_start_time)

buyer_exhaustion_df = buyer_exhaustion_df[np.logical_and(buyer_exhaustion_df['Timestamp']>=start_date,buyer_exhaustion_df['Timestamp']<=end_date)]
seller_exhaustion_df = seller_exhaustion_df[np.logical_and(seller_exhaustion_df['Timestamp']>=start_date,seller_exhaustion_df['Timestamp']<=end_date)]
#TODO: filter them through date



#loads SP minute frequency data
SPData = pd.read_csv('minfrequencySP.csv')
SPData['Time'] = SPData['Time'].apply(lambda x: pd.Timestamp(x).tz_localize(None))
SPData = SPData[np.logical_and(SPData['Time']>=start_date,SPData['Time']<=end_date)]
SPData=SPData.reset_index()
#generates 6-min moving average
SPData['6minMA'] = SPData['Price'].rolling(6).mean()


#generates the plot
st.subheader('SP500 with MCM buy and sell exhaustion siganls')
fig = go.Figure(data =go.Scatter(x=seller_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=seller_exhaustion_df['PriceLevel'], mode='markers',name='Seller Exhaustion',marker = {'color':'green'}))
fig.add_trace(go.Scatter(x=SPData['Time'].apply(lambda x: pd.Timestamp(x)), y=SPData['Price']/100, mode='lines',name='SP500',fillcolor='blue',line = {'color':'blue'}))
fig.add_trace(go.Scatter(x=SPData['Time'].apply(lambda x: pd.Timestamp(x)), y=SPData['6minMA']/100, mode='lines',name='6minMA',fillcolor='orange',line = {'color':'orange'}))
fig.add_trace(go.Scatter(x=buyer_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=buyer_exhaustion_df['PriceLevel'], mode='markers',name='Buyer Exhaustion',marker = {'color':'red'}))
fig.update_layout(width=900,height=500)
st.plotly_chart(fig)


if look_at_buy_exhaustions:
    if buy_6minMA:
        buyer_exhaustion_df = buyer_exhaustion_df[buyer_exhaustion_df['Percentile']>=buy_percentile]
        winner_buyer_exhaustion_df = buyer_exhaustion_df[buyer_exhaustion_df['IsWinner']]
        loser_buyer_exhaustion_df = buyer_exhaustion_df[np.logical_not(buyer_exhaustion_df['IsWinner'])]
        st.subheader('SP500 with buyer exhaustion siganls evaluated based on 6min MA convergence')
        st.write('winning rate of all buyer exhaustion signals in this time period is', buyer_exhaustion_df[buyer_exhaustion_df['IsWinner']].shape[0],'/',buyer_exhaustion_df.shape[0])
        st.write('total P/L is',np.sum(buyer_exhaustion_df['P/L']))
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=SPData['Time'].apply(lambda x: pd.Timestamp(x)), y=SPData['Price']/100, mode='lines',name='SP500',fillcolor='blue',line = {'color':'blue'}))
        fig1.add_trace(go.Scatter(x=SPData['Time'].apply(lambda x: pd.Timestamp(x)), y=SPData['6minMA']/100, mode='lines',name='6minMA',fillcolor='orange',line = {'color':'orange'}))
        fig1.add_trace(go.Scatter(x=winner_buyer_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=winner_buyer_exhaustion_df['PriceLevel'], mode='markers',name='Successful Buyer Exhaustion Signals',marker = {'color':'green'}))
        fig1.add_trace(go.Scatter(x=loser_buyer_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=loser_buyer_exhaustion_df['PriceLevel'], mode='markers',name='Unsuccessful Buyer Exhaustion Signals',marker = {'color':'red'}))
        fig1.update_layout(width=1000,height=500)
        st.plotly_chart(fig1)
        st.write("table view of buyer exhaustion signals")
        st.write(buyer_exhaustion_df)


if look_at_sell_exhaustions:
    if sell_6minMA:
        seller_exhaustion_df = seller_exhaustion_df[seller_exhaustion_df['Percentile']>=sell_percentile]
        st.subheader('SP500 with seller exhaustion siganls evaluated based on 6min MA convergence')
        st.write('winning rate of all seller exhaustion signals in this time period is', seller_exhaustion_df[seller_exhaustion_df['IsWinner']].shape[0],'/',seller_exhaustion_df.shape[0])
        st.write('total P/L is',np.sum(seller_exhaustion_df['P/L']))
        winner_seller_exhaustion_df = seller_exhaustion_df[seller_exhaustion_df['IsWinner']]
        loser_seller_exhaustion_df = seller_exhaustion_df[np.logical_not(seller_exhaustion_df['IsWinner'])]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=SPData['Time'].apply(lambda x: pd.Timestamp(x)), y=SPData['Price']/100, mode='lines',name='SP500',fillcolor='blue',line = {'color':'blue'}))
        fig2.add_trace(go.Scatter(x=SPData['Time'].apply(lambda x: pd.Timestamp(x)), y=SPData['6minMA']/100, mode='lines',name='6minMA',fillcolor='orange',line = {'color':'orange'}))
        fig2.add_trace(go.Scatter(x=winner_seller_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=winner_seller_exhaustion_df['PriceLevel'], mode='markers',name='Successful Seller Exhaustion Signals',marker = {'color':'green'}))
        fig2.add_trace(go.Scatter(x=loser_seller_exhaustion_df['Timestamp'].apply(lambda x: pd.Timestamp(x)), y=loser_seller_exhaustion_df['PriceLevel'], mode='markers',name='Unsuccessful Seller Exhaustion Signals',marker = {'color':'red'}))
        fig2.update_layout(width=1000,height=500)
        st.plotly_chart(fig2)
        st.write("table view of seller exhaustion signals")
        st.write(seller_exhaustion_df)




# #helper functions:
# def add_price_levels(df):
    
#     df['PriceLevel']= np.empty(df.shape[0])
#     for i in range(df.shape[0]):
#         df.iloc[i,-1]=float(df['Content'].iloc[i].split('at: ')[1])
#     return df

# def  check_buy_exhaustion_convergence(df,spdf):
#     #checks how many minutes it takes the price to converge, and whether it's a winner, and how much does it win/lose
#     df['MinToConverge'] = np.empty(df.shape[0])
#     df['P/L'] = np.empty(df.shape[0])
#     df['IsWinner']=  np.empty(df.shape[0])
#     df['IsWinner']=  df['IsWinner'].apply(lambda x: False)
#     for i in range(df.shape[0]):
#         signal_time = df.loc[i,'Timestamp']
#         signal_price = df.loc[i,'PriceLevel']
#         row = spdf[np.logical_and(spdf['Time']>signal_time, spdf['MA crossed from above'])].iloc[0]
#         converge_time = row['Time']
#         converge_price = row['Price']/100
#         df.loc[i,'MinToConverge'] = converge_time-signal_time
#         df.loc[i,'P/L'] =  signal_price - converge_price
#         df.loc[i,'IsWinner'] = signal_price - converge_price > 0
#     return df

# def  check_sell_exhaustion_convergence(df,spdf):
#     #checks how many minutes it takes the price to converge, and whether it's a winner, and how much does it win/lose
#     df['MinToConverge'] = np.empty(df.shape[0])
#     df['P/L'] = np.empty(df.shape[0])
#     df['IsWinner']=  np.empty(df.shape[0])
#     df['IsWinner']=  df['IsWinner'].apply(lambda x: False)
#     for i in range(df.shape[0]):
#         signal_time = df.loc[i,'Timestamp']
#         signal_price = df.loc[i,'PriceLevel']
#         row = spdf[np.logical_and(spdf['Time']>signal_time, spdf['MA crossed from below'])].iloc[0]
#         converge_time = row['Time']
#         converge_price = row['Price']/100
#         df.loc[i,'MinToConverge'] = converge_time-signal_time
#         df.loc[i,'P/L'] =  converge_price - signal_price
#         df.loc[i,'IsWinner'] = converge_price - signal_price > 0
#     return df

#TODO: Delete this?
# #generates MA crossing data
# SPData['MA crossed from above'] = np.empty(SPData.shape[0])
# SPData['MA crossed from below'] = np.empty(SPData.shape[0])
# SPData['MA crossed from above'] = SPData['MA crossed from above'].apply(lambda x: False)
# SPData['MA crossed from below'] = SPData['MA crossed from below'].apply(lambda x: False)
# for i in range(6,SPData.shape[0]):
#     if SPData.loc[i-1,'Price']> SPData.loc[i-1,'6minMA'] and SPData.loc[i,'Price']<= SPData.loc[i,'6minMA']:
#         SPData.loc[i,'MA crossed from above']=True
#         print('MA crossed from above at', SPData.loc[i,'Time'])
#     if SPData.loc[i-1,'Price']< SPData.loc[i-1,'6minMA'] and SPData.loc[i,'Price']>= SPData.loc[i,'6minMA']:
#         SPData.loc[i,'MA crossed from below']=True
#         print('MA crossed from below at', SPData.loc[i,'Time'])