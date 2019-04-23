#Importing libraries required
import re
from datetime import date
#from nsepy import get_history
import numpy as np
import pandas as pd
import datetime
from tqdm import tqdm
import requests
import io

#Reading the options list file online
response = requests.get('http://www.nseindia.com/content/fo/fo_mktlots.csv')

file_object = io.StringIO(response.content.decode('utf-8'))
lot_size = pd.read_csv(file_object, skiprows=[0,1,2,3], usecols = [0,1,2])
lot_size.columns = [x.replace(" ", "") for x in lot_size.columns]
lot_size['Symbol'] = lot_size['Symbol'].str.strip()


stocks = list(lot_size['Symbol'])
stocks = [x.replace('&', '%26') for x in stocks]
#stocks

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
    #lot_url = "https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuoteFO.jsp?underlying=" + symbol + "&instrument=FUTSTK&expiry=" + expdate+"&type=-&strike=-"
    page = requests.get(Base_url)
    #lot_page = requests.get(lot_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    table_cls_2 = soup.find(id="octable")
    req_row = table_cls_2.find_all('tr')

    strike_price_list = []
    call_volume_list = []
    put_volume_list = []
    call_ltp_list = []

    for row_number, tr_nos in enumerate(req_row):

        # This ensures that we use only the rows with values
        if row_number <= 1 or row_number == len(req_row) - 1:
            continue

        td_columns = tr_nos.find_all('td')
        strike_price = float(BeautifulSoup(str(td_columns[11]), 'html.parser').get_text())
        call_volume_list_html = BeautifulSoup(str(td_columns[3]), 'html.parser').get_text()
        put_volume_list_html = BeautifulSoup(str(td_columns[19]), 'html.parser').get_text()
        call_ltp_list_html =  BeautifulSoup(str(td_columns[5]), 'html.parser').get_text()
        call_ltp_list_html = str.strip(call_ltp_list_html).replace(",", "")
        
        num_format = re.compile("^[\-]?[1-9][0-9]*\.?[0-9]+$")
        
        if call_volume_list_html == "-":
            call_volume = 0
        else:
            call_volume = int(str.strip(call_volume_list_html).replace(",",""))
            
        if put_volume_list_html == "-":
            
            put_volume = 0
        else:
            put_volume = int(str.strip(put_volume_list_html).replace(",",""))
        
        if re.match(num_format, call_ltp_list_html):
            
            call_ltp = float(call_ltp_list_html)
        else:
            call_ltp = 0
            
            
        strike_price_list.append(strike_price)
        call_volume_list.append(call_volume)
        put_volume_list.append(put_volume)
        call_ltp_list.append(call_ltp)
        
    #soup = BeautifulSoup(lot_page.content, 'html.parser')
    # print (strike_price_list)
    return strike_price_list, call_volume_list, put_volume_list, call_ltp_list

options_dict = {}
empty_returns = []

for stock in tqdm(stocks) :
    try:
        
        exp_dates, value = get_expiry_from_option_chain(stock)
        
        strike_prices, call_volume_list, put_volume_list, call_ltp_list = \
                np.asarray(get_strike_price_from_option_chain(stock, exp_dates[0]))
        
        price_index = np.where(strike_prices > value)[0].tolist()
    
    except(ValueError, RuntimeError, TypeError, NameError):
        empty_returns.append(stock)
        continue
        
    if not price_index:
        empty_returns.append(stock)
        continue
        
    strike_price = float(strike_prices[price_index[0]])
    call_ltp_price = call_ltp_list[price_index[0]]
    expiry_date = datetime.datetime.strptime(exp_dates[0], '%d%b%Y')

    call_volume = sum(x for x in call_volume_list)
    put_volume = sum(x for x in put_volume_list)
    
    if 'Stock' in options_dict:        
        options_dict['Underlying_value'].append(value)
        options_dict['Strike_price'].append(strike_price)
        options_dict['call_LTP'].append(float(call_ltp_price))
        options_dict['Stock'].append(stock)
        options_dict['call_volume'].append(call_volume)
        options_dict['put_volume'].append(put_volume)
        
    else:
        options_dict['Stock'] = [stock]
        options_dict['Underlying_value'] = [value]
        options_dict['Strike_price'] = [strike_price]
        options_dict['call_LTP'] = [float(call_ltp_price)]
        options_dict['call_volume'] = [call_volume]
        options_dict['put_volume'] = [put_volume]

output = pd.DataFrame(options_dict)
output2 = pd.merge(output, lot_size, how = 'left', left_on = ['Stock'], right_on = ['Symbol'])

output2.rename(columns = {'DerivativesonIndividualSecurities' : 'Stock_Name',
                         'Underlying_value': 'Stock_Price'}, inplace = True)
output2.drop(['Symbol'], axis = 1, inplace = True)
output2['call_LTP*Lot'] = output2['call_LTP']*output2[output2.columns[7]]
output2['Price*Lot'] = output2['Stock_Price']*output2[output2.columns[7]]
print(output2.shape)
print(empty_returns)
output2.to_csv(exp_dates[0]+'list.csv', index = False)