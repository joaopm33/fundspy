"""
Module with functions to analyze funds (mutual funds, hedge funds, etc)

Main functions: 
Extracts repports regarding brazilian funds from CVM
Starts a new SQLite database with tables for daily prices and cadastral information of brazillian funds, the ibovespa index and selic rates
Updates the SQLite database tables
Calculates evaluation metrics for the investment funds in an efortless, one line command way (returns, volatility, correlation, beta, alpha, sharpe ratio, sortino ratio, capture ratios)

Author: Joao Penido Monteiro
Github: github.com/joaopm33
Linkedin: linkedin.com/in/joao-penido-monteiro/
"""

#modules from the python standard library
import os, os.path
import zipfile
import datetime
import sqlite3

#packages used to download data from the internet
import requests
import investpy

#packages used to manipulate data
import pandas as pd
import numpy as np

#other packages
from tqdm import tqdm

def cvm_informes (year: int, mth: int) -> pd.DataFrame:
    """Downloads the daily report (informe diario) from CVM for a given month and year. 

    Parameters:
    year (int): The year of the report the function should download
    mth (int): The month of the report the function should download

    Returns:
    pd.DataFrame: Pandas dataframe with the report for the given month and year. If the year is previous to 2017, will contain data regarding the whole year.

   """

    if int(year) >= 2017: #utiliza a estrutura de download para dados a partir de 2017
        try:
            mth = f"{mth:02d}"
            year = str(year)
            #criamos a url a partis dos parametros passados para a funcao
            url = 'http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_'+year+mth+'.csv'
            
            #lemos o arquivo csv retornado pelo link
            cotas = pd.read_csv(url, sep =';')
            cotas['DT_COMPTC'] = pd.to_datetime(cotas['DT_COMPTC']) #define tipo datetime para coluna de data
            
            try:
                #remove coluna que aparece apenas em certos arquivos para evitar inconsistencias
                cotas.drop(columns = ['TP_FUNDO'], inplace = True)
            except:
                pass
            
            return cotas
        except:
            print('nao ha arquivo para os parametros passados.')
    
    if int(year) < 2017:
        try:
            year = str(year)

            url = 'http://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/HIST/inf_diario_fi_' + year + '.zip'
            #envia requests para a url
            r = requests.get(url, stream=True, verify=False, allow_redirects=True)
            
            with open('informe' + year + '.zip', 'wb') as fd: #salva arquivo .zip
                fd.write(r.content)

            zip_inf = zipfile.ZipFile('informe' + year + '.zip') #abre arquivo .zip
            
            #le os arquivos csv dentro do arquivo zip
            informes = [pd.read_csv(zip_inf.open(f), sep=";") for f in zip_inf.namelist()] 
            cotas = pd.concat(informes,ignore_index=True)
            
            cotas['DT_COMPTC'] = pd.to_datetime(cotas['DT_COMPTC']) #define tipo datetime para coluna de data

            zip_inf.close() #fecha o arquivo zip
            os.remove('informe' + year + '.zip') #apaga o arquivo zip
            
            return cotas
        
        except Exception as E:
            print(E)           

def start_database(db_dir = r'investments_database.db'):
    #STEP 1:
    #starts the new database
    con = sqlite3.connect(db_dir)


    #STEP 2:
    #downloads each report in the cvm website and pushes it to the sql database daily_quotas table
    
    #for each year between 2017 and now
    for year in tqdm(range(2005, datetime.date.today().year + 1), position = 0, leave=True): 
        for mth in range(1, 13): #for each month

            #loop structure for years equal or after 2017
            if year>=2017: 
                informe = cvm_informes(str(year), mth)
                #informe = informe[informe.CNPJ_FUNDO.isin(fundos.CNPJ_FUNDO)]
                try:
                    #appends information to the sql database
                    informe.to_sql('cotas_diarias', con , if_exists = 'append', index=False)
                except:
                    pass
            
            else: #loop structure to handle years before 2017 (they have a different file structure)
                #only executes the download function once every year to avoid duplicates (unique file for each year)       
                if mth == 12:
                    informe = cvm_informes(str(year), mth)
                    try:
                        #appends information to the sql database
                        informe.to_sql('cotas_diarias', con , if_exists = 'append', index=False)
                    except:
                        pass


    #STEP 3:                    
    #creates index in the daily_quotas table to make future select queries faster. 
    #tradeoff: The updating proceesses of the database will be slower.
    index = '''
    CREATE INDEX "cnpj_date" ON "cotas_diarias" (
        "CNPJ_FUNDO" ASC,
        "DT_COMPTC" ASC
    )'''

    cursor = con.cursor()
    cursor.execute(index)
    con.commit()

    cursor.close()

    
    #STEP 4:
    #downloads cadastral information from CVM of the fundos and pushes it to the database
    info_cad = pd.read_csv('http://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv', sep = ';', encoding='latin1')
    info_cad.to_sql('info_cadastral_fundos', con, index=False)


    #STEP 5:
    #downloads daily ibovespa prices from investing.com and pushes it to the database
    ibov = investpy.get_etf_historical_data(etf='Ishares Ibovespa', 
                                        country='brazil',
                                        from_date='01/01/2005',
                                        to_date=datetime.date.today().strftime('%d/%m/%Y'))
    ibov.to_sql('ibov_returns', con, index=True) 


    #STEP 6:
    #downloads daily selic returns (basic interest rate of the brazilian economy) 
    #from the brazillian central bank and pushes it to the database
    selic = pd.read_json('http://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json'.format(11))
    selic['data'] = pd.to_datetime(selic['data'], format = '%d/%m/%Y')
    selic['valor'] = selic['valor']/100 #calculates decimal rate from the percentual value

    selic.rename(columns = {'data':'date', 'valor':'value'}, inplace = True)
    selic.to_sql('selic_rates', con , index=False)  


    #STEP 7:
    #creates a table with a log of the execution timestamps of the script
    update_log = pd.DataFrame({'date':[datetime.datetime.now()], 'log':[1]})
    update_log.to_sql('update_log', con, if_exists = 'append', index=False)


    #STEP 8
    #closes the connection with the database
    con.close()


def returns(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA'], rolling: bool = False, window_size: int = 1) -> pd.DataFrame:
    """Calculates the % returns for the given assets

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed columns
    group (str): name of the column in the dataframe used to group values (example: 'stock_ticker' or 'fund_code')
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark prices (Example: ['asset_price', 'index price'])
    rolling (bool): True or False. Indicates if the function will return total returns for each asset or rolling window returns
    window_size: (int): Default = 1. Only useful if rolling = True. Defines the size of the rolling window wich the returns will be calculated over.

    Returns:
    pd.DataFrame: If rolling = True: Pandas dataframe with total % returns for the assets. If rolling = False: The original pandas dataframe with added columns for the % returns in the rolling windows.

   """
    if rolling == True:
        window_size = 1

    #calculates the percentual change in the rolling windows specified for each group
    returns = df.groupby(group, sort = False, as_index = True)[values].apply(lambda x: x.pct_change(window_size))
    
    #renames the columns
    col_names = [(value + '_return_' + str(window_size) + 'd') for value in values]
    returns.columns = col_names

    #if the parameter rolling = False, returns the original data with the added rolling returns
    if rolling == False:
        df2 = df.merge(returns, how='left', left_index=True, right_index=True)
        return df2

    #if the parameter rolling = True, returns the total compound returns in the period, the number of days
    # and the Compound Annual Growth Rate (CAGR)
    elif rolling == True: 
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
        returns[col_names] = (returns.loc[:,values]
                                           .apply(lambda x: ((x + 1)**(252/returns.days))-1))

        return returns                                   

    else: 
        raise Exception("Wrong Parameter: rolling can only be True or False.") 
        

def cum_returns(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA']) -> pd.DataFrame:
    """Calculates the cumulative % returns for the given assets

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed columns
    group (str): name of the column in the dataframe used to group values (example: 'stock_ticker' or 'fund_code')
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark prices (Example: ['asset_price', 'index price'])
   
    Returns:
    pd.DataFrame: A pandas dataframe with the cumulative % returns for each asset.

   """

    cum_returns = returns(df, group = group, values = values) #calculates  the daily returns
    
    #calculates the cumulative returns in each day for each group
    cum_returns = cum_returns.groupby(group)[[value + '_return_1d' for value in values]].expanding().apply(lambda x: np.prod(x+1)-1)
    
    #renames the columns
    cum_returns.columns = [i + '_cum_return' for i in values]
    cum_returns.reset_index(level = 0, inplace = True)

    cum_returns = df.merge(cum_returns, on = group)
    return cum_returns


def volatility(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA'], rolling: bool = False ,returns_frequency: int = 1, window_size: int = 252) -> pd.DataFrame:
    """Returns the annualized volatillity (standard deviation of returns with degree of freedom = 0) for givens assets.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark prices. Example: ['asset_price', 'index price']. 
    rolling (bool): True or False. Indicates if the function will return total volatility for each asset or rolling window volatility
    returns frequency: (int): Default = 1. Indicates the frequency in days of the given returns. Should be in tradable days (252 days a year, 21 a month, 5 a week for stocks). This number is used to anualize the volatility.
    window_size: (int): Default = 252. Only useful if rolling = True. Defines the size of the rolling window wich the volatility will be calculated over.

    Returns:
    pd.DataFrame: If rolling = False: Pandas dataframe with total volatility for the assets. If rolling = True: The original pandas dataframe with added columns for the volatility in the rolling windows.

   """
    #Returns 
    if rolling == False:
        vol = df.groupby(group)[values].std(ddof=0) 
        
        #renames the columns
        col_names = [(value + '_vol') for value in values]        
        vol.columns = col_names

        #annualizes the volatility
        vol[col_names]= vol[col_names].apply(lambda x : x *((252/returns_frequency)**0.5))
        
        return vol

    elif rolling == True:    
        vol = (df.groupby(group, sort=False)[values].rolling(window_size).std(ddof=0) #standars deviation in the rolling period
                .reset_index()
                .drop(columns=['level_1'])
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
    
    else: 
        raise Exception("Wrong Parameter: rolling can only be True or False.")
  

def drawdown(df: pd.DataFrame, group: str = 'CNPJ_FUNDO', values: list = ['VL_QUOTA'])-> pd.DataFrame:
    """Returns the drawdown (the % the asset is down from its all-time-high) for givens assets.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'
    values (list): names of the columns in the dataframe wich contains the asset and its benchmark prices. Example: ['asset_price', 'index price']. 
   
    Returns:
    pd.DataFrame: The original pandas dataframe with added columns for the all time high and drawdown of the given assets.

   """
    df2 = df.copy(deep = True)
    for value in values:
        df2[('cum_max_'+ value)] = df2.groupby([group],sort=False,as_index=False)[value].expanding(min_periods = 1).max().to_numpy() 
        df2[('drawdown_'+ value)] = (df2[value]/df2[('cum_max_'+ value)])-1
    return df2


def corr_benchmark(df: pd.DataFrame,  asset_returns: str, index_returns: str, group: str = 'CNPJ_FUNDO', rolling: bool = False, window_size: int = 252) -> pd.DataFrame:
    """Returns the correlation between an asset and its benchmark.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'
    asset_returns (str): name of the column in the dataframe with the assets returns. 
    index_returns (str): name of the column in the dataframe with the benchmark returns.
    rolling (bool): True or False. Indicates if the function will return total correlation for each asset or rolling window correlations
    window_size: (int): Default = 252. Only useful if rolling = True. Defines the size of the rolling window wich the volatility will be calculated over.

    Returns:
    pd.DataFrame: If rolling = False: Pandas dataframe with total correlation for the assets and their benchmarks. If rolling = True: The original pandas dataframe with an added column for the correlation in the rolling windows.

   """
    if rolling == False: 
        #calculates the correlation between assests returns for the whole period
        corr = df.groupby([group])[[asset_returns,index_returns]].corr()
        corr = corr.xs(index_returns,level = 1, drop_level=False)
        corr = corr.reset_index(level = 1, drop = True)
        corr = corr.drop(columns=[index_returns])
        corr.columns=['correlation_benchmark']
        #df2 = df.merge(corr, left_on = group, right_index = True)
        return corr
    elif rolling == True:  
        #calculates the correlation between the assests returns across rolling windows     
        corr = (df.groupby(group, sort=False)[[asset_returns,index_returns]].rolling(window_size).corr() 
                  .xs(index_returns,level = 2, drop_level=True) #drops reduntant level of the corr matrix
                  .reset_index()
                  .drop(columns=[index_returns, 'level_1'])
                  .rename(columns = {asset_returns:'correl'})
                )
        df2 = df.merge(corr.drop(columns = [group]),left_index=True,right_index=True)
        return df2
    else:
        raise Exception("Wrong Parameter: rolling can only be True or False") 


def beta(df: pd.DataFrame, asset_vol: str, bench_vol: str, correlation: str) -> pd.DataFrame:
    """Returns the beta (measure of the volatility of an asset compared to the market, usually represented by a index benchmark) of the given assets.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    asset_vol (str): name of the column in the dataframe with the assets volatilities
    bench_vol (str): name of the column in the dataframe with the benchmark volatility
    correlation (str): name of the column in the dataframe with the correlations between assets and their benchmarks

    Returns:
    pd.DataFrame: The original pandas dataframe with an added column for the beta calculation.

   """
    df2 = df.copy(deep = True)
    df2['beta'] = (df2[asset_vol] / df2[bench_vol]) * df2[correlation]
    return df2


def alpha(df: pd.DataFrame, asset_returns: str, bench_returns: str, riskfree_returns: str, beta: str) -> pd.DataFrame:
    """Returns the alpha (measure of the excess of return of an asset compared to the market, usually represented by a index benchmark) of the given assets.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    asset_returns (str): name of the column in the dataframe with the assets returns
    bench_returns (str): name of the column in the dataframe with the benchmark returns
    riskfree_returns (str): name of the column in the dataframe with the risk free rate returns 
    beta (str): name of the column in the dataframe with the assets betas

    Returns:
    pd.DataFrame: The original pandas dataframe with an added column for the beta calculation.

   """
    df2 = df.copy(deep = True)
    df2['alpha'] = df2[asset_returns] - df2[riskfree_returns] - (df2[beta] * (df2[bench_returns] - df2[riskfree_returns]))
    return df2


def sharpe(df: pd.DataFrame, asset_returns: str, riskfree_returns: str, asset_vol: str) -> pd.DataFrame:
    """Returns the sharpe ratio (average return earned in excess of the risk-free rate per unit of volatility) of the given assets.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    asset_returns (str): name of the column in the dataframe with the assets returns
    riskfree_returns (str): name of the column in the dataframe with the risk free rate returns 
    asset_vol (str): name of the column in the dataframe with the assets volatilities

    Returns:
    pd.DataFrame: The original pandas dataframe with an added column for the beta calculation.

   """

    df2 = df.copy(deep = True)
    df2['sharpe'] = (df2[asset_returns] - df2[riskfree_returns]) / df2[asset_vol]


def sortino(df: pd.DataFrame, asset_returns: str, riskfree_returns: str, asset_negative_vol: str) -> pd.DataFrame:
    """Returns the sortino ratio (average return earned in excess of the risk-free rate per unit of negative volatility) of the given assets.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    asset_returns (str): name of the column in the dataframe with the assets returns
    riskfree_returns (str): name of the column in the dataframe with the risk free rate returns
    asset_negative_vol (str): name of the column in the dataframe with the assets downside volatilities (volatility of only negative returns)
    
    Returns:
    pd.DataFrame: The original pandas dataframe with an added column for the beta calculation.

   """
    df2 = df.copy(deep = True)
    df2['sortino'] = (df2[asset_returns] - df2[riskfree_returns]) / df2[asset_negative_vol]
    return sortino


def capture_ratio(df: pd.DataFrame, asset_returns: str, bench_returns: str, group: str = 'CNPJ_FUNDO') -> pd.DataFrame:
    """Returns the capture ratios (measure of assets performance relative to its benchmark in bull and bear markets) of the given assets.

    Parameters:
    df (pd.DataFrame): Pandas dataframe with the needed data
    asset_returns (str): name of the column in the dataframe with the assets returns
    bench_returns (str): name of the column in the dataframe with the benchmark returns
    group (str): name of the column in the dataframe used to group values. Example: 'stock_ticker' or 'fund_code'
    
    Returns:
    pd.DataFrame: The original pandas dataframe with added columns for the capture ratios (bull, bear and total).

   """   

    #df2 = df2[(df2[asset_returns].notnull()) & (df2[bench_returns].notnull())]

    df_bull = df.copy(deep = True)
    df_bear = df.copy(deep = True)

    df_bull = df_bull[df_bull[bench_returns] > 0] #dataframe with only positive returns from the benchmark
    df_bear = df_bear[df_bear[bench_returns] <= 0] #dataframe with only negative returns from the benchmark

    tables = [df_bull, df_bear]
    for i in range(len(tables)): #performs set of operations in each table
        #adds 1 to the returns
        tables[i][asset_returns] = tables[i][asset_returns]+1
        tables[i][bench_returns] = tables[i][bench_returns]+1

        compound = tables[i].groupby(group)[[asset_returns,bench_returns]].prod() #calculates compound returns + 1

        #counts number of periods
        nperiods = tables[i].groupby(group)[[asset_returns]].count().rename(columns = {asset_returns:'n_periods'})

        tables[i] = compound.merge(nperiods, on = group, how  ='left')#joins tables defined above

        #calculates the annualized returns (CAGR)
        tables[i][asset_returns]=(tables[i][asset_returns]**(1/tables[i]['n_periods']))-1
        tables[i][bench_returns]=(tables[i][bench_returns]**(1/tables[i]['n_periods']))-1

        tables[i]['capture'] = tables[i][asset_returns]/tables[i][bench_returns] #calculates the capture

    df2 = tables[1].merge(tables[0], on = group, how  ='left',suffixes=('_bear','_bull'))
    df2['capture_ratio'] = df2['capture_bull']/df2['capture_bear']
    return df2

