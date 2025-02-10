from pydantic import BaseModel


class BlockResp(BaseModel):
    block: dict

class TxResp(BaseModel):
    transaction: dict

class BalanceResp(BaseModel):
    balance: float

class SupplyResp(BaseModel):
    block_height: int
    supply: float

class UtxoResp(BaseModel):
    utxos: list