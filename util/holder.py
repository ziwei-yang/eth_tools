import sys
import re
import os
import datetime
from web3 import Web3
from eth_tool.common import webbrowser, web3_eth, etherscan, logger, cache

mem_logs = []

def mem_log(*args):
    strs = logger.log(*args, stacktrace_level=2)
    mem_logs.append(strs)
    globals()['mem_log_f'].write(" ".join(strs[2:]) + "\n") # Remove headers
    globals()['mem_log_f'].flush()

def parse_print_holders(target_addr, **kwargs):
    token_info = kwargs.get("token_info") or web3_eth.token_info(target_addr)
    header = kwargs.get("header") or ""
    if token_info is None:
        logger.error("No such token", target_addr)
        return

    data = etherscan.token_holders(target_addr)

    idx = 0
    show_qty_int = None
    first_qty = None
    for t in data:
        idx = idx + 1
        idx_str = header + str(idx).ljust(3)
        name, addr, qty = t
        qty_num = float(qty.replace(',', ''))
        if first_qty is None:
            first_qty = qty_num
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
        has_tag = (name != addr)
        checksum_addr = web3_eth.toChecksumAddress(addr)
        contract_info = None
        if has_tag: # Use public tag directly if could not find contract info.
            contract_info = etherscan.contract_info(checksum_addr, verbose=False)
            if contract_info is None:
                mem_log(idx_str, checksum_addr, qty, "Tag     ", logger.light_white(logger.on_green(name)))
                continue

        if contract_info is None:
            code = web3_eth.getCode(checksum_addr)
            if code == '0x': # Personal Address
                if idx <= 10 and qty_num/first_qty >= 0.1:
                    mem_log(idx_str, name_pad, qty)
                continue

        contract_info = etherscan.contract_info(checksum_addr, verbose=False)
        # Must be some contract
        if contract_info is None: # not open sourced yet.
            if idx <= 10:
                mem_log(idx_str, name_pad, qty, "Contract", "????")
            continue
        contract_name = contract_info['ContractName']
        mem_log(idx_str, checksum_addr, qty, "Contract", logger.light_white(logger.on_green(contract_name)))
        # If contract is LP, analyze its holder too.
        if checksum_addr == web3_eth.toChecksumAddress(target_addr):
            pass
        elif contract_name.startswith("UNI-V2:"):
            parse_print_holders(addr, header=' '*len(header) + "\t|-----\t")
        elif contract_name.startswith("BPT:"):
            parse_print_holders(addr, header=' '*len(header) + "\t|-----\t")
        elif contract_name.startswith("SLP:"):
            parse_print_holders(addr, header=' '*len(header) + "\t|-----\t")

token_addr = None
token_info = None
for a in sys.argv:
    if Web3.isAddress(a):
        token_addr = Web3.toChecksumAddress(a)
        token_info = web3_eth.token_info(token_addr)
    elif re.match(r'^[A-Za-z0-9\-]{2,8}$', a):
        token = a.upper()
        token_info = web3_eth.token_info(a)

if token_info is None:
    logger.error("No such token", token_addr)
    quit()
token_addr = token_info['addr']
globals()['mem_log_f'] = open("output/holder."+token_addr+".log.tmp", 'w')

mem_log(
    datetime.datetime.now().strftime("%m/%d-%H:%M:%S.%f"),
    "[",
    token_info.get("_fullname") or token_info['name'],
    "]",
    token_addr)

parse_print_holders(token_addr, token_info=token_info)

logger.info("memorized logs:")
for strs in mem_logs:
    strs = strs[2:] # Remove header
    print(*strs)

globals()['mem_log_f'].close()
os.rename(
        "output/holder."+token_addr+".log.tmp",
        "output/holder."+token_addr+".log"
    )
