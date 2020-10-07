import sys
import json
import re
from web3 import Web3
from eth_tool.common import web3_eth, cache, etherscan, logger

# args: addr [token] [page_size]
addr = Web3.toChecksumAddress(sys.argv[1])
page_size = 5
order_by = None
token = None
for a in sys.argv[2:]:
    if a.upper() == 'BYVALUE':
        order_by = 'value'
    elif a.upper() == 'BYTIME':
        order_by = None # Default
    elif re.match(r"^[0-9]{1,}$", a):
        page_size = int(a)
    elif re.match(r'^[A-Za-z]{2,8}$', a):
        token = a.upper()

txs = etherscan.addr_tx_update(addr, verbose=True)
tokens = etherscan.involved_tokens(txs)
if token is not None:
    web3_eth.print_balance(addr, [token])

ct = 0
txs = cache.addr_tx_get(addr)
if token is not None:
    logger.log("Filter TX by", token)
    txs = filter(lambda tx: token in etherscan.tx_tokens(tx), txs)
if order_by == 'value':
    if token is not None:
        logger.log("Sort TX by", token, "value")
        txs = sorted(txs, key=lambda tx: etherscan.tx_token_value(tx, token), reverse=True)

for tx in txs:
    ct += 1
    print(ct, '---------------------------------')
    print(etherscan.format_tx(tx, addr=addr))
    if ct % page_size == 0:
        logger.info("Press enter to show", page_size, "more TX")
        input()
