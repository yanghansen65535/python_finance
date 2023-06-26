# 周macd
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

######### choose one
end_time=datetime.strptime('20230105', '%Y%m%d') 
end_time=datetime.now()

start_time=end_time-timedelta(days=4*365)

prophet_week = 4 # 预测周

#设定周期period_type  转换为周是'W',月'M',季度线'Q',五分钟'5min',12天'12D'
period_type = 'W'
if mode == 'verify':
    end_time=end_time+timedelta(days=prophet_week*7)

file_name = code+'_week_'+mode+'.csv'
if data_mode == 'local':
    stock_data = pd.read_csv(file_name)
else:
    stock_data = ak.stock_zh_index_daily(code)
    #save
    stock_data.to_csv(file_name)

#print(stock_data)
stock_data['date'] = pd.to_datetime(stock_data['date'])
stock_data['bob'] = stock_data['date']
stock_data.set_index('date', inplace=True)
stock_data = stock_data[datetime.strftime(start_time, '%Y%m%d'):datetime.strftime(end_time, '%Y%m%d')]

prophet_lib.week_MACD_prophet(stock_data, mode, prophet_week, 1)
