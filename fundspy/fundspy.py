"""
This python based project helps you to extract and analyze data related to brazilian investment funds. It has functions to start and update a SQLite database containing cadastral information and daily quotas of all investment funds in brazil since 2005, as well as the ibovespa index and selic (the base interest rate of the brazilian economy). There are also functions to help you calculate important performance metrics for the investment funds, such as returns, volatility, correlation with indexes, beta, alpha, sharpe ratio, sortino ratio and capture ratios.

<b>Author:</b> <a href="https://www.linkedin.com/in/joao-penido-monteiro/">Joao Penido Monteiro</a>\n
<b>Github:</b> <a href="https://github.com/joaopm33/fundspy">Project repository</a>\n
<b>Examples:</b> <a href="https://jovian.ml/joaopm33/fundspy-example-notebook/v/8">Functions example notebook</a>\n
"""

#modules from the python standard library
import os
import os.path
import zipfile
import datetime
import calendar
import sqlite3

#packages used to download data
import requests
from requests import HTTPError
from yahoofinancials import YahooFinancials

#packages used to manipulate data
import pandas as pd
import numpy as np

#other packages
from tqdm import tqdm
from workalendar.america import Brazil
from dateutil.relativedelta import relativedelta

def cvm_informes (year: int, mth: int) -> pd.DataFrame:
    """Downloads the daily report (informe diario) from CVM for a given month and year\n

    <b>Parameters:</b>\n
    year (int): The year of the report the function should download\n
    mth (int): The month of the report the function should download\n

    <b>Returns:</b>\n
    pd.DataFrame: Pandas dataframe with the report for the given month and year. If the year is previous to 2017, will contain data regarding the whole year

   """

    if int(year) >= 2017: #uses download process from reports after the year of 2017
        try:
            mth = f"{mth:02d}"
            year = str(year)
            #creates url using the parameters provided to the function
            url = 'http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_'+year+mth+'.csv'
            
            #reads the csv returned by the link
            cotas = pd.read_csv(url, sep =';')
            cotas['DT_COMPTC'] = pd.to_datetime(cotas['DT_COMPTC']) #casts date column to datetime
            
            try:
                #removes column present in only a few reports to avoid inconsistency when making the union of reports
                cotas.drop(columns = ['TP_FUNDO'], inplace = True)
            except KeyError:
                pass
            
            return cotas
        except HTTPError:
            print('theres no report for this date yet!.\n')
    
    if int(year) < 2017:
        try:
            year = str(year)

            url = 'http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/HIST/inf_diario_fi_' + year + '.zip'
            #sends request to the url
            r = requests.get(url, stream=True, allow_redirects=True)
            
            with open('informe' + year + '.zip', 'wb') as fd: #writes the .zip file downloaded
                fd.write(r.content)

            zip_inf = zipfile.ZipFile('informe' + year + '.zip') #opens the .zip file
            
            #le os arquivos csv dentro do arquivo zip
            informes = [pd.read_csv(zip_inf.open(f), sep=";") for f in zip_inf.namelist()] 
            cotas = pd.concat(informes,ignore_index=True)
            
            cotas['DT_COMPTC'] = pd.to_datetime(cotas['DT_COMPTC']) #casts date column to datetime

            zip_inf.close() #fecha o arquivo zip
            os.remove('informe' + year + '.zip') #deletes .zip file
            
            return cotas
        
        except Exception as E:
            print(E)           


def start_db(db_dir: str = 'investments_database.db', start_year: int = 2005, target_funds: list = []):
    """Starts a SQLite database with 3 tables: daily_quotas (funds data), ibov_returns (ibovespa index data) and selic_rates (the base interest rate for the brazilian economy).\n 

    <b>Parameters:</b>\n
    db_dir (str): The path of the dabatabse file to be created. Defaults to 'investments_database.db', creating the file in the current working directory.\n
    start_year (int): Opitional (Defaults to 2005). Starting year for the data collection. . Can be use to reduce the size of the database.\n
    target_funds (list): Opitional (Defaults to []). List of target funds CNPJs. Only funds with CNPJs contained in this list will be included in the database. Can be used to radically reduce the size of the database. If none is specified, all funds will be included.\n

    <b>Returns:</b>\n
    Theres no return from the function.

   """
    ##STEP 1:
    #starts the new database
    print (f'creating SQLite database: {db_dir} \n')
    con = sqlite3.connect(db_dir)


    ##STEP 2:
    #downloads each report in the cvm website and pushes it to the sql database daily_quotas table
    print('downloading daily reports from the CVM website... \n')

    #for each year between 2017 and now
    for year in tqdm(range(start_year, datetime.date.today().year + 1), position = 0, leave=True): 
        for mth in range(1, 13): #for each month
            #loop structure for years equal or after 2017
            if year>=2017: 
                informe = cvm_informes(str(year), mth)

                try:
                    if target_funds: #if the target funds list is not empty, uses it to filter the result set
                        informe = informe[informe.CNPJ_FUNDO.isin(target_funds)]
                    #appends information to the sql database
                    informe.to_sql('daily_quotas', con , if_exists = 'append', index=False)
                except AttributeError:
                    pass
            
            elif year<2017: #loop structure to handle years before 2017 (they have a different file structure)
                #only executes the download function once every year to avoid duplicates (unique file for each year)       
                if mth == 12:
                    informe = cvm_informes(str(year), mth)

                    try:
                        if target_funds: #if the target funds list is not empty, uses it to filter the result set
                            informe = informe[informe.CNPJ_FUNDO.isin(target_funds)]
                        #appends information to the sql database
                        informe.to_sql('daily_quotas', con , if_exists = 'append', index=False)
                    except AttributeError:
                        pass

    #pushes target funds to sql for use when updating the database
    if target_funds:
        target_df = pd.DataFrame({'targets':target_funds})
        target_df.to_sql('target_funds', con , index=False)                    
    ##STEP 3:                    
    #creates index in the daily_quotas table to make future select queries faster. 
    #tradeoff: The updating proceesses of the database will be slower.
    print('creating sql index on "CNPJ_FUNDO", "DT_COMPTC" ... \n')
    index = '''
    CREATE INDEX "cnpj_date" ON "daily_quotas" (
        "CNPJ_FUNDO" ASC,
        "DT_COMPTC" ASC
    )'''

    cursor = con.cursor()
    cursor.execute(index)
    con.commit()

    cursor.close()

    
    ##STEP 4:
    #downloads cadastral information from CVM of the fundos and pushes it to the database
    print('downloading cadastral information from cvm...\n')
    info_cad = pd.read_csv('http://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv', sep = ';', encoding='latin1',
                           dtype = {'RENTAB_FUNDO': object,'FUNDO_EXCLUSIVO': object, 'TRIB_LPRAZO': object, 'ENTID_INVEST': object,
                                    'INF_TAXA_PERFM': object, 'INF_TAXA_ADM': object, 'DIRETOR': object, 'CNPJ_CONTROLADOR': object,
                                    'CONTROLADOR': object}
                            )
    if target_funds:
        info_cad = info_cad[info_cad.CNPJ_FUNDO.isin(target_funds)]
    info_cad.to_sql('info_cadastral_funds', con, index=False)


    ##STEP 5:
    #downloads daily ibovespa prices from investing.com and pushes it to the database
    print('downloading ibovespa index prices from investing.com ...\n')
    today = (datetime.date.today() + datetime.timedelta(1)).strftime('%Y-%m-%d')
    ibov = pd.DataFrame(YahooFinancials('^BVSP').get_historical_price_data('1990-09-15', today, 'daily')['^BVSP']['prices'])
    ibov = ibov.drop(columns=['date', 'close']).rename(columns={'formatted_date':'date', 'adjclose':'close'}).iloc[:,[5,0,1,2,3,4]]
    ibov['date'] = pd.to_datetime(ibov['date'])
    ibov.columns = [i.capitalize() for i in ibov.columns] #capitalizes columns to keep consistency with previous format (investpy)
    ibov.to_sql('ibov_returns', con, index=False) 


    ##STEP 6:
    #downloads daily selic returns (basic interest rate of the brazilian economy) 
    #from the brazillian central bank and pushes it to the database
    print('downloading selic rates from the Brazilian Central Bank website...\n')
    selic = pd.read_json('http://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json'.format(11))
    selic['data'] = pd.to_datetime(selic['data'], format = '%d/%m/%Y')
    selic['valor'] = selic['valor']/100 #calculates decimal rate from the percentual value

    #calculates asset "price" considering day 0 price as 1
    selic.loc[0,'price'] = 1 * (1 + selic.loc[0,'valor'])
    for i in range(1, len(selic)):
        selic.loc[i, 'price'] = selic.loc[i-1, 'price'] * (1 + selic.loc[i,'valor'])

    selic.rename(columns = {'data':'date', 'valor':'rate'}, inplace = True)
    selic.to_sql('selic_rates', con , index=False)  


    ##STEP 7:
    #creates a table with a log of the execution timestamps of the script
    print('creating the log table...\n')
    update_log = pd.DataFrame({'date':[datetime.datetime.now()], 'log':[1]})
    update_log.to_sql('update_log', con, if_exists = 'append', index=False)


    ##STEP 8
    #closes the connection with the database
    con.close()
    print('connection with the database closed! \n')

    print(f'Success: database created in {db_dir} !\n')


def update_db(db_dir: str = r'investments_database.db'):
    """Updates the database.\n

    <b>Parameters:</b>\n
    db_dir (str): The path of the dabatabse file to be updated. Defaults to 'investments_database.db'.\n

    <b>Returns:</b>\n
    Theres no return from the function.

   """
    ##STEP 1
    #connects to the database
    print(f'connected with the database {db_dir}\n')
    con = sqlite3.connect(db_dir)


    ##STEP 2
    #calculates relevant date limits to the update process
    Cal=Brazil() #inicializes the brazillian calendar
    today = datetime.date.today()

    #queries the last update from the log table
    last_update = pd.to_datetime(pd.read_sql('select MAX(date) from update_log', con).iloc[0,0])

    last_quota = Cal.sub_working_days(last_update, 2) #date of the last published cvm repport
    num_months = (today.year - last_quota.year) * 12 + (today.month - last_quota.month) + 1


    ##STEP 3
    #delete information that will be updated from the database tables
    print('deleting redundant data from the database... \n')
    tables = {'daily_quotas' : ['DT_COMPTC',last_quota.strftime("%Y-%m-01")],
              'ibov_returns' : ['Date',last_update.strftime("%Y-%m-%d")]}
    
    cursor = con.cursor()
    
    #sql delete statement to the database
    cursor.execute('delete from daily_quotas where DT_COMPTC >= :date', {'date': last_quota.strftime("%Y-%m-01")})
    cursor.execute('delete from ibov_returns where Date >= :date', {'date': last_update.strftime("%Y-%m-%d")})
        
    con.commit()  
    cursor.close()


    ##STEP 4
    #Pulls new data from CVM, investpy and the brazilian central bank
    #and pushes it to the database

    try:#tries to read targets funds if they were specified when starting the database
        target_funds = pd.read_sql('select targets from target_funds', con).targets.to_list()
    except AttributeError:
        target_funds = []
    
    print('downloading new daily reports from the CVM website...\n')
    # downloads the daily cvm repport for each month between the last update and today
    for m in range(num_months+1): 
        data_alvo = last_quota + relativedelta(months=+m) 
        informe = cvm_informes(data_alvo.year, data_alvo.month)
        if target_funds:
            informe = informe[informe.CNPJ_FUNDO.isin(target_funds)]
        try:
            informe.to_sql('daily_quotas', con , if_exists = 'append', index=False)
        except AttributeError:
            pass 

    #downloads cadastral information from CVM of the fundos and pushes it to the database
    print('downloading updated cadastral information from cvm...\n')
    info_cad = pd.read_csv('http://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv', sep = ';', encoding='latin1',
                           dtype = {'RENTAB_FUNDO': object,'FUNDO_EXCLUSIVO': object, 'TRIB_LPRAZO': object, 'ENTID_INVEST': object,
                                    'INF_TAXA_PERFM': object, 'INF_TAXA_ADM': object, 'DIRETOR': object, 'CNPJ_CONTROLADOR': object,
                                    'CONTROLADOR': object}
                            )
    if target_funds: #filters target funds if they were specified when building the database.
        info_cad = info_cad[info_cad.CNPJ_FUNDO.isin(target_funds)]
    info_cad.to_sql('info_cadastral_funds', con, if_exists='replace', index=False)

    #updates daily interest returns (selic)
    print('updating selic rates...\n')
    selic = pd.read_json('http://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json'.format(11))
    selic['data'] = pd.to_datetime(selic['data'], format = '%d/%m/%Y')
    selic['valor'] = selic['valor']/100 #calculates decimal rate from the percentual value

    #calculates asset "price" considering day 0 price as 1
    selic.loc[0,'price'] = 1 * (1 + selic.loc[0,'valor'])
    for i in range(1, len(selic)):
        selic.loc[i, 'price'] = selic.loc[i-1, 'price'] * (1 + selic.loc[i,'valor'])

    selic.rename(columns = {'data':'date', 'valor':'rate'}, inplace = True)

    #filters only new data
    selic = selic[selic.date>=(last_update + datetime.timedelta(-1))]
    selic.to_sql('selic_rates', con , if_exists = 'append', index=False) 

    #updates ibovespa data
    print('updating ibovespa returns...\n')
    today = (datetime.date.today() + datetime.timedelta(1)).strftime('%Y-%m-%d')
    ibov = pd.DataFrame(YahooFinancials('^BVSP').get_historical_price_data(last_update.strftime('%Y-%m-%d'), today, 'daily')['^BVSP']['prices'])
    ibov = ibov.drop(columns=['date', 'close']).rename(columns={'formatted_date':'date', 'adjclose':'close'}).iloc[:,[5,0,1,2,3,4]]
    ibov['date'] = pd.to_datetime(ibov['date'])
    ibov.columns = [i.capitalize() for i in ibov.columns] #capitalizes columns to keep consistency with previous format (investpy)
    ibov.to_sql('ibov_returns', con , if_exists = 'append', index=False)

    ##STEP 5
    #updates the log in the database
    print('updating the log...\n')
    update_log = pd.DataFrame({'date':[datetime.datetime.now()], 'log':[1]})
    update_log.to_sql('update_log', con, if_exists = 'append', index=False)


    ##STEP 6
    #closes the connection with the database
    con.close()
    print('connection with the database closed!\n')

    print(f'database {db_dir} updated!\n')


def returns(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA'], rolling: bool = False, window_size: int = 1) -> pd.DataFrame:
    """Calculates the % returns for the given assets both in rolling windows or for the full available period (you also get the CAGR in this case).\n

    <b>Parameters</b>:\n
    df (pd.DataFrame): Pandas dataframe with the needed columns.\n
    group (str): name of the column in the dataframe used to group values (example: 'stock_ticker' or 'fund_code').\n
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark prices (Example: ['asset_price', 'index price']).\n
    rolling (bool): True or False. Indicates if the function will return total returns for each asset or rolling window returns.\n
    window_size: (int): Default = 1. Only useful if rolling = True. Defines the size of the rolling window wich the returns will be calculated over.\n

    <b>Returns:</b>\n
    pd.DataFrame: If rolling = True: Pandas dataframe with total % returns for the assets. If rolling = False: The original pandas dataframe with added columns for the % returns in the rolling windows.

   """
    if not rolling:
        window_size = 1

    #garantees that the values are positive, once division by zero returns infinite
    returns = df.copy(deep=True)
    for col in values:
        returns = returns[returns[col]>0]
    returns.loc[:, values] = returns.loc[:, values].fillna(method = 'backfill')

    #calculates the percentual change in the rolling windows specified for each group
    returns = returns.groupby(group, sort = False, as_index = True)[values].apply(lambda x: x.pct_change(window_size))
    
    #renames the columns
    col_names = [(value + '_return_' + str(window_size) + 'd') for value in values]
    returns.columns = col_names

    #if the parameter rolling = False, returns the original data with the added rolling returns
    if rolling:
        df2 = df.merge(returns, how='left', left_index=True, right_index=True)
        return df2

    #if the parameter rolling = True, returns the total compound returns in the period, the number of days
    # and the Compound Annual Growth Rate (CAGR)
    if not rolling: 
        returns = df[[group]].merge(returns, left_index = True, right_index = True)
        
        #calculates the compound returns
        returns = returns.groupby(group, sort = False, as_index = True).apply(lambda x: np.prod(1+x) - 1)
        
        #calculates the number of days in the period
        n_observations =  df.groupby(group, sort = False, as_index = True)[values[0]].count()
        returns = returns.merge(n_observations, left_index = True, right_index = True)
        
        #renames the columns in the result set
        col_names = [(value + '_cum_return') for value in values]
        col_names.append('days')
        returns.columns = col_names
        
        #calculates the Compound Annual Growth Rate (CAGR)
        values = col_names[:-1]        
        col_names = [i.replace('_cum_return', '_cagr') for i in values]
        returns[col_names] = (returns.dropna()
                                     .loc[:,values]
                                     .apply(lambda x: ((x + 1)**(252/returns.days))-1))

        return returns                                   

    raise Exception("Wrong Parameter: rolling can only be True or False.") 
        

def cum_returns(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA']) -> pd.DataFrame:
    """Calculates the cumulative % returns for the given assets.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed columns.\n
    group (str): name of the column in the dataframe used to group values (example: 'stock_ticker' or 'fund_code').\n
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark prices (Example: ['asset_price', 'index price']).\n
   
    <b>Returns:</b>\n
    pd.DataFrame: A pandas dataframe with the cumulative % returns for each asset.

   """
    returns_df = returns(df, group = group, values = values, rolling=True) #calculates  the daily returns
    
    #calculates the cumulative returns in each day for each group
    cum_returns = returns_df.groupby(group)[[value + '_return_1d' for value in values]].expanding().apply(lambda x: np.prod(x+1)-1)
    
    #renames the columns
    cum_returns.columns = [i + '_cum_return' for i in values]
    cum_returns.reset_index(level = 0, inplace = True)

    cum_returns = returns_df.merge(cum_returns, how = 'right', on = group, left_index = True, right_index = True)
    return cum_returns


def volatility(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA_return_1d'], rolling: bool = False ,returns_frequency: int = 1, window_size: int = 21) -> pd.DataFrame:
    """Calculates the annualized volatillity (standard deviation of returns with degree of freedom = 0) for givens assets returns both in rolling windows or for the full available period.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'.\n
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark returns. Example: ['asset_price', 'index price']. \n
    rolling (bool): True or False. Indicates if the function will return total volatility for each asset or rolling window volatility.\n
    returns_frequency: (int): Default = 1. Indicates the frequency in days of the given returns. Should be in tradable days (252 days a year, 21 a month, 5 a week for stocks). This number is used to anualize the volatility.\n
    window_size: (int): Default = 252. Only useful if rolling = True. Defines the size of the rolling window wich the volatility will be calculated over.\n

    <b>Returns:</b>\n
    pd.DataFrame: If rolling = False: Pandas dataframe with total volatility for the assets. If rolling = True: The original pandas dataframe with added columns for the volatility in the rolling windows.

   """
    if not rolling:
        vol = df.copy(deep=True)
        for col in values:
            vol = df[df[col].notnull()]

        vol = vol.groupby(group)[values].std(ddof=0) 
        
        #renames the columns
        col_names = [(value + '_vol') for value in values]        
        vol.columns = col_names

        #annualizes the volatility
        vol[col_names]= vol[col_names].apply(lambda x : x *((252/returns_frequency)**0.5))
        
        return vol

    if rolling: 
        vol = df.copy(deep=True)
        for col in values:
            vol = df[df[col].notnull()]
        
        vol = (vol.groupby(group)[values]
                  .rolling(window_size)
                  .std(ddof=0) #standards deviation in the rolling period
                  .reset_index(level = 0)
                )
        #renames the columns
        col_names = [(value + '_vol_' + str(window_size) + 'rw') for value in values]
        col_names.insert(0, group)
        vol.columns = col_names

        #annualizes the volatility
        col_names.remove(group)
        vol[col_names]= vol[col_names].apply(lambda x : x *((252/returns_frequency)**0.5))

        df2 = df.merge(vol.drop(columns = group),left_index=True,right_index=True)
        return df2
    
    raise Exception("Wrong Parameter: rolling can only be True or False.")
  

def drawdown(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA'])-> pd.DataFrame:
    """Calculates the drawdown (the % the asset is down from its all-time-high) for givens assets.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'.\n
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark prices. Example: ['asset_price', 'index price'].\n
   
    <b>Returns:</b>\n
    pd.DataFrame: The original pandas dataframe with added columns for the all time high and drawdown of the given assets.

   """
    df2 = df.copy(deep = True)
    for value in values:
        col = 'cum_max_'+ value
        df2[col] = df2.groupby([group])[[value]].cummax().to_numpy() 
        df2[('drawdown_'+ value)] = (df2[value]/df2[col])-1
    return df2


def corr_benchmark(df: pd.DataFrame,  asset_returns: str, index_returns: str, group: str = 'CNPJ_FUNDO', rolling: bool = False, window_size: int = 252) -> pd.DataFrame:
    """Calculates the correlation between assets and a given benchmark both in rolling windows or for the full available period.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'.\n
    asset_returns (str): name of the column in the dataframe with the assets returns.\n
    index_returns (str): name of the column in the dataframe with the benchmark returns.\n
    rolling (bool): True or False. Indicates if the function will return total correlation for each asset or rolling window correlations.\n
    window_size: (int): Default = 252. Only useful if rolling = True. Defines the size of the rolling window wich the volatility will be calculated over.\n

    <b>Returns:</b>\n
    pd.DataFrame: If rolling = False: Pandas dataframe with total correlation for the assets and their benchmarks. If rolling = True: The original pandas dataframe with an added column for the correlation in the rolling windows.

   """
    if not rolling: 
        #calculates the correlation between assests returns for the whole period
        corr = df[df[asset_returns].notnull()].groupby([group])[[asset_returns,index_returns]].corr()
        corr = corr.xs(index_returns,level = 1, drop_level=False)
        corr = corr.reset_index(level = 1, drop = True)
        corr = corr.drop(columns=[index_returns])
        corr.columns=['correlation_benchmark']
        return corr
    if rolling:  
        #calculates the correlation between the assests returns across rolling windows     
        corr = (df[df[asset_returns].notnull()].groupby(group)[[asset_returns,index_returns]]
                                              .rolling(window_size)
                                              .corr() 
                                              .xs(index_returns,level = 2, drop_level=True) #drops reduntant level of the corr matrix
                                              .reset_index(level = 0)
                                              .drop(columns=[index_returns])
                                              .rename(columns = {asset_returns:'correlation_benchmark'})
                )
        df2 = df.merge(corr.drop(columns = [group]),left_index=True,right_index=True)
        return df2
    
    raise Exception("Wrong Parameter: rolling can only be True or False") 


def beta(df: pd.DataFrame, asset_vol: str, bench_vol: str, correlation: str = 'correlation_benchmark') -> pd.DataFrame:
    """Calculates the beta (measure of the volatility of an asset compared to the market, usually represented by a index benchmark) of the given assets.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    asset_vol (str): name of the column in the dataframe with the assets volatilities.\n
    bench_vol (str): name of the column in the dataframe with the benchmark volatility.\n
    correlation (str): name of the column in the dataframe with the correlations between assets and their benchmarks.\n

    <b>Returns:</b>\n
    pd.DataFrame: The original pandas dataframe with an added column for the beta calculation.

   """
    df2 = df.copy(deep = True)
    df2['beta'] = (df2[asset_vol] / df2[bench_vol]) * df2[correlation]
    return df2


def alpha(df: pd.DataFrame, asset_returns: str, bench_returns: str, riskfree_returns: str, beta: str) -> pd.DataFrame:
    """Calculates the alpha (measure of the excess of return of an asset compared to the market, usually represented by a index benchmark) of the given assets.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    asset_returns (str): name of the column in the dataframe with the assets returns.\n
    bench_returns (str): name of the column in the dataframe with the benchmark returns.\n
    riskfree_returns (str): name of the column in the dataframe with the risk free rate returns.\n
    beta (str): name of the column in the dataframe with the assets betas.\n

    <b>Returns:</b>\n
    pd.DataFrame: The original pandas dataframe with an added column for the alpha calculation.

   """
    df2 = df.copy(deep = True)
    df2['alpha'] = df2[asset_returns] - df2[riskfree_returns] - (df2[beta] * (df2[bench_returns] - df2[riskfree_returns]))
    return df2


def sharpe(df: pd.DataFrame, asset_returns: str, riskfree_returns: str, asset_vol: str) -> pd.DataFrame:
    """Calculates the sharpe ratio (average return earned in excess of the risk-free rate per unit of volatility) of the given assets.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    asset_returns (str): name of the column in the dataframe with the assets returns.\n
    riskfree_returns (str): name of the column in the dataframe with the risk free rate returns.\n 
    asset_vol (str): name of the column in the dataframe with the assets volatilities.\n

    <b>Returns:</b>\n
    pd.DataFrame: The original pandas dataframe with an added column for the sharpe calculation.

   """

    df2 = df.copy(deep = True)
    df2['sharpe'] = (df2[asset_returns] - df2[riskfree_returns]) / df2[asset_vol]
    return df2


def sortino(df: pd.DataFrame, asset_returns: str, riskfree_returns: str, asset_negative_vol: str) -> pd.DataFrame:
    """Calculates the sortino ratio (average return earned in excess of the risk-free rate per unit of negative volatility) of the given assets.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    asset_returns (str): name of the column in the dataframe with the assets returns.\n
    riskfree_returns (str): name of the column in the dataframe with the risk free rate returns.\n
    asset_negative_vol (str): name of the column in the dataframe with the assets downside volatilities (volatility of only negative returns).\n
    
    <b>Returns:</b>\n
    pd.DataFrame: The original pandas dataframe with an added column for the sortino calculation.

   """
    df2 = df.copy(deep = True)
    df2['sortino'] = (df2[asset_returns] - df2[riskfree_returns]) / df2[asset_negative_vol]
    return df2


def capture_ratio(df: pd.DataFrame, asset_returns: str, bench_returns: str, returns_frequency: int, group: str = 'CNPJ_FUNDO') -> pd.DataFrame:
    """Calculates the capture ratios (measure of assets performance relative to its benchmark in bull and bear markets) of the given assets.\n

    <b>Parameters:</b>\n
    df (pd.DataFrame): Pandas dataframe with the needed data.\n
    asset_returns (str): name of the column in the dataframe with the assets returns.\n
    bench_returns (str): name of the column in the dataframe with the benchmark returns.\n
    returns_frequency: (int): Indicates the frequency in days of the given returns. Should be in tradable days (252 days a year, 21 a month, 5 a week for stocks).\n 
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'.\n
    
    <b>Returns:</b>\n
    pd.DataFrame: The original pandas dataframe with added columns for the capture ratios (bull, bear and ratio bull/bear).\n

   """   

    df_bull = df[(df[asset_returns].notnull()) & (df[bench_returns].notnull())].copy(deep = True)
    df_bear = df[(df[asset_returns].notnull()) & (df[bench_returns].notnull())].copy(deep = True)

    df_bull = df_bull[df_bull[bench_returns] > 0] #dataframe with only positive returns from the benchmark
    df_bear = df_bear[df_bear[bench_returns] <= 0] #dataframe with only negative returns from the benchmark

    tables = [df_bull, df_bear]
    for i, _ in enumerate(tables): #performs set of operations in each table
        #calculates total returns + 1
        compound = tables[i].groupby(group)[[asset_returns,bench_returns]].apply(lambda x: np.prod(1+x))
        
        #counts number of periods
        nperiods = tables[i].groupby(group)[[asset_returns]].count().rename(columns = {asset_returns:'n_periods'})

        tables[i] = compound.merge(nperiods, on = group, how  ='left')#joins tables defined above

        #calculates the annualized returns (CAGR)
        tables[i][asset_returns]=(tables[i][asset_returns]**((252/returns_frequency)/tables[i]['n_periods']))-1
        tables[i][bench_returns]=(tables[i][bench_returns]**((252/returns_frequency)/tables[i]['n_periods']))-1

        tables[i]['capture'] = tables[i][asset_returns]/tables[i][bench_returns] #calculates the capture

    df2 = tables[1].merge(tables[0], on = group, how  ='left',suffixes=('_bear','_bull'))
    df2['capture_ratio'] = df2['capture_bull']/df2['capture_bear']
    return df2