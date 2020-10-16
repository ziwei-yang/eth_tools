import json
from web3 import Web3
from eth_tool.common import webbrowser, web3_eth, etherscan, logger, cache

data = etherscan.token_holders("Pickle")

idx = 0
for t in data:
    idx = idx + 1
    idx_str = str(idx).ljust(3)
    name, addr, qty = t
    name_pad = t[0].ljust(len(addr))
    if name != addr: # Use public tag directly.
        logger.log(idx_str, addr, "Tag     ", logger.green(logger.reverse(name)))
        continue

    addr = Web3.toChecksumAddress(addr)
    # log("getCode()", addr)
    code = web3_eth.getCode(addr)
    if code == '0x': # Personal Address
        logger.log(idx_str, name_pad)
        continue

    # Must be some contract
    info = etherscan.contract_info(addr, verbose=False)
    if info is None:
        # logger.error(idx_str, name_pad, "Contract ????")
        continue
    logger.log(idx_str, name_pad, "Contract", logger.green(logger.reverse(info['ContractName'])))
