import json
from eth_tool.common import tool, cache, etherscan

addr = '0x0d533ffaa4f930d97710776524ba463fe482c4f7'
for tx in etherscan._raw_addr_internal_tx(addr, 0, verbose=True)[0:9]:
    print(json.dumps(tx))
    print('---------------------------------')

# etherscan.addr_tx_update(addr, verbose=True)
# 
# for tx in cache.addr_tx_get(addr, max=1)[0:9]:
#     print(etherscan.format_tx(tx, addr=addr))
#     print('---------------------------------')
