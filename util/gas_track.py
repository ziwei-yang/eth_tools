from eth_tool.common import web3_eth, etherscan, logger, cache

last_data = cache.last_gas_tracker()
new_data = etherscan.gas_tracker_or_cached(valid_cache_t=600)

data = new_data
if new_data == last_data:
    logger.info("gas_tracker data unchanged")

logger.info("At", data['time_str'], "Gas Tracker Contracts:")
idx = 0
for t in data['data']:
    idx = idx + 1
    idx_str = str(idx).ljust(3)
    name = t[0]
    addr = t[1]
    name_pad = t[0].ljust(len(addr))
    if name != addr: # Use public tag directly.
        logger.log(idx_str, addr, "Tag     ", logger.green(logger.reverse(name)))
        continue

    addr = web3_eth.toChecksumAddress(addr)
    # log("getCode()", addr)
    code = web3_eth.getCode(addr)
    if code == '0x': # Personal Address
        # logger.log(idx_str, name_pad, "Address")
        continue

    # Must be some contract
    info = etherscan.contract_info(addr, verbose=False)
    if info is None:
        # logger.error(idx_str, name_pad, "Contract ????")
        continue
    logger.log(idx_str, name_pad, "Contract", logger.green(logger.reverse(info['ContractName'])))
