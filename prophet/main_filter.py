import prophet_lib
from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import akshare as ak
import talib as tb

#mode = 'verify'
mode = 'forecast'

#data_mode = 'local'
data_mode = 'remote'

prophet_week = 4  # 预测周

#symbol="小金属"
end_time_str="20220401"  # useless

result_list = []

industry_list = ak.stock_board_industry_name_em()
for index, row in industry_list.iterrows():
    symbol = row["板块名称"]
    ################################
    # dif dea 不可全小于0
    start_time_str = '20050101'
    end_time_dt=datetime.now()
    end_time_str=datetime.strftime(end_time_dt, '%Y%m%d')
    period_type = 'W'
    data = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="hfq")

    data.rename(columns={'日期':'bob',
                        '开盘':'open',
                        '收盘':'close',
                        '最高':'high',
                        '最低':'low',
                        '成交量':'volume',
                        '成交额':'amount'},inplace=True)    

    data['bob'] = pd.to_datetime(data['bob'])
    data.set_index('bob', inplace=True)
    period_stock_data = data.resample(period_type).last()
    period_stock_data['open'] = data['open'].resample(period_type).first()
    period_stock_data['high'] = data['high'].resample(period_type).max()
    period_stock_data['low'] = data['low'].resample(period_type).min()
    period_stock_data['volume'] = data['volume'].resample(period_type).sum()
    period_stock_data['amount'] = data['amount'].resample(period_type).sum()
    period_stock_data = period_stock_data[period_stock_data['open'].notnull()]
    period_stock_data.reset_index(inplace=True)

    period_stock_data.set_index("bob", inplace=True)
    # print(period_stock_data)
    data_macd = period_stock_data.copy(deep=True)
    data_macd_count = len(data_macd)

    macd, macdsignal, macdhist = tb.MACD(
        data_macd['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    # 计算，去掉前面一段没有MACD值
    macd = pd.DataFrame(macd, columns=['0']).tail(data_macd_count-32)   # dif
    macdsignal = pd.DataFrame(macdsignal, columns=['0']).tail(data_macd_count-32)   #dea
    macdhist = pd.DataFrame(macdhist, columns=['0']).tail(data_macd_count-32)   # MACD

    dif = macd['0'].to_list()
    dea = macdsignal['0'].to_list()
    macd_hist = macdhist['0'].to_list()
    #if dif[-1]<0 and dea[-1]<0:
    #    continue
    ##################################
    # week
    
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

    data_forecast_week = prophet_lib.week_MACD_prophet(data, mode, prophet_week, 0)

    yhat = data_forecast_week['yhat'].to_list()

    filter1 = ((dif[-1]>0)or(dea[-1]>0))and(yhat[-1-prophet_week]<yhat[-prophet_week])
    filter2 = ((dif[-1]>0)and(dea[-1]>0))
    filter3 = ((dif[-1]<0)and(dea[-1]<0)and(dif[-1]>dif[-2]))

    if filter1 or filter2 or filter3:
        #####################################
        # day, 5天内有极小值
        prophet_day = 5
        start_time_dt=end_time_dt-timedelta(days=365*2)
        start_time_str=datetime.strftime(start_time_dt, '%Y%m%d')
        file_name = symbol+'_day_'+mode+'_akshare.csv'
        if data_mode == 'local':
            data = pd.read_csv(file_name)
        else:
            if mode == 'forecast':
                data = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="hfq")
            if mode == 'verify':
                data0 = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="hfq")

                end_time_dt=end_time_dt+timedelta(days=prophet_day) 
                end_time_str=datetime.strftime(end_time_dt, '%Y%m%d') 

                data = ak.stock_board_industry_hist_em(symbol=symbol, start_date=start_time_str, end_date=end_time_str, period="日k", adjust="hfq")     
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
        data_forecast_day = prophet_lib.day_MACD_prophet(data, mode, prophet_day, 0)  
        yhat = data_forecast_week['yhat'].to_list()
        # 5天内有极小值
        for i in range(0,prophet_day+1):
            if yhat[-1-i]>yhat[-2-i] and yhat[-2-i]<yhat[-3-i]:
                result_list.append(symbol)
    print(symbol)
print(result_list)
# save to csv
data = pd.DataFrame(data = result_list)
data.to_csv("_weekly_industry.csv")