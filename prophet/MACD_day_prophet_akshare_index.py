# day MACD - pro
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
import mplfinance as mpf
import talib as tb
import math
from datetime import datetime
from datetime import timedelta

import akshare as ak
import prophet_lib

#mode = 'verify'
mode = 'forecast'

#data_mode = 'local'
data_mode = 'remote'

code='sh000905' #中证500指数

##########  choose  one
end_time=datetime.strptime('20230305', '%Y%m%d') 
#end_time=datetime.now()

start_time=end_time-timedelta(days=365*2)
prophet_day = 20 # 多几天用于预测。但是有周末，实际的天数比这个少

period_type = 'D'
file_name = code+'_day_'+mode+'.csv'
if data_mode == 'local':
    stock_data = pd.read_csv(file_name)
    stock_data['bob'] = pd.to_datetime(stock_data['bob'])
else:
    stock_data = ak.stock_zh_index_daily(code)
    if mode == 'forecast':
        stock_data['date'] = pd.to_datetime(stock_data['date'])
        stock_data['bob'] = stock_data['date']
        stock_data.set_index('date', inplace=True)
        stock_data = stock_data[datetime.strftime(start_time, '%Y%m%d'):datetime.strftime(end_time, '%Y%m%d')]
    if mode == 'verify':
        stock_data0 = stock_data
        stock_data0['date'] = pd.to_datetime(stock_data0['date'])
        stock_data0['bob'] = stock_data0['date']
        stock_data0.set_index('date', inplace=True)
        stock_data0 = stock_data0[datetime.strftime(start_time, '%Y%m%d'):datetime.strftime(end_time, '%Y%m%d')]

        end_time=end_time+timedelta(days=prophet_day)
        stock_data['date'] = pd.to_datetime(stock_data['date'])
        stock_data['bob'] = stock_data['date']
        stock_data.set_index('date', inplace=True)
        stock_data = stock_data[datetime.strftime(start_time, '%Y%m%d'):datetime.strftime(end_time, '%Y%m%d')]
        prophet_day = len(stock_data)-len(stock_data0) # 更新真实的预测天数
    #save
    stock_data.to_csv(file_name)

prophet_lib.day_MACD_prophet(stock_data, mode, prophet_day, 1)