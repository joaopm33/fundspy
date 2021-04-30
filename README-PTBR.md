# fundspy
### [Read in English/Leia em Inglês](README.md)

Esse projeto baseado em python te permite extrair e analisar dados relacionados a fundos de investimento brasileiros. 
O projeto possui funções para iniciar e atualizar um banco de dados SQLite com informações cadastrais e cotas diárias de todos os fundos de investimento disponíveis na CVM (desde 2005), assim como dados relacionados ao índice ibovespa e a taxa selic.
Também existem funções para calcular métricas de performance importantes para a análise quantitativa dos fundos, como retornos, volatilidade, correlação com índices, beta, alpha, sharpe ratio, sortino ratio e capture ratios.


## Documentação e Exemplos
* Você pode acessar a documentação das funções [aqui](https://joaopm33.github.io/fundspy/docs/fundspy.html).
* Também existe um Notebook com exemplos de uso de todas as funções de cálculo de métricas de performance [aqui](https://jovian.ai/joaopm33/fundspy-example-notebook).


## Comece Aqui
Você precisará do python na versão 3.5 ou superior para utilizar este projeto. Para começar, primeiramente clone este repositório para seu computador. 

### Instalação

Para instalar as bibliotecas necessárias, abra o seu terminal, navegue até o diretório onde seus arquivos foram baixados e execute o seguinte comando:

```
pip install -r requirements.txt
```

Agora você está pronto para começar a usar as funções.


## Principais Funcionalidades

Os principais usos desse projeto estão relacionados a iniciar um banco de dados de fundos, atualizá-lo e calcular métricas de performance com funções pré construidas.


### Construindo o banco de dados

Construir o banco de dados é fácil: basta executar o arquivo "start_db.py" no diretório do projeto a partir do seu terminal:

```
python start_db.py
```

Será criado um banco de dados SQLite em seu diretório com ~6Gb, então tenha certeza de possuir espaço livre suficiente.

Você também pode abrir o arquivo "start_db.py" em um editor de texto e alterar os parametros da função start_db. Para extrair um recorte menor dos dados disponíveis, use os parâmetros:

* ```start_year``` para definir o ano inicial da coleta de dados. 
* ```target_funds``` para definir uma lista de CNPJs de fundos alvo para a extração.

Isso poderá lhe salvar muito espaço de disco, embora diminua a quantidade de dados extraidos.

```
start_db(db_dir = 'investments_database.db', 
         start_year = 2005, 
         target_funds = [])
```

### Atualizando o banco de dados

Uma vez que você queria extrair novos dados e atualizar a sua base, execute o arquivo "update_db.py" no diretório do projeto a partir do seu terminal:

```
python update_db.py
```
Essa função coletará os dados disponíveis entre a última atualização e a data atual. Caso você tenha definido um recorte de fundos específicos no parâmetro ```target_funds = []``` quando iniciou a base de dados, a atualização também se limitará a esse subset.

**Obs:** Caso você tenha alterado o parâmetro padrão ```db_dir = r'investments_database.db'``` ao iniciar o banco de dados, lembre-se de alterá-lo também não função de atualização.

### Calculando métricas de performance para os fundos de invesimento
This package contains pre-built performance metrics for investment funds analysis:
* ```returns``` function - Calcula o % de retorno para os ativos tanto em janelas móveis ou para o período total disponível (calculando também o [CAGR](https://www.investopedia.com/terms/c/cagr.asp) nessa última opção).
* ```cum_returns``` function - Calcula o [retorno cumulativo](https://www.investopedia.com/terms/c/cumulativereturn.asp) para os ativos.
* ```drawdown``` function - Calcula o [drawdown](https://www.investopedia.com/terms/d/drawdown.asp) (% em que o ativo está abaixo do seu pico máximo) para os ativos.
* ```volatility``` function - Calcula a [volatilidade anualizada](https://www.investopedia.com/terms/v/volatility.asp) (desvio padrão dos retornos com grau de liberdade = 0) para os ativos tanto em janelas móveis quanto no período completo disponível.
* ```corr_benchmark``` function - Calcula a [correlação](https://www.investopedia.com/terms/c/correlationcoefficient.asp) entre os ativos e um benchmark escolhido em janelas móveis ou no período completo disponível.
* ```beta``` function - Calcula o [beta](https://www.investopedia.com/terms/b/beta.asp) (medida da volatilidade do ativo em relação ao mercado) para os ativos.
* ```alpha``` function - Calcula o [alpha](https://www.investopedia.com/terms/a/alpha.asp) (medida do excesso de retorno do ativo em relação ao mercado como um todo) para os ativos.
* ```sharpe``` function - Calcula o [sharpe ratio](https://www.investopedia.com/terms/s/sharperatio.asp) (retorno médio em excesso à taxa livre de risco por unidade de volatilidade) para os ativos.
* ```sortino``` function - Calcula o [sortino ratio](https://www.investopedia.com/terms/s/sortinoratio.asp) (retorno médio em excesso à taxa livre de risco por unidade de volatilidade negativa) para os ativos.
* ```capture_ratio``` function - Calcula o [capture ratios](https://cleartax.in/s/capture-ratio) (medida da performance dos ativos comparada ao benchmark em mercados de alta e baixa) para os ativos.


## Autores

* **Joao Monteiro** - [LinkedIn](https://www.linkedin.com/in/joao-penido-monteiro/)


## License

Esse projeto tem a licença MIT License - veja o arquivo [LICENSE.md](LICENSE.md) para mais detalhes
