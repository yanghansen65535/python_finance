from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import akshare as ak
import mplfinance as mpf
import talib as tb


##### 东方财富 行业板块
print(ak.stock_board_industry_name_em())
exit()

#### 东方财富 行业板块 画图
symbol="小金属"
end_time_str="20220401"

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

