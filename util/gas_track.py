import json
from web3 import Web3
from eth_tool.common import web3_eth, etherscan, logger, cache

last_data = cache.last_gas_tracker()
new_data = etherscan.gas_tracker_or_cached(valid_cache_t=600)

data = new_data
if new_data == last_data:
    logger.info("gas_tracker data unchanged")

logger.info("At", data['time_str'], "Gas Tracker Contracts:")
for t in data['data']:
    name = t[0]
    addr = t[1]
    name_pad = t[0].ljust(len(addr))
    if name != addr: # Use public tag directly.
        logger.log(addr, "Tag     ", logger.green(logger.reverse(name)))
        continue

    addr = Web3.toChecksumAddress(addr)
    # log("getCode()", addr)
    code = web3_eth.getCode(addr)
    if code == '0x': # Personal Address
        # logger.log(name_pad, "Address")
        continue

    # Must be some contract
    info = etherscan.contract_info(addr, verbose=False)
    if info is None:
        # logger.error(name_pad, "Contract ????")
        continue
    logger.log(name_pad, "Contract", logger.green(logger.reverse(info['ContractName'])))
