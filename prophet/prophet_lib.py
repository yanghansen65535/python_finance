import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
import mplfinance as mpf
import talib as tb
import math
from datetime import datetime
from datetime import timedelta

# para - stock data
    # have bellow column:
    # '日期':'bob',  data time
    # '开盘':'open',
    # '收盘':'close',
    # '最高':'high',
    # '最低':'low',
    # '成交量':'volume',
    # '成交额':'amount'      
# para - mode: 'verify' or 'forecast'
# para - plot_en: 1, 0
# return data_forecast
def day_MACD_prophet(data, mode, prophet_day, plot_en):
    if mode != 'verify' and mode != 'forecast':
        print('day_MACD_prophet para-mode err')
        return -1
    period_type = 'D'
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
    model.add_seasonality(name='m22', period=28, fourier_order=4)
    #model.add_seasonality(name='m30', period=30, fourier_order=round(math.log(30,2)))
    model.add_seasonality(name='m60', period=63, fourier_order=12)
    model.add_seasonality(name='m120', period=120, fourier_order=18)
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
    if plot_en==1:
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
            
    return forecast

# para - data
    # have bellow column:
    # '日期':'bob',  data time
    # '开盘':'open',
    # '收盘':'close',
    # '最高':'high',
    # '最低':'low',
    # '成交量':'volume',
    # '成交额':'amount'     
# para - mode: 'verify' or 'forecast'
# para - plot_en: 1, 0
# return data_forecast
def week_MACD_prophet(stock_data, mode, prophet_week, plot_en):
    period_type = 'W'
        
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
    #period_stock_data['amount'] = stock_data['amount'].resample(period_type).sum()
    ##计算周线turnover
    #period_stock_data['turnover'] = period_stock_data['volume']/\
    #                                (period_stock_data['traded_market_value']/period_stock_data['close'])
    #股票在有些周一天都没有交易，将这些周去除
    period_stock_data = period_stock_data[period_stock_data['open'].notnull()]
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
    #fig = px.line(data_prophet, x="ds", y="y")
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
    model.add_seasonality(name='m20', period=20*7, fourier_order=round(20/5))
    model.add_seasonality(name='m50', period=50*7, fourier_order=round(30/5))
    model.add_seasonality(name='m100', period=100*7, fourier_order=round(50/5))
    model.add_seasonality(name='m200', period=200*7, fourier_order=round(50/5))
    model.fit(data_prophet)
            
    # 05 模型预测
    future = model.make_future_dataframe(periods=prophet_week, freq=period_type)
    forecast = model.predict(future)        
    #print(forecast)

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
    if plot_en==1:
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
                        title="Week Candlestick", 
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
                        vlines=forecast['ds'][data_macd_count],
                        mav=(5, 10, 20, 30, 60)
                        )
    return forecast


def day_to_week(stock_data):
    period_type = 'W'
    stock_data_week = stock_data.resample(period_type).last()
    stock_data_week['open'] = stock_data['open'].resample(period_type).first()
    stock_data_week['high'] = stock_data['high'].resample(period_type).max()
    stock_data_week['low'] = stock_data['low'].resample(period_type).min()
    stock_data_week['volume'] = stock_data['volume'].resample(period_type).sum()
    stock_data_week = stock_data_week[stock_data_week['open'].notnull()]
    return stock_data_week

# stock_data use datetime as index
def macd_add(stock_data):
    dif, dea, macd = tb.MACD(stock_data['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    macd_add = pd.DataFrame(data = zip(dif.values,dea.values,macd.values),
                        index = dif.index.tolist(),
                        columns=['dif','dea','macd'])
    data_merge = stock_data.join(macd_add,how='inner')
    return data_merge