# CS50 Finance

![Demo image](https://raw.githubusercontent.com/LaurenceZanotti/cs50-finance/assets/cs50finance-mockup.png)

CS50 Finance allows you to quote, buy and sell stocks. Start with $10,000 and try to earn profit! (It's a simulation of course) You can also view the stock prices in real time and the account history.

More information about the project can be found at [CS50 specifications](https://cs50.harvard.edu/x/2022/psets/9/finance/).

See the project live at https://pacific-dawn-05944.herokuapp.com/

This project is my submission for the Problem Set 9 of CS50 Introduction to Computer Science course from Harvard, which I took at 2020.

## Installation

Create and activate virtual environment

    python -m venv venv
    source venv/bin/activate

Go to https://iexcloud.io/cloud-login#/register/ and create an account.

Get an API key at https://iexcloud.io/console/tokens. **(Don't forget to activate sandbox mode before copying the API key)**

    pip install -r requirements.txt
    export FLASK_APP=application
    export API_KEY=<your_iex_exchange_api_key>

Finally, run the app

    flask run

Create an account and log in with it. Now you can quote, buy and sell stocks.