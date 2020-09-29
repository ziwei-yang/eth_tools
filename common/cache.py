import os
import json
from web3 import Web3

ROOT_DIR = os.environ['ETH_TOOLS_DIR']
CACHE_DIR = ROOT_DIR + '/cache'

########################################
# Cache for contract ABI
########################################
def abi_cache_clear(addr):
    abi_file = CACHE_DIR + '/abi.' +addr
    if os.path.exists(abi_file):
        os.remove(abi_file)

def abi_cache_get(addr):
    abi_file = CACHE_DIR + '/abi.' +addr
    if os.path.exists(abi_file):
        with open(abi_file, 'r') as f:
            return f.read()
    return None

def abi_cache_set(addr, abi):
    abi_file = CACHE_DIR + '/abi.' +addr
    with open(abi_file, 'w') as f:
        f.write(abi)

########################################
# Cache for token info
########################################
token_info_mem_cache = {}
def token_cache_set(addr, symbol, name, decimals):
    info = {
            'symbol': symbol,
            'name':   name,
            'addr':   addr,
            'decimals':decimals
        }
    token_info_mem_cache[addr] = token_info_mem_cache[symbol] = info

    addr_f = CACHE_DIR + '/addr.' + addr + '.json'
    symbol_f = CACHE_DIR + '/token.' + symbol + '.json'
    if os.path.exists(addr_f) and os.path.exists(symbol_f):
        return info
    json_str = json.dumps(info)
    with open(addr_f, 'w') as f:
        f.write(json_str)
    with open(symbol_f, 'w') as f:
        f.write(json_str)
    return info

def token_cache_get(addr_or_symbol):
    if addr_or_symbol in token_info_mem_cache:
        return token_info_mem_cache[addr_or_symbol]
    token_f = CACHE_DIR + '/token.' + addr_or_symbol + '.json'
    if Web3.isAddress(addr_or_symbol):
        token_f = CACHE_DIR + '/addr.' + addr_or_symbol + '.json'
    if os.path.exists(token_f):
        with open(token_f, 'r') as f:
            info = json.loads(f.read())
            token_info_mem_cache[addr_or_symbol] = info
            return info
    return None
