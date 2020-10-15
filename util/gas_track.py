import json
from web3 import Web3
from eth_tool.common import web3_eth, etherscan, logger, cache

last_data = cache.last_gas_tracker()
new_data = etherscan.gas_tracker_or_cached()

data = new_data
if new_data == last_data:
    logger.info("gas_tracker data unchanged")

logger.info(data['time_str'])
for t in data['data']:
    name = t[0]
    addr = t[1]
    logger.info(name)
    if name != addr: # Use public tag directly.
        continue

    addr = Web3.toChecksumAddress(addr)
    logger.log("\t", addr)
    # log("getCode()", addr)
    code = web3_eth.getCode(addr)
    if code == '0x': # Personal Address
        continue
    # Must be some contract
    info = etherscan.contract_info(addr)
    if info is None:
        logger.error("contract name not found on etherscan")
        continue
    logger.info("\t\t", "Contract name", logger.reverse(info['ContractName']))
