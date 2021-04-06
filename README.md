# funds_py

This python based project helps you to extract and analyze data related to brazilian investment funds. 
It has functions to start and update a SQLite database containing cadastral information and daily quotas of all investment funds in brazil since 2005, as well as the ibovespa index and selic (the base interest rate of the brazilian economy).
There are also functions to help you calculate importante performance metrics for the investment funds, such as returns, volatility, correlation with indexes, beta, alpha, sharpe ratio, sortino ratio and capture ratios.


## Getting Started
You will need python 3.5 (at least) for running this project. To start, first clone this repository to your local machine.

### Installing

Now is the time to install the needed libraries in the "requirements.txt" file.  Navigate to the package directory and then run in your command line:

```
pip install -r requirements.txt
```

Now you are all set up to start using the package.


## Main Functionalities

The main use cases this library covers are starting a investment funds database, updating it and calculatin performance metrics with pre built functions.

### Starting the database

Starting the database is pretty easy: execute the file "start_db.py" in the project directory:

```
python start_db.py
```

This will create a ~6Gb SQLite database in your disk named "investments_database.db", so be sure to have enough free space. 

You can also open the "start_db.py" file in a text editor to change the start_db function parameters. To get a smaller subset of the available data, use the parameters: 

* ```start_year``` to set the minimal year used as filter 
* ```target_funds``` to pass a list of target funds CNPJs (unique ids) 

This can save you a lot of disk space, but will of course reduce the amount of data you get.

```
start_db(db_dir = 'investments_database.db', 
         start_year = 2005, 
         target_funds = [])
```

### Updating the database

Once you want to extract new data and update your database, run the "update_db.py" file in the project directory:

```
python update_db.py
```
This function will collect the data available between the last database update and the current system date. If you defined a subset of target funds in the ```target_funds = []``` parameter when starting the databased, they will also be considered when updating the database. 

**Obs:** If you changed the default ```db_dir = r'investments_database.db'``` parameter when starting the database, make sure to add it to the update script.

### Calculating performance metrics for the investment funds
This package contains pre-built performance metrics for investment funds analysis:
* ```returns``` function - Calculates the % returns for the given assets both in rolling windows or for the full available period (you also get the [CAGR](https://www.investopedia.com/terms/c/cagr.asp) in this option)
* ```cum_returns``` function - Calculates the [cumulative % returns](https://www.investopedia.com/terms/c/cumulativereturn.asp) for the given assets
* ```drawdown``` function - [Calculates the drawdown](https://www.investopedia.com/terms/d/drawdown.asp) (the % the asset is down from its all-time-high) for givens assets
* ```volatility``` function - Calculates the [annualized volatillity](https://www.investopedia.com/terms/v/volatility.asp) (standard deviation of returns with degree of freedom = 0) for givens assets returns both in rolling windows or for the full available period
* ```corr_benchmark``` function - Calculates the [correlation](https://www.investopedia.com/terms/c/correlationcoefficient.asp) between assets and a given benchmark both in rolling windows or for the full available period
* ```beta``` function - Calculates the [beta](https://www.investopedia.com/terms/b/beta.asp) (measure of the volatility of an asset compared to the market, usually represented by a index benchmark) of the given assets
* ```alpha``` function - Calculates the [alpha](https://www.investopedia.com/terms/a/alpha.asp) (measure of the excess of return of an asset compared to the market, usually represented by a index benchmark) of the given assets
* ```sharpe``` function - Calculates the [sharpe ratio](https://www.investopedia.com/terms/s/sharperatio.asp) (average return earned in excess of the risk-free rate per unit of volatility) of the given assets
* ```sortino``` function - Calculates the [sortino ratio](https://www.investopedia.com/terms/s/sortinoratio.asp) (average return earned in excess of the risk-free rate per unit of negative volatility) of the given assets
* ```capture_ratio``` function - Calculates the [capture ratios](https://cleartax.in/s/capture-ratio) (measure of assets performance relative to its benchmark in bull and bear markets) of the given assets.


## Authors

* **Joao Monteiro** - [LinkedIn](https://www.linkedin.com/in/joao-penido-monteiro/)


## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
