import sys
from web3 import Web3
from eth_tool.common import webbrowser, web3_eth, etherscan, logger, cache

addr_or_name = sys.argv[1]
logger.debug(addr_or_name)
data = etherscan.token_holders(addr_or_name)

addr = addr_or_name
if Web3.isAddress(addr_or_name):
    addr = Web3.toChecksumAddress(addr_or_name)
    info = web3_eth.token_info(addr, skip_cache=True)
else:
    info = web3_eth.token_info(addr)
    if info is None:
        logger.error("No such token", addr)
        quit()
    addr = info['addr']
logger.info("Token name", info.get("_fullname") or info['name'], addr)

idx = 0
show_qty_int = None
for t in data:
    idx = idx + 1
    idx_str = str(idx).ljust(3)
    name, addr, qty = t
    qty_int_str = qty.split('.')[0]
    if show_qty_int is None: # Decide show_qty_int by first record.
        if len(qty_int_str) > 3:
            show_qty_int = True
        else:
            show_qty_int = False
    if show_qty_int:
            qty = qty.split('.')[0].rjust(10) # Get Integer part
    else:
            qty = qty.rjust(10) # Get all.
    name_pad = t[0].ljust(len(addr))
    etherscan_tag = None
    if name != addr: # Use public tag directly if could not find contract info.
        etherscan_tag = name
        info = etherscan.contract_info(addr, verbose=False)
        if info is None:
            logger.log(idx_str, addr, qty, "Tag     ", logger.green(logger.reverse(name)))
        else:
            logger.log(idx_str, addr, qty, "Contract", logger.green(logger.reverse(info['ContractName'])))
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
