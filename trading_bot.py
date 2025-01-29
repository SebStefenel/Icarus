import asyncio
import websockets
import json
import time
import requests
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solders.commitment_config import CommitmentLevel
from solders.rpc.requests import SendVersionedTransaction
from solders.rpc.config import RpcSendTransactionConfig

coins = [[], []]
coins_populated_event = asyncio.Event()

def record_trade_time(mint):
    if mint in coins[0]:
        index = coins[0].index(mint)
        coins[1][index] = time.time()  # Update the trade time
    else:
        pass

def extract_mint(message):
    current_time = time.time()
    if 'marketCapSol' in message and message['marketCapSol'] < 45:
        if len(coins[0]) <= 20:
            coins[0].append(message['mint'])
            coins[1].append(current_time)
            coins_populated_event.set()
            print(message['mint'])
        elif all(current_time - trade_time >= 180 for trade_time in coins[1]):
            oldest_trade_index = coins[1].index(min(coins[1]))
            coins[0].pop(oldest_trade_index)
            coins[1].pop(oldest_trade_index)
        else:
            pass
    else:
        print("Market cap too high")

async def execute_trade(mint):
    print(f"Attempting to trade for mint: {mint}")
    public_key = "your_public_key"
    private_key = "your_private_key"
    rpc_endpoint = "https://api.mainnet-beta.solana.com"

    try:
        trade_response = requests.post(
            url="https://pumpportal.fun/api/trade-local",
            data={
                "publicKey": public_key,
                "action": "buy",
                "mint": mint,
                "amount": 100000,
                "denominatedInSol": "false",
                "slippage": 10,
                "priorityFee": 0.005,
                "pool": "pump"
            }
        )
        trade_response.raise_for_status()

        keypair = Keypair.from_base58_string(private_key)
        tx = VersionedTransaction(VersionedTransaction.from_bytes(trade_response.content).message, [keypair])
        commitment = CommitmentLevel.Confirmed
        config = RpcSendTransactionConfig(preflight_commitment=commitment)

        tx_payload = SendVersionedTransaction(tx, config)
        rpc_response = requests.post(
            url=rpc_endpoint,
            headers={"Content-Type": "application/json"},
            data=tx_payload.to_json()
        )

        if rpc_response.status_code == 200 and 'result' in rpc_response.json():
            tx_signature = rpc_response.json()['result']
            print(f"Transaction successful: https://solscan.io/tx/{tx_signature}")
        else:
            print(f"RPC error: {rpc_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error executing trade: {e}")

async def execute_sell(mint):
    """
    Executes a sell trade for the specified mint.
    """
    print(f"Attempting to sell for mint: {mint}")
    public_key = "your_public_key"
    private_key = "your_private_key"
    rpc_endpoint = "https://api.mainnet-beta.solana.com"

    try:
        sell_response = requests.post(
            url="https://pumpportal.fun/api/trade-local",
            data={
                "publicKey": public_key,
                "action": "sell",
                "mint": mint,
                "amount": 100000,  # Adjust the amount as needed
                "denominatedInSol": "false",
                "slippage": 10,
                "priorityFee": 0.005,
                "pool": "pump"
            }
        )
        sell_response.raise_for_status()

        keypair = Keypair.from_base58_string(private_key)
        tx = VersionedTransaction(VersionedTransaction.from_bytes(sell_response.content).message, [keypair])
        commitment = CommitmentLevel.Confirmed
        config = RpcSendTransactionConfig(preflight_commitment=commitment)

        tx_payload = SendVersionedTransaction(tx, config)
        rpc_response = requests.post(
            url=rpc_endpoint,
            headers={"Content-Type": "application/json"},
            data=tx_payload.to_json()
        )

        if rpc_response.status_code == 200 and 'result' in rpc_response.json():
            tx_signature = rpc_response.json()['result']
            print(f"Sell transaction successful: https://solscan.io/tx/{tx_signature}")
        else:
            print(f"RPC error during sell: {rpc_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error executing sell trade: {e}")

async def subscribe():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        payload = {"method": "subscribeNewToken"}
        await websocket.send(json.dumps(payload))

        async for message in websocket:
            extract_mint(json.loads(message))

async def token():
    uri = "wss://pumpportal.fun/api/data"
    async with websockets.connect(uri) as websocket:
        await coins_populated_event.wait()

        payload = {
            "method": "subscribeTokenTrade",
            "keys": coins[0]  # array of token CAs to watch
        }
        await websocket.send(json.dumps(payload))

        async for message in websocket:
            message_json = json.loads(message)
            if 'marketCapSol' in message_json and 'mint' in message_json:
                record_trade_time(message_json['mint'])
                print(f"trade: {message_json['mint']} mc: {message_json['marketCapSol']}")
                if 35 <= message_json['marketCapSol'] <= 60:
                    print(message_json['mint'])
                    print("!!! BUY !!!")
                    await execute_trade(message_json['mint'])
                    
            # Sell logic option 1: Sell if market cap exceeds 70
                if message_json['marketCapSol'] > 70:  
                    print(message_json['mint'])
                    print("!!! SELL (Option 1: Market Cap Exceeded) !!!")
                    await execute_sell(message_json['mint'])
                
                # Sell logic option 2: Sell if a certain condition (placeholder) is met
                # Replace this condition with your desired logic (e.g., time-based, custom signal)
                if custom_sell_condition(message_json):
                    print(message_json['mint'])
                    print("!!! SELL (Option 2: Custom Condition Met) !!!")
                    await execute_sell(message_json['mint'])


def custom_sell_condition(message):
    """
    Placeholder for custom sell logic. Replace or expand this with your own condition.
    For example:
    - Check for price change over time
    - Check for specific trade volume
    """
    # Example placeholder condition: Sell if 'priceChange' is negative
    if 'priceChange' in message and message['priceChange'] < 0:
        return True
    return False



async def main():
    subscribe_task = asyncio.create_task(subscribe())
    token_task = asyncio.create_task(token())
    await asyncio.gather(subscribe_task, token_task)

asyncio.run(main())
