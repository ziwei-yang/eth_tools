import sys
import json
import re
from web3 import Web3
from eth_tool.common import web3_eth, cache, etherscan, logger
from eth_tool.common.logger import log, debug, error

#################################################
# Analyze address latest TX.
# choose address:
#   addr1 addr2 ...
#   tag/tag_name
#   contact/contact_name
# orderby:
#   byvalue
#   bytime
#   bynet
# filterby:
#   peer
#################################################

addr_list = [] # Target addresses
page_size = 5
order_by = None
filter_by = None
token = None
for a in sys.argv:
    if Web3.isAddress(a):
        addr_list.append(Web3.toChecksumAddress(a))
    elif re.match(r"^contact\/", a.lower()):
        contact_key = a.split('contact/')[1]
        addr_list = cache.contact_addresses(contact_key)
        if addr_list is None:
            error("No contact", contact_key)
            quit()
        logger.info("Load contact address", len(addr_list))
    elif re.match(r"^tag\/", a.lower()):
        tag_key = a.split('tag/')[1]
        a = cache.tag_address(tag_key)
        if a is None:
            error("No tag", a)
            quit()
        logger.info("Load tag address", a)
        addr_list = [a]
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
    elif re.match(r'^[A-Za-z0-9\-]{2,8}$', a):
        token = a.upper()

logger.info("Addresses", len(addr_list))
logger.info("Token", token, "order_by", order_by, "filter_by", filter_by)

txs_ct = 0
txs_map = {}
for a in addr_list:
    etherscan.addr_tx_update(a, verbose=True)
    txs_map[a] = cache.addr_tx_get(a)
    txs_ct = txs_ct + len(txs_map[a])

#################################################
# TX filter, would be post-filtering if txs is too many.
#################################################
if token is not None:
    for a in txs_map:
        txs = txs_map[a]
        logger.log("Filter", len(txs), "TX by", token, a)
        txs_map[a] = list(filter(lambda tx: token in etherscan.tx_tokens(tx), txs))

if filter_by == 'peer' and txs_ct < 1000:
    for a in txs_map:
        txs = txs_map[a]
        logger.log("Filter", len(txs), "TX by peer transfer", a)
        txs_map[a] = list(filter(lambda tx: len(etherscan.tx_xfr_info(tx, a, mode='peer')) == 1, txs))

#################################################
# TX merging, add owner address.
#################################################
all_txs = []
for a in txs_map:
    for tx in txs_map[a]:
        tx['owner'] = a
        all_txs.append(tx)
if len(txs_map) > 1:
    all_txs = sorted(all_txs, key=lambda tx: tx['timeStamp'], reverse=True)

#################################################
# TX analyzing
#################################################
if token is not None:
    if order_by == 'value':
        logger.log("Sort", len(all_txs), "TX by", token, "Value")
        all_txs = sorted(all_txs, key=lambda tx: etherscan.tx_token_value(tx, token), reverse=True)
    elif order_by == 'netvalue':
        logger.log("Compute", token, "net value in", len(txs), "TX")
        net_value_map = {}
        for tx in all_txs:
            net_value_map = etherscan.tx_token_netvalue(tx, token, net_value_map=net_value_map)
        for a in addr_list:
            if a in net_value_map:
                net_value_map.pop(a)
        addr_value_list = sorted(list(net_value_map.items()), key=lambda kv: kv[1], reverse=True)
        logger.log("Biggest net buyer/withdrawer:")
        for kv in addr_value_list[0:19]:
            if kv[1] <= 0:
                break
            name = etherscan.render_addr(kv[0])
            if name == kv[0]:
                logger.info(kv[0], kv[1])
            else:
                logger.info(kv[0], kv[1], name)
        logger.log("Biggest net seller/depositor:")
        addr_value_list.reverse()
        for kv in addr_value_list[0:19]:
            if kv[1] >= 0:
                break
            name = etherscan.render_addr(kv[0])
            if name == kv[0]:
                logger.info(kv[0], kv[1])
            else:
                logger.info(kv[0], kv[1], name)
        quit()
    else: # Compute net value from TX for validation.
        net_value_map = {}
        for tx in txs:
            net_value_map = etherscan.tx_token_netvalue(tx, token, net_value_map=net_value_map)
        for a in addr_list:
            logger.log("Net", token, "balance computed", a, net_value_map.get(a))

if token is not None:
    for a in addr_list:
        web3_eth.print_balance(a, [token])

#################################################
# TX printing
#################################################
logger.log("Total", len(all_txs), "TX")
ct = 0
for tx in all_txs:
    # Post-filtering
    if filter_by == 'peer':
        if len(etherscan.tx_xfr_info(tx, a, mode='peer')) != 1:
            continue
    ct += 1
    print(ct, '---------------------------------')
    print(etherscan.format_tx(tx, addr=tx['owner'], show_owner=(len(addr_list)>1)))
    if ct % page_size == 0:
        logger.info("Press enter to show", page_size, "more TX")
        input()
