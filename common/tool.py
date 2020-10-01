import os
import json
from web3 import Web3

from . import etherscan
from . import cache

w3 = Web3(Web3.HTTPProvider(
    'https://mainnet.infura.io/v3/' + os.environ['INFURA_ID']))

########################################
# Basic ABI and contract invokation.
########################################
def is_verbose(kwargs):
    return kwargs.get('verbose') != False

def contract_abi(addr, **kwargs):
    contract_info = cache.contract_info(addr)
    if contract_info is not None:
        return contract_info['ABI']
    info = etherscan.contract_info(addr)
    cache.contract_info_set(addr, info)
    return info['ABI']

CONTRACT_MAP = {}
def get_contract(addr):
    if addr in CONTRACT_MAP:
        return CONTRACT_MAP[addr]
    contract = w3.eth.contract(address=addr, abi=contract_abi(addr))
    CONTRACT_MAP[addr] = contract
    return CONTRACT_MAP[addr]

def call_contract(contract_addr, func, *args, **kwargs):
    if is_verbose(kwargs):
        if cache.token_cache_get(contract_addr) is not None:
            symbol = cache.token_cache_get(contract_addr)['symbol']
            print("Call", symbol, func, *args)
        else:
            print("Call", contract_addr, func, *args)
    return get_contract(contract_addr).functions[func](*args).call()

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
    name = call_contract(addr, 'name', verbose=True)
    decimals = call_contract(addr, 'decimals', verbose=True)
    info = cache.token_cache_set(addr, symbol, name, decimals)
    return info

def token_balance(addr_or_name, addr, **kwargs):
    info = token_info(addr_or_name)
    t_addr = info['addr']
    ret = call_contract(t_addr, 'balanceOf', addr, **kwargs)
    return int(ret)/(10**(info['decimals']))

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
    print('----', 'Bal', addr, '----')
    for k in bal_map:
        if Web3.isAddress(k) == False:
            print(k.ljust(12), bal_map[k])
