import sys
import json
from web3 import Web3
from eth_tool.common import web3_eth, cache, etherscan, logger
from eth_tool.common.logger import debug, log

#################################################
# Check if address is contract
# Print its balance and latest TX.
#################################################
addr = Web3.toChecksumAddress(sys.argv[1])

info = cache.contract_info(addr)
if info is not None:
    if len(info) == 0:
        log("Contract info is empty", info)
    elif len(info['ContractName']) > 0:
        log("Contract name", logger.on_green(info['ContractName']))
        quit()

log("getCode()", addr)
code = web3_eth.getCode(addr)
if code is not '0x': # Contract
    if len(code) > 30:
        log("\t", "code", code[0:29], "...",  "len:", len(code)-2)
    else:
        log("\t", "code", code,  "len:", len(code)-2)

    info = etherscan.contract_info(addr)
    if info is None:
        log("contract name not found on etherscan")
    else:
        log("Contract name", logger.on_green(info['ContractName']))
    quit()

# Address
log("It seems to be a non-contract address", addr)
etherscan.addr_tx_update(addr, verbose=True)
txs = cache.addr_tx_get(addr)
tokens = etherscan.involved_tokens(txs)
web3_eth.print_balance(addr, tokens.keys())
ct = 0
for tx in txs:
    ct = ct + 1
    print(ct, '---------------------------------')
    print(etherscan.format_tx(tx, addr=addr))
    if ct % 5 == 0:
        input(logger.green("Press enter to show 5 more TX"))
