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

for alias in contacts:
    addr_list = contacts[alias]
    for addr in addr_list:
        addr = Web3.toChecksumAddress(addr)
        debug("Scanning", alias, addr)
        new_txs = etherscan.addr_tx_update(addr, verbose=False)
        for tx in new_txs:
            log("New TX", alias, addr)
            print(etherscan.format_tx(tx, addr=addr))
