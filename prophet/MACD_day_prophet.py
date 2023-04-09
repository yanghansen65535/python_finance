# day MACD - pro
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
mode = 'forecast'

set_token('489c24f4bfbed614673f6a766e9b298015c40f4b')
#code='SHSE.510500' #基金暂时不能复权
code='SHSE.000905' #中证500指数
end_time='2019-11-30'
end_time=datetime.strptime(end_time, '%Y-%m-%d') 
end_time = end_time+timedelta(days=7*17)
if mode == 'forecast':
    end_time=datetime.now()
start_time=end_time-timedelta(days=365*2)
prophet_day = 20 # 多几天用于预测。但是有周末，实际的天数比这个少

period_type = 'D'
if mode == 'forecast':
    data = history(symbol=code, frequency='1d', start_time=start_time, end_time=end_time,
              adjust=ADJUST_PREV, df=True)
if mode == 'verify':
    data0 = history(symbol=code, frequency='1d', start_time=start_time, end_time=end_time,
                adjust=ADJUST_PREV, df=True)    
    end_time=end_time+timedelta(days=prophet_day)              
    data = history(symbol=code, frequency='1d', start_time=start_time, end_time=end_time,
                adjust=ADJUST_PREV, df=True)
    prophet_day = len(data)-len(data0) # 更新真实的预测天数

data.set_index("bob", inplace=True)
data_macd = data.copy(deep=True)
data_macd_count = len(data_macd)

macd, macdsignal, macdhist = tb.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
# 计算，去掉前面一段没有MACD值
macd=pd.DataFrame(macd,columns=['0']).tail(data_macd_count-32)
macdsignal=pd.DataFrame(macdsignal,columns=['0']).tail(data_macd_count-32)
macdhist=pd.DataFrame(macdhist,columns=['0']).tail(data_macd_count-32)

# 前面一段没有MACD值
data_macd = data_macd.tail(data_macd_count-32)
data_macd_count = len(data_macd)

data_plot = data.copy(deep=True)
data_plot = data_plot.tail(data_macd_count)

macdhist['ds'] = macdhist.index
macdhist.columns = ['y','ds']
#print(macdhist)

data_prophet = macdhist.copy(deep=True)
if mode == 'verify':
    data_prophet = data_prophet[0:-prophet_day]  #减去用于预测的几天
data_prophet = data_prophet 

data_prophet['ds'] = data_prophet['ds'].dt.tz_localize(None)  # remove timezone
#print(data_prophet)

# 03 绘制原始趋势图
import plotly.express as px
fig1 = px.line(data_prophet, x="ds", y="y")
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
#model.add_seasonality(name='m5', period=5, fourier_order=5)
'''
#model.add_seasonality(name='m5', period=5, fourier_order=round(math.log(5,2)))
model.add_seasonality(name='m10', period=10, fourier_order=round(math.log(60,2)))
model.add_seasonality(name='m22', period=22, fourier_order=round(math.log(60,2)))
#model.add_seasonality(name='m30', period=30, fourier_order=round(math.log(30,2)))
model.add_seasonality(name='m60', period=60, fourier_order=round(math.log(60,2)))
model.add_seasonality(name='m120', period=120, fourier_order=round(math.log(60,2)))
#model.add_seasonality(name='m250', period=250, fourier_order=round(math.log(60,2)))
'''
#model.add_seasonality(name='m5', period=7, fourier_order=6)
model.add_seasonality(name='m10', period=14, fourier_order=2)
model.add_seasonality(name='m22', period=28, fourier_order=5)
#model.add_seasonality(name='m30', period=30, fourier_order=round(math.log(30,2)))
model.add_seasonality(name='m60', period=63, fourier_order=10)
model.add_seasonality(name='m120', period=120, fourier_order=20)
#model.add_seasonality(name='m250', period=250, fourier_order=round(math.log(60,2)))
model.fit(data_prophet)
          
# 05 模型预测
future = model.make_future_dataframe(periods=prophet_day, freq=period_type)
forecast = model.predict(future)        
#print(forecast)

# 05.1 绘制预测趋势图
#import plotly.express as px
fig2 = px.line(forecast, x="ds", y="yhat")
#fig2.show()

# 06 绘制分解图
from prophet.plot import plot_plotly, plot_components_plotly
from prophet.plot import add_changepoints_to_plot
#fig1 = model.plot(forecast)
#a = add_changepoints_to_plot(fig1.gca(), model, forecast)
#fig1.savefig('temp1.png')
#fig2 = model.plot_components(forecast)

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

if mode == 'forecast':
    # 注意macd_prophet_plot 的数据会多出 prophet_week 个
    # make_addplot 并不管时间，而是直接对应数据
    # 在原始数据后加 prophet_week 个空值
    index_append = pd.date_range(data_plot.index[-1] + timedelta(days=1), data_plot.index[-1]+timedelta(days=prophet_day), freq = period_type)
    data_plot = data_plot.append(pd.DataFrame(index = index_append, columns = data_plot.columns))
    macdhist = macdhist.append(pd.DataFrame(index = index_append, columns = macdhist.columns))
    macd = macd.append(pd.DataFrame(index = index_append, columns = macd.columns))
    macdsignal = macdsignal.append(pd.DataFrame(index = index_append, columns = macdsignal.columns))

    add_plot = [mpf.make_addplot(macdhist['y'].tail(data_macd_count+prophet_day),type='bar',panel=2,ylabel='daliy MACD',color='darkslateblue'),
                mpf.make_addplot(macd.tail(data_macd_count+prophet_day),panel=2,color='orangered'),
                mpf.make_addplot(macdsignal.tail(data_macd_count+prophet_day),panel=2,color='limegreen'),
                mpf.make_addplot(macd_prophet_plot.tail(data_macd_count+prophet_day),type='bar',panel=3,ylabel='daliy MACD_p',color='darkslateblue')
            ]

    mpf.plot(data_plot, 
            type="candle", 
            title="daliy candle", 
            ylabel="price",
            style="charles",
            volume=True,
            addplot=add_plot,
            vlines=forecast['ds'][data_macd_count],
            mav=(5, 10, 20, 30, 60)
            )

if mode == 'verify':
    add_plot = [mpf.make_addplot(macdhist['y'].tail(data_macd_count),type='bar',panel=2,ylabel='MACD',color='darkslateblue'),
            mpf.make_addplot(macd.tail(data_macd_count),panel=2,color='orangered'),
            mpf.make_addplot(macdsignal.tail(data_macd_count),panel=2,color='limegreen'),
            mpf.make_addplot(macd_prophet_plot.tail(data_macd_count),type='bar',panel=3,ylabel='MACD_p',color='darkslateblue')
           ]

    mpf.plot(data_plot, 
            type="candle", 
            title="daliy candle", 
            ylabel="price",
            style="charles",
            volume=True,
            addplot=add_plot,
            vlines=forecast['ds'][data_macd_count-prophet_day],
            mav=(5, 10, 20, 30, 60)
            )
