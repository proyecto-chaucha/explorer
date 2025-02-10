from sqlmodel import SQLModel, Column, Field, JSON


class UTXO(SQLModel, table=True):
    __tablename__ = "utxos"
    __table_args__ = {'schema': 'work'}

    txid: str = Field(primary_key=True)
    height: int = Field(index=True)
    vout_n: int = Field(primary_key=True)
    value: int
    address: str = Field(index=True)
    spent: bool | None = Field(default=False)


class TX(SQLModel, table=True):
    __tablename__ = "txs"
    __table_args__ = {'schema': 'work'}

    txid: str = Field(primary_key=True)
    height: int = Field(index=True)
    transaction: dict = Field(default_factory=dict, sa_column=Column(JSON))

    class Config:
        arbitrary_types_allowed = True


class Block(SQLModel, table=True):
    __tablename__ = "blocks"
    __table_args__ = {'schema': 'work'}
    height: int = Field(primary_key=True, index=True)
    block: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    class Config:
        arbitrary_types_allowed = True