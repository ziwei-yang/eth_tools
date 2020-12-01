import os
import sys
import json
from web3 import Web3
from eth_tool.common import web3_eth, cache, etherscan, logger
from eth_tool.common.logger import debug, log

ROOT_DIR = os.environ['ETH_TOOLS_DIR']
contacts_ = ROOT_DIR + '/data/trace_contacts.json'
if len(sys.argv) >= 2:
    contacts_ = sys.argv[1]

log("Loading", contacts_)
with open(contacts_, 'r') as f:
    contacts = json.loads(f.read())

contact_ct = 0
for alias in contacts:
    contact_ct += 1
    addr_list = contacts[alias]
    has_new_tx = False
    for addr in addr_list:
        addr = Web3.toChecksumAddress(addr)
        debug("Scanning", alias, addr)
        new_txs = etherscan.addr_tx_update(addr, verbose=False)
        if len(new_txs) == 0:
            continue
        has_new_tx = True
        log("New TX", alias, addr)
        ct = 0
        page_size = 5
        for tx in new_txs:
            ct += 1
            print(etherscan.format_tx(tx, addr=addr))
            if ct % page_size == 0:
                logger.info(
                        "Press enter to show",
                        ct+1, "-", min(len(new_txs), ct+page_size),
                        "/", len(new_txs),
                        "TX [", alias, "]")
                input()
    if has_new_tx:
        logger.info("Press enter to scan next addr", contact_ct+1, '/', len(contacts))
        input()
