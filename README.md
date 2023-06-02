# Stock Portfolio Web Application

Harvard CS50 Project\
Video Demo:  https://youtu.be/hle4h0g3xOs

## Description:

A stock portfolio web application that allows users to track and manage their stock portfolio. It is a fully functional web application with authentication and authorization thus, users can register, log-in and manage their account credentials with changing password options or adding cash to their funds. It not only allows you to look up real-time stocks’ actual prices and portfolios’ values by fetching from IEX Cloud API but also let you buy or sell stocks and see your portfolio transaction history.

## Tech Stack:

* Python
* Flask
* SQL
* HTML
* CSS
* Bootstrap

## Project Specification:

### Register
The function allows user to register for an account on the web application. It also checks user credentials to register with distinct username and protect privacy of user password by hashing then store in the database.

### Quote
The function allows user to lookup for real-time stocks by retrieving data via IEX Cloud API. It validates the stock symbol before allow user to lookup for stock data.

### Buy
The function allows user to buy stocks with real-time prices by fetching data from IEX Cloud API. It validates the stock symbol and the amount of stock you can buy with your current fund. It executes transaction once it completed then update your stock portfolio, current fund, current total value of your stock portfolio and save it to the database.

### Index
The function displays the homepage contains HTML table summarizing, for the user currently logged in, which stocks the user owns, the numbers of shares owned, the current price of each stock, and the total value of each holding. It also displays the user’s current total stock value, cash balance and a grand total of user stock portfolio.

### Sell
The function allows user to sell stocks with real-time prices by fetching data from IEX Cloud API. It validates the stock symbol and the amount of stock you can sell with your current fund. It executes transaction once it completed then update your stock portfolio, current fund, current total value of your stock portfolio and save it to the database.

### History
The function displays an HTML table summarizing all of a user’s past transactions, listing row by row each and every buy and every sell include the stock’s symbol, the purchase or sale price, the number of shares bought or sold, the total value of purchase or sale and the method of transaction.

### changePassword
The function allows user to change their password. It validates the account credentials and then hash the new password and update to the database.

### addCash
The function allows user to add cash to their funds. It validates amount of cash user want to add then updates the current fund of user in the database.

## How to run

1. Clone this project
2. Register for IEX Cloud API
3. Execute in the terminal: export API_KEY=value where value is the API key from IEX Cloud
4. Run Flask within the directory/folder with command: flask run

