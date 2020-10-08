import sys
import json
import re
from web3 import Web3
from eth_tool.common import web3_eth, cache, etherscan, logger

#################################################
# Analyze address latest TX.
#################################################

# args: addr [token] [page_size]
addr = None
page_size = 5
order_by = None
filter_by = None
token = None
for a in sys.argv:
    if Web3.isAddress(a):
        addr = Web3.toChecksumAddress(a)
    elif a.upper() == 'BYVALUE': # Order TX by token value
        order_by = 'value'
    elif a.upper() == 'BYTIME':
        order_by = None # Default
    elif a.upper() == 'BYNET': # Order TX associate addresses by sum(token value).
        order_by = 'netvalue'
    elif a.upper() == 'PEER': # Show transferring TX only.
        filter_by = 'peer'
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

#################################################
# TX filter
#################################################
if token is not None:
    logger.log("Filter", len(txs), "TX by", token)
    txs = list(filter(lambda tx: token in etherscan.tx_tokens(tx), txs))

if filter_by == 'peer':
    logger.log("Filter", len(txs), "TX by peer transfer")
    txs = list(filter(lambda tx: len(etherscan.tx_xfr_info(tx, addr, mode='peer')) == 1, txs))

#################################################
# TX analyzing
#################################################
if token is not None:
    if order_by == 'value':
        logger.log("Sort", len(txs), "TX by", token, "Value")
        txs = sorted(txs, key=lambda tx: etherscan.tx_token_value(tx, token), reverse=True)
    elif order_by == 'netvalue':
        logger.log("Compute", token, "net value in", len(txs), "TX")
        txs.reverse()
        net_value_map = {}
        for tx in txs:
            net_value_map = etherscan.tx_token_netvalue(tx, token, net_value_map=net_value_map)
        if addr in net_value_map:
            net_value_map.pop(addr)
        addr_value_list = sorted(list(net_value_map.items()), key=lambda kv: kv[1], reverse=True)
        logger.log("Biggest net buyer/withdrawer:")
        for kv in addr_value_list[0:19]:
            if kv[1] <= 0:
                break
            name = etherscan.render_addr(kv[0])
            logger.info(name.ljust(44), kv[1])
        logger.log("Biggest net seller/depositor:")
        addr_value_list.reverse()
        for kv in addr_value_list[0:19]:
            if kv[1] >= 0:
                break
            name = etherscan.render_addr(kv[0])
            logger.info(name.ljust(44), kv[1])
        quit()
    else: # Compute net value from TX for validation.
        net_value_map = {}
        for tx in txs:
            net_value_map = etherscan.tx_token_netvalue(tx, token, net_value_map=net_value_map)
        logger.log("Net value computed", net_value_map.get(addr))

#################################################
# TX printing
#################################################
logger.log("Total", len(txs), "TX")
for tx in txs:
    ct += 1
    print(ct, '---------------------------------')
    print(etherscan.format_tx(tx, addr=addr))
    if ct % page_size == 0:
        logger.info("Press enter to show", page_size, "more TX")
        input()