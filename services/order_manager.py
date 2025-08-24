from metaapi_cloud_sdk import MetaApi
from config import META_API_TOKEN

class OrderManager:
    def __init__(self, user_token: str):
        self.token = user_token
        self.api = MetaApi(self.token)

    async def get_account_balance(self, account_id: str) -> float:
        try:
            account = await self.api.metatrader_account_api.get_account(account_id)
            await account.wait_connected()
            account_information = account.account_information
            return account_information['balance']
        except Exception as e:
            print(f"Error getting account balance: {e}")
            return 0.0

    def get_lot_size(self, balance: float) -> float:
        if 30 <= balance <= 100: return 0.01
        if 100 < balance <= 200: return 0.02
        if 200 < balance <= 400: return 0.04
        if 400 < balance <= 700: return 0.05
        if 700 < balance <= 1100: return 0.07
        if balance > 1100: return 0.08
        return 0.01 # Default smallest lot

    async def execute_trade(self, account_id: str, trade_details: dict):
        balance = await self.get_account_balance(account_id)
        lot_size = self.get_lot_size(balance)
        
        try:
            account = await self.api.metatrader_account_api.get_account(account_id)
            connection = account.get_rpc_connection()
            await connection.connect()
            
            result = await connection.create_market_buy_order(
                symbol=trade_details['symbol'],
                volume=lot_size,
                stop_loss=trade_details['sl'],
                take_profit=trade_details['tp1'],
                comment='migosconcept_bot'
            )
            print(f"Trade execution result: {result}")
            return result
        except Exception as e:
            print(f"Error executing trade: {e}")
            return None
