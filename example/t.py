import json
from eth_tool.common import tool, cache, etherscan

addr = '0x0d533ffaa4f930d97710776524ba463fe482c4f7'
etherscan.addr_tx_update(addr, verbose=True)

for tx in cache.addr_tx_get(addr, max=1):
    print(etherscan.format_tx(tx, addr=addr))
    print('---------------------------------')
