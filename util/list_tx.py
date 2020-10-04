import sys
import json
from eth_tool.common import web3_eth, cache, etherscan

addr = sys.argv[1]
max_num = 10
if len(sys.argv) > 2:
    max_num = int(sys.argv[2])

etherscan.addr_tx_update(addr, verbose=True)

ct = 0
for tx in cache.addr_tx_get(addr, max=max_num):
    ct += 1
    print(ct, '---------------------------------')
    print(etherscan.format_tx(tx, addr=addr))
    if ct >= max_num:
        break
