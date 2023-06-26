import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
import talib as tb
import mplfinance as mpf

import akshare as ak
import sys
sys.path.append("E:/proj_python/python_finance/prophet")
import prophet_lib

code='sh000905'
stock_data = ak.stock_zh_index_daily(code)
stock_data['date'] = pd.to_datetime(stock_data['date'])
#stock_data['bob'] = stock_data['date']
stock_data.set_index('date', inplace=True)
stock_data_d = prophet_lib.macd_add(stock_data)

'''add_plot = [mpf.make_addplot(stock_data_d['dif'].tail(100),panel=2,color='orangered'),
    mpf.make_addplot(stock_data_d['dea'].tail(100),panel=2,color='limegreen'),
    mpf.make_addplot(stock_data_d['macd'].tail(100),type='bar',panel=2,ylabel='MACD_p',color='darkslateblue')
]
mpf.plot(stock_data_d.tail(100), 
    type="candle", 
    title="Week Candlestick", 
    ylabel="price",
    style="charles",
    volume=True,
    addplot=add_plot,
    mav=(5, 10, 20, 30, 60)
    )'''

# to week
stock_data_week = prophet_lib.day_to_week(stock_data)
stock_data_w = prophet_lib.macd_add(stock_data_week)

'''add_plot = [mpf.make_addplot(stock_data_w['dif'].tail(100),panel=2,color='orangered'),
    mpf.make_addplot(stock_data_w['dea'].tail(100),panel=2,color='limegreen'),
    mpf.make_addplot(stock_data_w['macd'].tail(100),type='bar',panel=2,ylabel='MACD_p',color='darkslateblue')
]
mpf.plot(stock_data_w.tail(100), 
    type="candle", 
    title="Week Candlestick", 
    ylabel="price",
    style="charles",
    volume=True,
    addplot=add_plot,
    mav=(5, 10, 20, 30, 60)
    )'''
#print(stock_data_w)
######## filt out 
time_list = []
#print(stock_data_w.rolling(3))
for i in range(2,len(stock_data_w)):
    if pd.isnull(stock_data_w.iloc[i-2]['macd']):
        continue
    else:
        filter1 = ((stock_data_w.iloc[i]['dif'])<0) and ((stock_data_w.iloc[i]['dea'])<0)
        filter2 = ((stock_data_w.iloc[i-2]['macd'])>(stock_data_w.iloc[i-1]['macd'])) and ((stock_data_w.iloc[i]['macd'])>(stock_data_w.iloc[i-1]['macd']))
        filter3 = ((stock_data_w.iloc[i-2]['dif'])>(stock_data_w.iloc[i-1]['dif'])) and ((stock_data_w.iloc[i]['dif'])>(stock_data_w.iloc[i-1]['dif']))
        if ((filter1) and (filter2)) or ((not(filter1)) and (filter3)):
            #print(type(stock_data_w.iloc[i]))
            time_list.append(stock_data_w.iloc[i].name)
            #print(stock_data_w.iloc[i])
#print(time_list)

####### back test
result = pd.DataFrame(columns = ['date','0_high','0_low','1_high','1_low','2_high','2_low','3_high','3_low'])
# time  |  this week high low  |   1 week  high low   |   2 week  high low  |   3 week  high low
for i in range(2,len(stock_data_w)):
    if stock_data_w.iloc[i].name in time_list:
        if (i+3)<len(stock_data_w):
            append_data = [[stock_data_w.iloc[i].name, 
                            stock_data_w.iloc[i]['high'], stock_data_w.iloc[i]['low'], 
                      stock_data_w.iloc[i+1]['high'], stock_data_w.iloc[i+1]['low'],
                     stock_data_w.iloc[i+2]['high'], stock_data_w.iloc[i+2]['low'],
                     stock_data_w.iloc[i+3]['high'],stock_data_w.iloc[i+3]['low']]]
            #print((append_data))
            result = pd.concat([result, pd.DataFrame(append_data, columns = ['date','0_high','0_low','1_high','1_low','2_high','2_low','3_high','3_low'])])
            result.reset_index()
            #print(stock_data_w.iloc[i].name)
#print(result)
result.to_csv(code+'_backtest.csv')
