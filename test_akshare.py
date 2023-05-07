from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import akshare as ak
import mplfinance as mpf
import talib as tb


##### 东方财富 行业板块
#print(ak.stock_board_industry_name_em())
#exit()

#### 东方财富 行业板块 画图
symbol="珠宝首饰"
start_time_str = "20050101"
end_time_str = "202200507"
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


# 改 index   inplace是原地修改，不要创建一个新对象
data.set_index('bob', inplace=True)

# 进行转换，周线的每个变量都等于那一周中最后一个交易日的变量值
period_stock_data = data.resample(period_type).last()

# 周线的change等于那一周中每日change的连续相乘
#period_stock_data['change'] = stock_data['change'].resample(period_type,how=lambda x:(x+1.0).prod()-1.0)

# 周线的open等于那一周中第一个交易日的open
period_stock_data['open'] = data['open'].resample(period_type).first()

# 周线的high等于那一周中的high的最大值
period_stock_data['high'] = data['high'].resample(period_type).max()

# 周线的low等于那一周中的low的最小值
period_stock_data['low'] = data['low'].resample(period_type).min()

# 周线的volume和money等于那一周中volume和money各自的和
period_stock_data['volume'] = data['volume'].resample(period_type).sum()
period_stock_data['amount'] = data['amount'].resample(period_type).sum()
# 计算周线turnover
# period_stock_data['turnover'] = period_stock_data['volume']/\
#                                (period_stock_data['traded_market_value']/period_stock_data['close'])
# 股票在有些周一天都没有交易，将这些周去除
period_stock_data = period_stock_data[period_stock_data['open'].notnull()]
period_stock_data.reset_index(inplace=True)

period_stock_data.set_index("bob", inplace=True)
# print(period_stock_data)
data_macd = period_stock_data.copy(deep=True)
data_macd_count = len(data_macd)

macd, macdsignal, macdhist = tb.MACD(
    data_macd['close'], fastperiod=12, slowperiod=26, signalperiod=9)
# 计算，去掉前面一段没有MACD值
macd = pd.DataFrame(macd, columns=['0']).tail(data_macd_count-32)
macdsignal = pd.DataFrame(macdsignal, columns=['0']).tail(data_macd_count-32)
macdhist = pd.DataFrame(macdhist, columns=['0']).tail(data_macd_count-32)

# 前面一段没有MACD值
data_macd = data_macd.tail(data_macd_count-32)
data_macd_count = len(data_macd)

data_plot = period_stock_data.copy(deep=True)
data_plot = data_plot.tail(data_macd_count)

macdhist['ds'] = macdhist.index
macdhist.columns = ['y', 'ds']

add_plot = [mpf.make_addplot(macdhist['y'].tail(data_macd_count), type='bar', panel=2, ylabel='MACD', color='darkslateblue'),
            mpf.make_addplot(macd.tail(data_macd_count),
                                panel=2, color='orangered'),
            mpf.make_addplot(macdsignal.tail(
                data_macd_count), panel=2, color='limegreen')
            ]

mpf.plot(data_plot,
            type="candle",
            title="Week Candlestick",
            ylabel="price",
            style="charles",
            volume=True,
            addplot=add_plot,
            mav=(5, 10, 20, 30, 60)
            )
exit()

#######
stock_zh_index_daily_df = ak.stock_zh_index_daily(symbol="sh000905")
stock_zh_index_daily_df['date'] = pd.to_datetime(stock_zh_index_daily_df['date'])
stock_zh_index_daily_df.set_index("date", inplace=True)

mpf.plot(stock_zh_index_daily_df, 
         type="candle", 
         title="Candlestick for MSFT", 
         ylabel="price",
         style="charles",
         volume=True,
        mav=(5, 10, 20, 30, 60)
        )

