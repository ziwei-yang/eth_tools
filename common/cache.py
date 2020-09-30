import os
import json
import re
from web3 import Web3

ROOT_DIR = os.environ['ETH_TOOLS_DIR']
CACHE_DIR = ROOT_DIR + '/cache'
for d in ['abi', 'addr', 'token', 'etherscan_tx_his']:
    if os.path.exists(CACHE_DIR + '/' + d) is False:
        os.mkdir(CACHE_DIR + '/' + d)

########################################
# Cache for contract ABI
########################################
def abi_cache_clear(addr):
    abi_file = CACHE_DIR + '/abi/' +addr
    if os.path.exists(abi_file):
        os.remove(abi_file)

def abi_cache_get(addr):
    abi_file = CACHE_DIR + '/abi/' +addr
    if os.path.exists(abi_file):
        with open(abi_file, 'r') as f:
            return f.read()
    return None

def abi_cache_set(addr, abi):
    abi_file = CACHE_DIR + '/abi/' +addr
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

    addr_f = CACHE_DIR + '/addr/' + addr + '.json'
    symbol_f = CACHE_DIR + '/token/' + symbol + '.json'
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
    token_f = CACHE_DIR + '/token/' + addr_or_symbol + '.json'
    if Web3.isAddress(addr_or_symbol):
        token_f = CACHE_DIR + '/addr/' + addr_or_symbol + '.json'
    if os.path.exists(token_f):
        with open(token_f, 'r') as f:
            info = json.loads(f.read())
            token_info_mem_cache[addr_or_symbol] = info
            return info
    return None

########################################
# Cache for TX list for address
# Etherscan tx querying for addr is very expensive,
# Cache history tx in cache/etherscan_tx_his/addr/$from_blk.$to_blk.json
########################################
def addr_tx_get(addr, **kwargs):
    dir_p = CACHE_DIR + '/etherscan_tx_his/' + addr
    if os.path.exists(dir_p) is False:
        os.mkdir(dir_p)
    files = [f for f in os.listdir(dir_p) if re.match(r"^[0-9]{1,8}\.[0-9]{8,10}.json$", f)]
    files.sort(reverse=True) # From latest to oldest
    # Parse from file until max reached.
    txs = []
    for f1 in files:
        with open(dir_p+'/'+f1, 'r') as f:
            txs = txs + json.loads(f.read())
            if len(txs) >= kwargs.get('max') or 1000:
                break
    return txs # Sort txs again?

def addr_tx_append(addr, txs, from_blk, end_blk, **kwargs):
    # Defensive check.
    latest_cached_blk = -1 
    latest_cached_txs = addr_tx_get(addr, max=1)
    if len(latest_cached_txs) > 0:
        latest_cached_blk = latest_cached_txs[0]['blockNumber']
    if latest_cached_blk >= from_blk:
        raise Exception("Latest blk in cached data", latest_cached_blk, "append", from_blk)
    if from_blk > end_blk:
        raise Exception("Append blk error", from_blk, end_blk)

    dir_p = CACHE_DIR + '/etherscan_tx_his/' + addr
    if os.path.exists(dir_p) is False:
        os.mkdir(dir_p)
    f_path = CACHE_DIR+'/etherscan_tx_his/'+addr+'/'+str(from_blk)+'.'+str(end_blk)+'.json'
    print("Append TX to", addr, from_blk, '->', end_blk)
    with open(f_path, 'w') as f:
        f.write(json.dumps(txs))
