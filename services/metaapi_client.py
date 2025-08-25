from metaapi_cloud_sdk import MetaApi
from config.settings import METAAPI
from utils.logger import get_logger

log = get_logger("metaapi")

class MetaApiClient:
    def __init__(self, user_token:str|None=None):
        self.token = user_token or METAAPI["mt5_token"]
        self.api = MetaApi(self.token)

    async def get_account(self, login_id: str|None=None):
        """If a specific account id is known, fetch. Else return first available."""
        try:
            accounts = await self.api.metatrader_account_api.get_accounts()
            if not accounts:
                return None
            if login_id:
                for a in accounts:
                    if a.login == login_id or a.id == login_id:
                        return a
            return accounts[0]
        except Exception as e:
            log.exception("MetaApi get_account failed: %s", e)
            return None
