# fundspy

[![Version](https://img.shields.io/pypi/v/fundspy)]() [![CodeFactor](https://www.codefactor.io/repository/github/joaopm33/fundspy/badge/master)](https://www.codefactor.io/repository/github/joaopm33/fundspy/overview/master) [![Status](https://img.shields.io/pypi/status/fundspy)]()  [![License](https://img.shields.io/github/license/joaopm33/fundspy)]() [![Repo size](https://img.shields.io/github/repo-size/joaopm33/fundspy)]()   [![Stars](https://img.shields.io/github/stars/joaopm33/fundspy)]()  [![Issues](https://img.shields.io/github/issues/joaopm33/fundspy)]() [![Last commit](https://img.shields.io/github/last-commit/joaopm33/fundspy)]() 

### [Read in Portuguese / Leia em Portugues](https://github.com/joaopm33/fundspy/blob/master/README-PTBR.md)

This python based project helps you to extract and analyze data related to brazilian investment funds. 
It has functions to start and update a SQLite database containing cadastral information and daily quotas of all investment funds in brazil since 2005, as well as the ibovespa index and selic (the base interest rate of the brazilian economy).

There are also functions to help you calculate important performance metrics for the investment funds, such as returns, volatility, correlation with indexes, beta, alpha, sharpe ratio, sortino ratio and capture ratios.


## Documentation and Examples
* You can access the functions documentation [here](https://joaopm33.github.io/fundspy/docs/fundspy.html).
* Theres also a Notebook with use examples of all performance metrics functions [here](https://jovian.ai/joaopm33/fundspy-example-notebook).


## Getting Started
You will need python 3.5 (at least) for running this project. 

### Installing
To install the package, open a terminal and execute the command:

```
pip install fundspy
```


## Main Functionalities

The main use cases this library covers are starting a investment funds database, updating it and calculating performance metrics with pre built functions.

### Building the database

To start the database you will have to execute the "start_db" function. You can do this by creating a file "start_db.py" in your local directory and pasting the following code inside it (or just download it [here](https://github.com/joaopm33/fundspy/blob/master/example_scripts/start_db.py)):

```
from fundspy.fundspy import cvm_informes, start_db
start_db(db_dir = 'investments_database.db', start_year = 2005, target_funds = [])
```

and then executing the file from your terminal:

```
python start_db.py
```

This will create a ~6Gb SQLite database in your disk named "investments_database.db", so be sure to have enough free space. 

You can also change the start_db function parameters. To get a smaller subset of the available data, use the parameters: 

* ```start_year``` to set the minimal year used as filter. 
* ```target_funds``` to pass a list of target funds CNPJs (unique ids).

This can save you a lot of disk space, but will of course reduce the amount of data you get.

```
start_db(db_dir = 'investments_database.db', 
         start_year = 2005, 
         target_funds = [])
```

### Updating the database

Once you want to extract new data and update your database, create a file "update_db.py" in your local directory and paste the following code inside it (or just download it [here](https://github.com/joaopm33/fundspy/blob/master/example_scripts/update_db.py)):

```
from fundspy.fundspy import cvm_informes, update_db
update_db(db_dir = r'investments_database.db')
```

run the "update_db.py" file from your terminal:
```
python update_db.py
```

This function will collect the data available between the last database update and the current date. If you defined a subset of target funds in the ```target_funds = []``` parameter when starting the databased, it will also be considered when updating the database. 

**Obs:** If you changed the default ```db_dir = r'investments_database.db'``` parameter when starting the database, make sure to add it to the "update_db" function as well.

### Calculating performance metrics for the investment funds
This package contains pre-built performance metrics for investment funds analysis:
* ```returns``` function - Calculates the % returns for the given assets both in rolling windows or for the full available period (you also get the [CAGR](https://www.investopedia.com/terms/c/cagr.asp) in this option).
* ```cum_returns``` function - Calculates the [cumulative % returns](https://www.investopedia.com/terms/c/cumulativereturn.asp) for the given assets.
* ```drawdown``` function - Calculates the [drawdown](https://www.investopedia.com/terms/d/drawdown.asp) (the % the asset is down from its all-time-high) for the givens assets.
* ```volatility``` function - Calculates the [annualized volatillity](https://www.investopedia.com/terms/v/volatility.asp) (standard deviation of returns with degree of freedom = 0) for givens assets returns both in rolling windows or for the full available period.
* ```corr_benchmark``` function - Calculates the [correlation](https://www.investopedia.com/terms/c/correlationcoefficient.asp) between assets and a given benchmark both in rolling windows or for the full available period.
* ```beta``` function - Calculates the [beta](https://www.investopedia.com/terms/b/beta.asp) (measure of the volatility of an asset compared to the market, usually represented by an index benchmark) for the given assets.
* ```alpha``` function - Calculates the [alpha](https://www.investopedia.com/terms/a/alpha.asp) (measure of the excess of return of an asset compared to the market, usually represented by an index benchmark) for the given assets.
* ```sharpe``` function - Calculates the [sharpe ratio](https://www.investopedia.com/terms/s/sharperatio.asp) (average return earned in excess of the risk-free rate per unit of volatility) for the given assets.
* ```sortino``` function - Calculates the [sortino ratio](https://www.investopedia.com/terms/s/sortinoratio.asp) (average return earned in excess of the risk-free rate per unit of negative volatility) for the given assets.
* ```capture_ratio``` function - Calculates the [capture ratios](https://cleartax.in/s/capture-ratio) (measure of assets performance relative to its benchmark in bull and bear markets windows) for the given assets.


## Authors

* **Joao Monteiro** - [LinkedIn](https://www.linkedin.com/in/joao-penido-monteiro/)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
