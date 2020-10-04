import sys
import json
from eth_tool.common import web3_eth, cache, etherscan, logger
from eth_tool.common.logger import debug, log

addr = sys.argv[1]
max_num = 10
if len(sys.argv) > 2:
    max_num = int(sys.argv[2])

info = cache.contract_info(addr)
if info is not None:
    log("Contract name", logger.on_green(info['ContractName']))
else:
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
    else: # Address
        log("It seems to be a non-contract address", addr)
