import os
import json
import web3
from web3 import Web3

from . import etherscan
from . import cache
from .logger import log, debug, error

w3 = Web3(Web3.HTTPProvider(
    'https://mainnet.infura.io/v3/' + os.environ['INFURA_ID']))

########################################
# Basic ABI and contract invokation.
########################################
def is_verbose(kwargs):
    return kwargs.get('verbose') != False

def contract_abi(addr, **kwargs):
    info = etherscan.contract_info(addr)
    return info['ABI']

CONTRACT_MAP = {}
def get_contract(addr):
    if addr in CONTRACT_MAP:
        return CONTRACT_MAP[addr]
    contract = w3.eth.contract(address=addr, abi=contract_abi(addr))
    CONTRACT_MAP[addr] = contract
    return CONTRACT_MAP[addr]

def call_contract(contract_addr, func, *args, **kwargs):
    if etherscan.contract_info(contract_addr) is None:
        error("No contract info", contract_addr)
        return None
    if is_verbose(kwargs):
        if cache.token_cache_get(contract_addr) is not None:
            symbol = cache.token_cache_get(contract_addr)['symbol']
            debug("Call", symbol, func, *args)
        else:
            debug("Call", contract_addr, func, *args)
    try:
        return get_contract(contract_addr).functions[func](*args).call()
    except web3.exceptions.BadFunctionCallOutput:
        error("BadFunctionCallOutput while calling", contract_addr,
                "Maybe contract is destructed.")
        return None

########################################
# Other basic ETH APIs.
########################################
def eth():
    return w3.eth

def getCode(addr):
    return Web3.toHex(w3.eth.getCode(addr))

########################################
# token info access
########################################
def token_info(addr_or_symbol):
    info = cache.token_cache_get(addr_or_symbol)
    if info is not None:
        return info
    
    if Web3.isAddress(addr_or_symbol) == False:
        raise Exception("Unknown new symbol: " + addr_or_symbol)
    addr = addr_or_symbol
    symbol = call_contract(addr, 'symbol', verbose=True)
    if symbol is None:
        return None
    name = call_contract(addr, 'name', verbose=True)
    decimals = call_contract(addr, 'decimals', verbose=True)
    total_supply = call_contract(addr, 'totalSupply', verbose=True)
    info = cache.token_cache_set(addr, symbol, name, decimals, total_supply=total_supply)
    return info

def token_balance(addr_or_name, addr, **kwargs):
    info = token_info(addr_or_name)
    t_addr = info['addr']
    try:
        ret = call_contract(t_addr, 'balanceOf', addr, **kwargs)
        if ret is None:
            return -1
        return int(ret)/(10**(info['decimals']))
    except web3.exceptions.ABIFunctionNotFound:
        return -1

def scan_balance(addr, token_addr_or_name=[], **kwargs):
    bal = { 'ETH' : Web3.fromWei(w3.eth.getBalance(addr), 'ether') }
    for addr_or_name in token_addr_or_name:
        b = token_balance(addr_or_name, addr, **kwargs)
        bal[addr_or_name] = b
        if Web3.isAddress(addr_or_name): # Also write as symbol
            bal[cache.token_cache_get(addr_or_name)['symbol']] = b
    return bal

def print_balance(addr, token_addr_or_name=[]):
    bal_map = scan_balance(addr, token_addr_or_name)
    log('----', 'Bal', etherscan.render_addr(addr), '----')
    for k in bal_map:
        if Web3.isAddress(k) == False:
            if bal_map[k] != 0:
                log(k.ljust(30), "%10f" % bal_map[k])
