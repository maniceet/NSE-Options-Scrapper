#Importing libraries required
import re
from datetime import date
from nsepy import get_history
import numpy as np
import pandas as pd
import datetime 
from tqdm import tqdm
#Reading the options list file
options_list = pd.read_csv('options_list.csv')
stocks = list(options_list['Symbol'])
stocks = [x.replace('&', '%26') for x in stocks]
#stocks

#You can change this according to the task at Hand
start_date = datetime.date.today()-datetime.timedelta(10)
end_date = datetime.date.today()

import requests
from bs4 import BeautifulSoup

# Get all get possible expiry date details for the given script
def get_expiry_from_option_chain (symbol):

    # Base url page for the symbole with default expiry date
    Base_url = "https://www.nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?symbol=" + symbol + "&date=-"

    # Load the page and sent to HTML parse
    page = requests.get(Base_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    
    # Locate where expiry date details are available
    locate_expiry_point = soup.find(id="date")
    underlying_value = str(soup.find('b', {'style':"font-size:1.2em;"}))
    #print(underlying_value)
    underlying_value = re.sub(r'<.*?>', '', underlying_value)
    #print(underlying_value)
    underlying_value = float(re.sub(r'[^\d.]+', '', underlying_value))
    #underlying_value = soup.get_text(underlying_value)
    # Convert as rows based on tag option
    expiry_rows = locate_expiry_point.find_all('option')

    index = 0
    expiry_list = []
    for each_row in expiry_rows:
        # skip first row as it does not have value
        if index <= 0:
            index = index + 1
            continue
        index = index + 1
        # Remove HTML tag and save to list
        expiry_list.append(BeautifulSoup(str(each_row), 'html.parser').get_text())

    # print(expiry_list)
    return expiry_list, underlying_value # return list

def get_strike_price_from_option_chain(symbol, expdate):

    Base_url = "https://www.nseindia.com/live_market/dynaContent/live_watch/option_chain/optionKeys.jsp?symbol=" + symbol + "&date=" + expdate
    page = requests.get(Base_url)    
    soup = BeautifulSoup(page.content, 'html.parser')

    table_cls_2 = soup.find(id="octable")
    req_row = table_cls_2.find_all('tr')

    strike_price_list = []

    for row_number, tr_nos in enumerate(req_row):

        # This ensures that we use only the rows with values
        if row_number <= 1 or row_number == len(req_row) - 1:
            continue

        td_columns = tr_nos.find_all('td')
        strike_price = int(float(BeautifulSoup(str(td_columns[11]), 'html.parser').get_text()))
        strike_price_list.append(strike_price)
    #soup = BeautifulSoup(lot_page.content, 'html.parser')
    # print (strike_price_list)
    return strike_price_list

options_dict = {}
empty_returns = []
for stock in tqdm(stocks) :
    
    exp_dates, value = get_expiry_from_option_chain(stock)
    strike_prices = np.asarray(get_strike_price_from_option_chain(stock, exp_dates[0]))
    price_index = np.where(strike_prices > value)[0].tolist()
    
    if not price_index:
        empty_returns.append(stock)
        continue
        
    strike_price = float(strike_prices[price_index[0]])
    expiry_date = datetime.datetime.strptime(exp_dates[0], '%d%b%Y')
    stock_opt = get_history(symbol= stock,
                        start=start_date,
                        end= end_date,
                        option_type="CE",
                        strike_price= strike_price,
                        expiry_date= expiry_date)
    if stock_opt.empty:
        empty_returns.append(stock)
        #print(stock + " returned empty dataframe")
        continue
        
    if 'Stock' in options_dict:        
        options_dict['Underlying_value'].append(value)
        options_dict['Strike_price'].append(strike_price)
        options_dict['LTP'].append(float(stock_opt.iloc[[-1]]['Last']))
        options_dict['Stock'].append(stock)
        
    else:
        options_dict['Stock'] = [stock]
        options_dict['Underlying_value'] = [value]
        options_dict['Strike_price'] = [strike_price]
        options_dict['LTP'] = [float(stock_opt.iloc[[-1]]['Last'])]
    #print(stock+" done")

output = pd.DataFrame(options_dict)
lot_size = pd.read_csv('lotsize.csv')
lot_size['SYMBOL'] = lot_size['SYMBOL'].str.strip()
output2 = pd.merge(output, lot_size, how = 'left', left_on = ['Stock'], right_on = ['SYMBOL'])
output2.rename(columns = {'UNDERLYING' : 'Stock_Name'}, inplace = True)
output2.drop(['SYMBOL'], axis = 1, inplace = True)
output2.to_csv(exp_dates[0]+'list.csv', index = False)
print(empty_returns)
