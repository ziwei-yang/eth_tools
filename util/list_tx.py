import sys
import json
import re
from web3 import Web3
from eth_tool.common import web3_eth, cache, etherscan, logger

# args: addr [token] [max_num]
addr = Web3.toChecksumAddress(sys.argv[1])
token = None
max_num = 5
for a in sys.argv[2:]:
    if re.match(r"^[0-9]{1,}$", a):
        max_num = int(a)
    elif re.match(r'^[A-Za-z]{2,8}$', a):
        token = a.upper()

txs = etherscan.addr_tx_update(addr, verbose=True)
tokens = etherscan.involved_tokens(txs)
if token is not None:
    web3_eth.print_balance(addr, [token])

ct = 0
for tx in cache.addr_tx_get(addr, max=max_num):
    if token == None:
        ct += 1
        print(ct, '---------------------------------')
        print(etherscan.format_tx(tx, addr=addr))
    elif any(token in t for t in etherscan.tx_tokens(tx)):
        ct += 1
        print(token, ct, '---------------------------------')
        print(etherscan.format_tx(tx, addr=addr))
    else:
        continue
    if ct % max_num == 0:
        logger.info("Press enter to show", max_num, "more TX")
        input()
