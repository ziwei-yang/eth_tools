import os
import json
import web3

from . import etherscan
from . import cache
from .logger import log, debug, error

w3 = web3.Web3(web3.Web3.HTTPProvider(
    'https://mainnet.infura.io/v3/' + os.environ['INFURA_ID']))

########################################
# Basic ABI and contract invokation.
########################################
def is_verbose(kwargs):
    return kwargs.get('verbose') != False

def contract_abi(addr, **kwargs):
    return etherscan.contract_abi(addr)

CONTRACT_MAP = {}
def get_contract(addr):
    if addr in CONTRACT_MAP:
        return CONTRACT_MAP[addr]
    contract = w3.eth.contract(address=addr, abi=contract_abi(addr))
    CONTRACT_MAP[addr] = contract
    return CONTRACT_MAP[addr]

def call_contract(contract_addr, func, *args, **kwargs):
    if etherscan.contract_abi(contract_addr) is None:
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
    return web3.Web3.toHex(w3.eth.getCode(addr))

def toChecksumAddress(addr):
    return web3.Web3.toChecksumAddress(addr)

########################################
# token info access
########################################
def token_info(addr_or_symbol, **kwargs):
    info = None
    if kwargs.get('skip_cache') != True:
        info = cache.token_cache_get(addr_or_symbol)
        if info is not None:
            return info
    
    if web3.Web3.isAddress(addr_or_symbol) == False:
        raise Exception("Unknown new symbol: " + addr_or_symbol)
    addr = web3.Web3.toChecksumAddress(addr_or_symbol)
    symbol = None
    try:
        symbol = call_contract(addr, 'symbol', verbose=True)
    except web3.exceptions.ABIFunctionNotFound:
        return None
    if symbol is None:
        return None
    name = call_contract(addr, 'name', verbose=True)
    decimals = 0
    try:
        decimals = call_contract(addr, 'decimals', verbose=True)
    except web3.exceptions.ABIFunctionNotFound:
        pass # zero by default.
    total_supply = call_contract(addr, 'totalSupply', verbose=True)
    kwargs = { 'total_supply' : total_supply }
    # Additional parser for different contracts:
    if symbol in ['UNI-V2', 'SLP']:
        token0_addr = web3.Web3.toChecksumAddress(call_contract(addr, 'token0', verbose=True))
        token0_symbol = __token_shown_symbol(token0_addr, '???')
        if token0_symbol is None:
            if token_info(token0_addr) is None:
                token0_symbol = '???'
            else:
                token0_symbol = token_info(token0_addr)['symbol']
        token1_addr = web3.Web3.toChecksumAddress(call_contract(addr, 'token1', verbose=True))
        token1_symbol = __token_shown_symbol(token1_addr, '???')
        fullname = symbol + ':' + token0_symbol + '-' + token1_symbol
        kwargs['token0'] = token0_addr
        kwargs['token1'] = token1_addr
        kwargs['_fullname'] = fullname
    elif symbol in ['BPT']:
        token_addr_list = call_contract(addr, 'getCurrentTokens', verbose=True)
        token_symbol_list = list(map(__token_shown_symbol, token_addr_list))
        kwargs['tokens'] = token_addr_list
        kwargs['_fullname'] = symbol + ':' + (' '.join(token_symbol_list))
    info = cache.token_cache_set(addr, symbol, name, decimals, **kwargs)
    return info

def __token_shown_symbol(addr, default=None):
    if cache.tag_address(addr) != None:
        return cache.tag_address(addr)
    if token_info(addr) is None:
        return default
    return token_info(addr)['symbol']

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
    bal = { 'ETH' : web3.Web3.fromWei(w3.eth.getBalance(addr), 'ether') }
    for addr_or_name in token_addr_or_name:
        b = token_balance(addr_or_name, addr, **kwargs)
        bal[addr_or_name] = b
        if web3.Web3.isAddress(addr_or_name): # Also write as symbol
            bal[cache.token_cache_get(addr_or_name)['symbol']] = b
    return bal

def print_balance(addr, token_addr_or_name=[]):
    bal_map = scan_balance(addr, token_addr_or_name)
    log('----', 'Bal', etherscan.render_addr(addr), '----')
    for k in bal_map:
        if web3.Web3.isAddress(k) == False:
            if bal_map[k] != 0:
                log(k.ljust(30), "%10f" % bal_map[k])
