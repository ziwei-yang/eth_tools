import sys
from web3 import Web3
from eth_tool.common import webbrowser, web3_eth, etherscan, logger, cache

addr_or_name = sys.argv[1]
logger.debug(addr_or_name)
data = etherscan.token_holders(addr_or_name)

addr = addr_or_name
if Web3.isAddress(addr_or_name):
    addr = Web3.toChecksumAddress(addr_or_name)
    info = web3_eth.token_info(addr)
    logger.info("Token name", info.get("_fullname") or info['name'], addr)
else:
    info = web3_eth.token_info(addr)
    logger.info("Token name", addr, info['addr'])

idx = 0
for t in data:
    idx = idx + 1
    idx_str = str(idx).ljust(3)
    name, addr, qty = t
    qty = qty.split('.')[0].rjust(10) # Get Integer part
    name_pad = t[0].ljust(len(addr))
    if name != addr: # Use public tag directly.
        logger.log(idx_str, addr, qty, "Tag     ", logger.green(logger.reverse(name)))
        continue

    addr = web3_eth.toChecksumAddress(addr)
    code = web3_eth.getCode(addr)
    if code == '0x': # Personal Address
        if idx <= 10:
            logger.log(idx_str, name_pad, qty)
        continue

    # Must be some contract
    info = etherscan.contract_info(addr, verbose=False)
    if info is None:
        if idx <= 10:
            logger.error(idx_str, name_pad, qty, "Contract ????")
        continue
    logger.log(idx_str, name_pad, qty, "Contract", logger.green(logger.reverse(info['ContractName'])))
