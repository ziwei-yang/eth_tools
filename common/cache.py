import os
import json
import re
from web3 import Web3

########################################
# Cache provides a layer for other components.
# Should not be called from outside.
########################################

ROOT_DIR = os.environ['ETH_TOOLS_DIR']
CACHE_DIR = ROOT_DIR + '/cache'
RES_DIR = ROOT_DIR + '/res'

for d in ['contract', 'addr', 'token', 'etherscan_tx_his']:
    if os.path.exists(CACHE_DIR + '/' + d) is False:
        os.mkdir(CACHE_DIR + '/' + d)

CONTRACT_NAME_MAP = {}
CONTRACT_NAME_MAP_FILE = RES_DIR + '/export-verified-contractaddress-opensource-license.csv'
if os.path.exists(CONTRACT_NAME_MAP_FILE):
    print("Loading contract addr-name")
    with open(CONTRACT_NAME_MAP_FILE, 'r') as f:
        for l in f.readlines():
            segs = l.split(',')
            if len(segs) != 3:
                continue
            if len(segs) != 3 or len(segs[1]) < 16 or len(segs[2]) < 3:
                continue
            addr = segs[1][1:-1] # Remove quotes
            name = segs[2][1:-2] # Remove quotes and new line char.
            if Web3.isAddress(addr):
                CONTRACT_NAME_MAP[addr] = name
    print(len(CONTRACT_NAME_MAP), "contract addr-name load")
else:
    print("No export-verified-contractaddress-opensource-license.csv found in res")

########################################
# Cache for contract name
########################################
def contract_name(addr):
    # Layer 1 cache
    if addr in CONTRACT_NAME_MAP:
        return CONTRACT_NAME_MAP[addr]
    # Layer 2 file cache
    info = contract_info(addr)
    if info is not None:
        CONTRACT_NAME_MAP[addr] = info['ContractName']
        return info['ContractName']
    return None

########################################
# Cache for contract info (ABI, SourceCode, ContractName, ...)
########################################
CONTRACT_INFO_MAP = {}
def contract_info_clear(addr):
    CONTRACT_INFO_MAP[addr] = None
    contract_f = CACHE_DIR + '/contract/' +addr
    if os.path.exists(contract_f):
        os.remove(contract_f)

def contract_info(addr):
    if addr in CONTRACT_INFO_MAP:
        return CONTRACT_INFO_MAP[addr]

    contract_f = CACHE_DIR + '/contract/' +addr
    if os.path.exists(contract_f):
        with open(contract_f, 'r') as f:
            CONTRACT_INFO_MAP[addr] = info = json.loads(f.read())
            return info
    return None

def contract_info_set(addr, j):
    CONTRACT_INFO_MAP[addr] = j
    contract_f = CACHE_DIR + '/contract/' +addr
    with open(contract_f, 'w') as f:
        f.write(json.dumps(j))

########################################
# Cache for token info
########################################
TOKEN_INFO_MAP = {}
def token_cache_set(addr, symbol, name, decimals):
    info = {
            'symbol': symbol,
            'name':   name,
            'addr':   addr,
            'decimals':decimals
        }
    TOKEN_INFO_MAP[addr] = TOKEN_INFO_MAP[symbol] = info

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
    if addr_or_symbol in TOKEN_INFO_MAP:
        return TOKEN_INFO_MAP[addr_or_symbol]
    token_f = CACHE_DIR + '/token/' + addr_or_symbol + '.json'
    if Web3.isAddress(addr_or_symbol):
        token_f = CACHE_DIR + '/addr/' + addr_or_symbol + '.json'
    if os.path.exists(token_f):
        with open(token_f, 'r') as f:
            info = json.loads(f.read())
            TOKEN_INFO_MAP[addr_or_symbol] = info
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
            for l in f.readlines():
                txs.append(json.loads(l))
            if len(txs) >= kwargs.get('max') or 1000:
                break
    return txs # Sort txs again?

def addr_tx_append(addr, txs, from_blk, end_blk, **kwargs):
    # Defensive check.
    latest_cached_blk = -1 
    latest_cached_txs = addr_tx_get(addr, max=1)
    if len(latest_cached_txs) > 0:
        latest_cached_blk = int(latest_cached_txs[0]['blockNumber'])
    if latest_cached_blk >= from_blk:
        raise Exception("Latest blk in cached data", latest_cached_blk, "append", from_blk)
    if from_blk > end_blk:
        raise Exception("Append blk error", from_blk, end_blk)

    dir_p = CACHE_DIR + '/etherscan_tx_his/' + addr
    if os.path.exists(dir_p) is False:
        os.mkdir(dir_p)
    f_path = CACHE_DIR+'/etherscan_tx_his/'+addr+'/'+str(from_blk)+'.'+str(end_blk)+'.json'
    print("Append", len(txs), "TX to", addr, from_blk, '->', end_blk)
    with open(f_path, 'w') as f:
        for tx in txs:
            f.write(json.dumps(tx))
            f.write("\n")
