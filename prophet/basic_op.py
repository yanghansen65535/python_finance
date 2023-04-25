def code_convert(code):
    if code[0]=='0' and code[1]=='0':
        code=code+'.XSHE'     
    if code[0]=='3' and code[1]=='0':
        code=code+'.XSHE'         
    if code[0]=='6' and code[1]=='0':
        code=code+'.XSHG'
    if code[0]=='6' and code[1]=='8':
        code=code+'.XSHG'
    return code

import akshare as ak

#print(ak.__doc__)
#stock_zh_index_spot_df = ak.stock_zh_index_spot()
#print(stock_zh_index_spot_df)

#print(ak.stock_board_concept_name_em())   # 东方财富 概念板块
print(ak.stock_board_industry_name_em())  # 东方财富 行业板块