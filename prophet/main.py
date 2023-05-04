import prophet_lib
from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import akshare as ak

mode = 'verify'
#mode = 'forecast'

data_mode = 'local'
#data_mode = 'remote'

symbol="小金属"
end_time_str="20220401"

# week
prophet_week = 4  # 预测周
if mode == 'forecast':
    end_time_dt=datetime.now()
    end_time_str=datetime.strftime(end_time_dt, '%Y%m%d')
else:
    end_time_dt=datetime.strptime(end_time_str, '%Y%m%d')    
start_time_dt=end_time_dt-timedelta(days=365*4)
start_time_str=datetime.strftime(start_time_dt, '%Y%m%d')

period_type = 'W'
file_name = symbol+'_week_'+mode+'_akshare.csv'

if data_mode == 'local':
    data = pd.read_csv(file_name)
else:
    if mode == 'forecast':
        data = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="")
    if mode == 'verify':
        data0 = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="")

        end_time_dt=end_time_dt+timedelta(days=prophet_week*7) 
        end_time_str=datetime.strftime(end_time_dt, '%Y%m%d') 

        data = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="")     
        #prophet_day = len(data)-len(data0) # 更新真实的预测天数
    # save 
    data.to_csv(file_name)
# replace 
data.rename(columns={'日期':'bob',
                    '开盘':'open',
                    '收盘':'close',
                    '最高':'high',
                    '最低':'low',
                    '成交量':'volume',
                    '成交额':'amount'},inplace=True) 

data['bob'] = pd.to_datetime(data['bob'])

data_forecast_week = prophet_lib.week_MACD_prophet(data, mode, prophet_week, 1)  

# day
prophet_day = 20 # 多几天用于预测。但是有周末，实际的天数比这个少

if mode == 'forecast':
    end_time_dt=datetime.now()
    end_time_str=datetime.strftime(end_time_dt, '%Y%m%d') 
else:
    end_time_dt=datetime.strptime(end_time_str, '%Y%m%d')
start_time_dt=end_time_dt-timedelta(days=365*2)
start_time_str=datetime.strftime(start_time_dt, '%Y%m%d')

file_name = symbol+'_day_'+mode+'_akshare.csv'
if data_mode == 'local':
    data = pd.read_csv(file_name)
else:
    if mode == 'forecast':
        data = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="")
    if mode == 'verify':
        data0 = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="")

        end_time_dt=end_time_dt+timedelta(days=prophet_day) 
        end_time_str=datetime.strftime(end_time_dt, '%Y%m%d') 

        data = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="")     
        prophet_day = len(data)-len(data0) # 更新真实的预测天数
    # save 
    data.to_csv(file_name)

# replace 
data.rename(columns={'日期':'bob',
                    '开盘':'open',
                    '收盘':'close',
                    '最高':'high',
                    '最低':'low',
                    '成交量':'volume',
                    '成交额':'amount'},inplace=True) 

#
data['bob'] = pd.to_datetime(data['bob'])    

data_forecast_day = prophet_lib.day_MACD_prophet(data, mode, prophet_day, 1)    