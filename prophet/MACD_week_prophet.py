# 周macd
from __future__ import print_function, absolute_import
from gm.api import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
import mplfinance as mpf
import talib as tb
import math
from datetime import datetime
from datetime import timedelta

mode = 'verify'
#mode = 'forecast'

set_token('489c24f4bfbed614673f6a766e9b298015c40f4b')
end_time='2023-2-26'
end_time=datetime.strptime(end_time, '%Y-%m-%d') 
#end_time=datetime.now()
start_time=end_time-timedelta(days=3*365)
prophet_week = 4 # 预测周
#code='SHSE.510500' #基金暂时不能复权
code='SHSE.000905' #中证500指数

#设定周期period_type  转换为周是'W',月'M',季度线'Q',五分钟'5min',12天'12D'
period_type = 'W'
if mode == 'verify':
        end_time=end_time+timedelta(days=prophet_week*7)
stock_data = history(symbol=code, frequency='1d', start_time=start_time, end_time=end_time,
              adjust=ADJUST_PREV, adjust_end_time=end_time, df=True)

#print(stock_data)

#改 index   inplace是原地修改，不要创建一个新对象
stock_data.set_index('bob',inplace=True)

#进行转换，周线的每个变量都等于那一周中最后一个交易日的变量值
period_stock_data = stock_data.resample(period_type).last()

##周线的change等于那一周中每日change的连续相乘
#period_stock_data['change'] = stock_data['change'].resample(period_type,how=lambda x:(x+1.0).prod()-1.0)

#周线的open等于那一周中第一个交易日的open
period_stock_data['open'] = stock_data['open'].resample(period_type).first()

#周线的high等于那一周中的high的最大值
period_stock_data['high'] = stock_data['high'].resample(period_type).max()

#周线的low等于那一周中的low的最小值
period_stock_data['low'] = stock_data['low'].resample(period_type).min()

#周线的volume和money等于那一周中volume和money各自的和
period_stock_data['volume'] = stock_data['volume'].resample(period_type).sum()
period_stock_data['amount'] = stock_data['amount'].resample(period_type).sum()
##计算周线turnover
#period_stock_data['turnover'] = period_stock_data['volume']/\
#                                (period_stock_data['traded_market_value']/period_stock_data['close'])
#股票在有些周一天都没有交易，将这些周去除
period_stock_data = period_stock_data[period_stock_data['symbol'].notnull()]
period_stock_data.reset_index(inplace=True)

period_stock_data.set_index("bob", inplace=True)
#print(period_stock_data)
data_macd = period_stock_data.copy(deep=True)
data_macd_count = len(data_macd)


macd, macdsignal, macdhist = tb.MACD(data_macd['close'], fastperiod=12, slowperiod=26, signalperiod=9)
# 计算，去掉前面一段没有MACD值
macd=pd.DataFrame(macd,columns=['0']).tail(data_macd_count-32)
macdsignal=pd.DataFrame(macdsignal,columns=['0']).tail(data_macd_count-32)
macdhist=pd.DataFrame(macdhist,columns=['0']).tail(data_macd_count-32)

# 前面一段没有MACD值
data_macd = data_macd.tail(data_macd_count-32)
data_macd_count = len(data_macd)

data_plot = period_stock_data.copy(deep=True)
data_plot = data_plot.tail(data_macd_count)

macdhist['ds'] = macdhist.index
macdhist.columns = ['y','ds']
#print(macdhist)

data_prophet = macdhist.copy(deep=True)
if mode == 'verify':
        data_prophet = data_prophet[0:-prophet_week]  #减去用于预测的几周
data_prophet['ds'] = data_prophet['ds'].dt.tz_localize(None)  # remove timezone
#print(data_prophet)

# 03 绘制原始趋势图
import plotly.express as px
fig = px.line(data_prophet, x="ds", y="y")
#fig.show()

# 04 模型训练
model = Prophet(yearly_seasonality=False, 
                weekly_seasonality=False, 
                daily_seasonality=False,
               changepoint_prior_scale=1,
                changepoint_range=0.8,
                #mcmc_samples=0,
                n_changepoints=25,
                #interval_width=0.5,
               holidays_prior_scale=0.01)
                #growth="logistic")
#model.add_country_holidays(country_name="CN")
model.add_seasonality(name='m5', period=5*7, fourier_order=round(5/5))
model.add_seasonality(name='m10', period=10*7, fourier_order=round(10/5))
model.add_seasonality(name='m20', period=22*7, fourier_order=round(22/5))
model.add_seasonality(name='m60', period=60*7, fourier_order=round(60/5))
#model.add_seasonality(name='m120', period=120*7, fourier_order=round(120/5))
#model.add_seasonality(name='m250', period=250, fourier_order=20)
model.fit(data_prophet)
          
# 05 模型预测
future = model.make_future_dataframe(periods=prophet_week, freq=period_type)
forecast = model.predict(future)        
#print(forecast)

# 06 绘制分解图
from prophet.plot import plot_plotly, plot_components_plotly
from prophet.plot import add_changepoints_to_plot
fig1 = model.plot(forecast)
a = add_changepoints_to_plot(fig1.gca(), model, forecast)
#fig1.savefig('temp1.png')
fig2 = model.plot_components(forecast)

# 07 模型评估
train_len = len(data_prophet["y"])
rmse = np.sqrt(sum((data_prophet["y"] - forecast["yhat"].head(train_len)) ** 2) / train_len)
print(rmse)
print('RMSE Error in forecasts = {}'.format(round(rmse, 2)))

# 08 模型存储

# 模型保存
#with open('prophet_model.json', 'w') as md:
#    json.dump(model_to_json(model), md)

# 模型读取
#with open('prophet_model.json', 'r') as md:
#    model = model_from_json(json.load(md))

# plot to Candlestick
macd_prophet_plot = pd.DataFrame()
macd_prophet_plot['data'] = forecast['yhat'] #注意两个dataframe 的index得一致，所以先copy，再赋index
macd_prophet_plot.index = forecast['ds'] 

if mode == 'verify':
        add_plot = [mpf.make_addplot(macdhist['y'].tail(data_macd_count),type='bar',panel=2,ylabel='MACD',color='darkslateblue'),
            mpf.make_addplot(macd.tail(data_macd_count),panel=2,color='orangered'),
            mpf.make_addplot(macdsignal.tail(data_macd_count),panel=2,color='limegreen'),
            mpf.make_addplot(macd_prophet_plot.tail(data_macd_count),type='bar',panel=3,ylabel='MACD_p',color='darkslateblue')
           ]

        mpf.plot(data_plot, 
                type="candle", 
                title="Candlestick for MSFT", 
                ylabel="price",
                style="charles",
                volume=True,
                addplot=add_plot,
                vlines=forecast['ds'][data_macd_count-prophet_week],
                mav=(5, 10, 20, 30, 60)
                )

if mode == 'forecast':
        # 注意macd_prophet_plot 的数据会多出 prophet_week 个
        # make_addplot 并不管时间，而是直接对应数据
        # 在原始数据后加 prophet_week 个空值
        index_append = pd.date_range(data_plot.index[-1] + timedelta(days=7), data_plot.index[-1]+timedelta(days=prophet_week*7), freq = period_type)
        data_plot = data_plot.append(pd.DataFrame(index = index_append, columns = data_plot.columns))
        macdhist = macdhist.append(pd.DataFrame(index = index_append, columns = macdhist.columns))
        macd = macd.append(pd.DataFrame(index = index_append, columns = macd.columns))
        macdsignal = macdsignal.append(pd.DataFrame(index = index_append, columns = macdsignal.columns))

        add_plot = [mpf.make_addplot(macdhist['y'].tail(data_macd_count+prophet_week),type='bar',panel=2,ylabel='week MACD',color='darkslateblue'),
                mpf.make_addplot(macd.tail(data_macd_count+prophet_week),panel=2,color='orangered'),
                mpf.make_addplot(macdsignal.tail(data_macd_count+prophet_week),panel=2,color='limegreen'),
                mpf.make_addplot(macd_prophet_plot.tail(data_macd_count+prophet_week),type='bar',panel=3,ylabel='week MACD_p',color='darkslateblue')
                ]

        mpf.plot(data_plot, 
                type="candle", 
                title="Week Candlestick", 
                ylabel="price",
                style="charles",
                volume=True,
                addplot=add_plot,
                #vlines=forecast['ds'][data_macd_count],
                mav=(5, 10, 20, 30, 60)
                )
