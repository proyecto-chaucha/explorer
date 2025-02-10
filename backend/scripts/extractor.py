from dotenv import load_dotenv
from json import loads, dumps
from base64 import b64encode
from psycopg import connect
from decimal import Decimal
from urllib import request
from os import getenv


def rpc_call(method, params=[]):
	data = dumps({
			"jsonrpc": "2.0",
			"id": "extractor",
			"method": method,
			"params": [p for p in params]
		}).encode()

	req_url = f"http://{getenv('RPC_HOST')}:{getenv('RPC_PORT')}/"
	req_login = f"{getenv('RPC_USER')}:{getenv('RPC_PASS')}"

	req = request.Request(req_url, data=data)
	auth_base64 = b64encode(bytes(req_login, "ascii")).decode("utf-8")

	req.add_header("Authorization", "Basic %s" % auth_base64)
	req.add_header("Content-Type", "text/plain")
	req.add_header("Content-Length", len(data))

	resp = request.urlopen(req)
	if resp.status != 200:
		return None

	resp = loads(resp.read())
	assert resp["id"] == "extractor"
	return resp["result"]


def insert_block(cur, height, block):
	cur.execute("INSERT INTO work.blocks (height, block) \
				VALUES (%s, %s) ON CONFLICT DO NOTHING;", 
				(height, dumps(block)))


def insert_tx(cur, height, tx):
	cur.execute("INSERT INTO work.txs (height, txid, transaction) \
				VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", 
				(height, tx['txid'], dumps(tx)))


def extract_utxo(cur, height, tx):
	for vin in tx["vin"]:
		if "txid" not in vin:
			continue

		cur.execute("UPDATE work.utxos SET spent = true \
					WHERE txid = %s AND vout_n = %s;",
					(vin["txid"], vin["vout"],))

	for vout in tx["vout"]:
		vout_value = str(vout["value"])
		vout_value = Decimal(vout_value)*Decimal("1e8")
		vout_value = '{:f}'.format(vout_value)

		if "addresses" in vout["scriptPubKey"]:
			address = vout["scriptPubKey"]["addresses"][0]
		else:
			address = None

		cur.execute("INSERT INTO work.utxos (height, txid, vout_n, value, address) \
					VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;", 
					(height, tx['txid'], vout['n'], vout_value, address))


def main(conn_string):
	with connect(conn_string) as con:
		with con.cursor() as cur:
			res = cur.execute("SELECT MAX(height) FROM work.utxos;")
			last_height = res.fetchone()[0]
			start_height = 1 if last_height == None else last_height + 1
			print("last height:", last_height)

			end_height = rpc_call("getblockcount") + 1
			for height in range(start_height, end_height):
				blockhash = rpc_call("getblockhash", [height])
				block = rpc_call("getblock", [blockhash])
				insert_block(cur, height, block)

				for txid in block["tx"]:
					raw_tx = rpc_call("getrawtransaction", [txid])
					tx = rpc_call("decoderawtransaction", [raw_tx])

					extract_utxo(cur, height, tx)
					insert_tx(cur, height, tx)

				con.commit()

			print("blocks processed:", (end_height - start_height))


if __name__ == '__main__':
	load_dotenv()

	conn_string = f"host={getenv('DB_HOST')} \
					port={getenv('DB_PORT')} \
					dbname={getenv('DB_NAME')} \
					user={getenv('DB_USER')} \
					password={getenv('DB_PASS')}"

	main(conn_string)