from sqlmodel import create_engine, Session, SQLModel, select, JSON
from fastapi import FastAPI, HTTPException, Depends
from dotenv import load_dotenv
from sqlalchemy import func
from os import getenv
from json import dumps

from .models import *
from .responses import *


load_dotenv()

con_creds = f"{getenv('DB_USER')}:{getenv('DB_PASS')}"
con_url = f"{getenv('DB_HOST')}:{getenv('DB_PORT')}"
con_db = getenv('DB_NAME')
DATABASE_URL = f"postgresql://{con_creds}@{con_url}/{con_db}"
engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI()


@app.get("/supply", response_model=SupplyResp)
def get_block(session: Session = Depends(get_session)):
    query = select(
        func.max(UTXO.height),
        func.sum(UTXO.value) / 1e8
    ).where(UTXO.spent==False)
    result = session.exec(query).one()
    height, supply = result
    return SupplyResp(block_height=height, supply=supply)


@app.get("/block/{height}", response_model=BlockResp)
def get_block(height: int, session: Session = Depends(get_session)):
    if height <= 0:
        raise HTTPException(status_code=404, detail="Block not found")

    query = select(Block.block).filter(Block.height==height)
    result = session.exec(query).one()
    if result is None:
        raise HTTPException(status_code=404, detail="Block not found")

    del result["confirmations"]
    return BlockResp(block=result)


@app.get("/tx/{txid}", response_model=TxResp)
def get_tx(txid: str, session: Session = Depends(get_session)):
    if len(txid) != 64:
        raise HTTPException(status_code=404, detail="Address invalid length")
        
    query = select(TX.transaction).filter(TX.txid==txid)
    result = session.exec(query).one()
    if result is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TxResp(transaction=result)


@app.get("/utxo/{address}", response_model=UtxoResp)
def get_utxos(address: str, session: Session = Depends(get_session)):
    if len(address) != 34:
        raise HTTPException(status_code=404, detail="Address invalid length")

    query = select(UTXO).filter(UTXO.address==address).filter(UTXO.spent==False)
    result = session.exec(query).all()
    if result is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return UtxoResp(utxos=result)


@app.get("/balance/{address}", response_model=BalanceResp)
def get_balance(address: str, session: Session = Depends(get_session)):
    if len(address) != 34:
        raise HTTPException(status_code=404, detail="Address invalid length")

    query = select(func.sum(UTXO.value) / 1e8).where(
        UTXO.address==address,
        UTXO.spent==False
    )
    result = session.exec(query).one()
    if result is None:
        raise HTTPException(status_code=404, detail="Address not found")

    return BalanceResp(balance=result)