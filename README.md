# Icarus
“Never regret thy fall,
 Icarus of the fearless flight
For the greatest tragedy of them all
Is never to feel the burning light." -Oscar Wilde

## Functions
### Monitors Tokens
Subscribes to new tokens created on pump.fun using Websocket connections.
Listens for messages containing token data and extracts tokens (mint) based on market cap.
Stores up to 20 tokens (mint) with a market cap of less than 45 sol in a list (coins[0]) also with timestamps for how often the tokens are traded(coins[1]).
### Filters the list of tokens
If the list is full and the coins in the list have not been traded for at least 3 minutes, the bot replaces the oldest coin by removing it from the list
### Executes trades
Executes a buy trade for tokens that meet the condition of having a market cap between 35 and 60 sol.
Executes a sell trade for tokens for conditions to be discussed.
2 sell parameters, one for TP and one for SL.
Sends a POST request to "https://pumpportal.fun/api/trade-local" to initiate the trade.
Signs and sends the transaction to the Solana blockchain using the solders library for Solana transactions.
Posts the transaction payload to the Solana RPC endpoint for execution.
Verifies if the transaction was successful and prints the transaction link (e.g., via https://solscan.io/tx/).
