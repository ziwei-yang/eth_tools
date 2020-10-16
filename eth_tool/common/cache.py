import os
import json
import re
import datetime
from web3 import Web3

from .logger import log, debug, error

########################################
# Cache provides a layer for other components.
# Should not be called from outside.
########################################

ROOT_DIR = os.environ['ETH_TOOLS_DIR']
CACHE_DIR = ROOT_DIR + '/cache'
RES_DIR = ROOT_DIR + '/res'
DATA_DIR = ROOT_DIR + '/data'

for d in ['contract', 'addr', 'token', 'etherscan_tx_his', 'gas_tracker']:
    if os.path.exists(CACHE_DIR + '/' + d) is False:
        os.mkdir(CACHE_DIR + '/' + d)

CONTRACT_NAME_MAP = {}
CONTRACT_NAME_MAP_FILE = RES_DIR + '/export-verified-contractaddress-opensource-license.csv'
if os.path.exists(CONTRACT_NAME_MAP_FILE):
    debug("Loading contract addr-name")
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
                CONTRACT_NAME_MAP[Web3.toChecksumAddress(addr)] = name
    debug(len(CONTRACT_NAME_MAP), "contract addr-name load")
else:
    debug("No export-verified-contractaddress-opensource-license.csv found in res")

PUBLIC_TAG_MAP = {}
PUBLIC_TAG_FILE = DATA_DIR + '/tags'
if os.path.exists(PUBLIC_TAG_FILE):
    debug("Loading", PUBLIC_TAG_FILE)
    with open(PUBLIC_TAG_FILE, 'r') as f:
        for l in f.readlines():
            l = l.strip()
            if len(l) == 0 or l.startswith('#'):
                continue
            segs = l.split(' ')
            if len(segs) < 2:
                continue
            addr = Web3.toChecksumAddress(segs[0])
            if addr in PUBLIC_TAG_MAP:
                error("Duplicated address tag found", addr)
            PUBLIC_TAG_MAP[addr] = segs[1]
            PUBLIC_TAG_MAP[segs[1]] = addr

def tag_address(name):
    return PUBLIC_TAG_MAP.get(name)

def __import_contacts(files):
    addr_map = {}
    name_map = {}
    for f in files:
        if os.path.exists(f) == False:
            continue
        debug("Loading", f)
        with open(f, 'r') as fo:
            j = json.loads(fo.read())
            for name in j:
                ct = 0
                name_map[name] = list(map(lambda a: Web3.toChecksumAddress(a), j[name]))
                for addr in name_map[name]:
                    ct = ct + 1
                    if addr in addr_map:
                        error("Duplicated contact address found", addr)
                    addr_map[addr] = name + '#' + str(ct) + '-' + addr[0:6]
    return (addr_map, name_map)

CONTACT_ADDR_MAP, CONTACT_NAME_MAP = __import_contacts([
        DATA_DIR + '/contacts.json',
        DATA_DIR + '/trace_contacts.json'
    ])

def contact_addresses(name):
    return CONTACT_NAME_MAP.get(name)

def address_nametag(addr):
    addr = Web3.toChecksumAddress(addr)
    if addr in PUBLIC_TAG_MAP:
        return "tags/" + PUBLIC_TAG_MAP[addr]
    if addr in CONTACT_ADDR_MAP:
        return "contact/" + CONTACT_ADDR_MAP[addr]
    return None

########################################
# Cache for contract name
########################################
def contract_name(addr):
    addr = Web3.toChecksumAddress(addr)
    # Layer 1 cache
    if addr in CONTRACT_NAME_MAP:
        if CONTRACT_NAME_MAP[addr] == 'NULL':
            return None
        return CONTRACT_NAME_MAP[addr]
    # Layer 2 file cache
    info = contract_info(addr)
    if info is not None:
        if 'ContractName' in info:
            CONTRACT_NAME_MAP[addr] = info['ContractName']
            return info['ContractName']
    CONTRACT_NAME_MAP[addr] = 'NULL'
    return None

########################################
# Cache gas_tracker with timestamp.
########################################
def save_gas_tracker(data):
    t = datetime.datetime.now()
    utc = datetime.datetime.utcnow()
    t_str = t.strftime('%Y%m%d_%H%M%S')
    d = {
            'time_utc' : utc.timestamp(),
            'time_utc_str' : utc.strftime('%Y%m%d_%H%M%S'),
            'time' : t.timestamp(),
            'time_str' : t_str,
            'data' : data
        }
    data_f = CACHE_DIR + '/gas_tracker/' + t_str + '.json'
    debug("Saving gas_tracker file", t_str)
    with open(data_f, 'w') as f:
        f.write(json.dumps(d))

def last_gas_tracker():
    dir_p = CACHE_DIR + '/gas_tracker/'
    files = [f for f in os.listdir(dir_p) if re.match(r"^[0-9]{8}_[0-9]{6}.json$", f)]
    if len(files) == 0:
        return None
    files.sort(reverse=True) # From latest to oldest
    debug("Loading latest gas_tracker file", files[0])
    with open(dir_p + '/' + files[0], 'r') as f:
        return json.loads(f.read())

########################################
# Cache for contract info (ABI, SourceCode, ContractName, ...)
########################################
CONTRACT_INFO_MAP = {}
def contract_info_clear(addr):
    addr = Web3.toChecksumAddress(addr)
    CONTRACT_INFO_MAP[addr] = None
    contract_f = CACHE_DIR + '/contract/' +addr
    if os.path.exists(contract_f):
        os.remove(contract_f)

def contract_info(addr):
    addr = Web3.toChecksumAddress(addr)
    if addr in CONTRACT_INFO_MAP:
        return CONTRACT_INFO_MAP[addr]

    contract_f = CACHE_DIR + '/contract/' +addr
    if os.path.exists(contract_f):
        with open(contract_f, 'r') as f:
            CONTRACT_INFO_MAP[addr] = info = json.loads(f.read())
            return info
    return None

def contract_info_set(addr, j):
    addr = Web3.toChecksumAddress(addr)
    CONTRACT_INFO_MAP[addr] = j
    contract_f = CACHE_DIR + '/contract/' +addr
    with open(contract_f, 'w') as f:
        f.write(json.dumps(j))

########################################
# Cache for token info
########################################
TOKEN_INFO_MAP = {}
def token_cache_set(addr, symbol, name, decimals, **kwargs):
    addr = Web3.toChecksumAddress(addr)
    info = {
            'symbol': symbol,
            'name':   name,
            'addr':   addr,
            'decimals':decimals
        }
    for k in kwargs:
        info[k] = kwargs[k]
    TOKEN_INFO_MAP[addr] = TOKEN_INFO_MAP[symbol] = info

    addr_f = CACHE_DIR + '/addr/' + addr + '.json'
    symbol_f = CACHE_DIR + '/token/' + symbol.replace('/','_slash_') + '.json'
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
    token_f = None
    if Web3.isAddress(addr_or_symbol):
        addr_or_symbol = Web3.toChecksumAddress(addr_or_symbol)
        token_f = CACHE_DIR + '/addr/' + addr_or_symbol + '.json'
    else:
        token_f = CACHE_DIR + '/token/' + addr_or_symbol.replace('/', '_slash_') + '.json'
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
    addr = Web3.toChecksumAddress(addr)
    dir_p = CACHE_DIR + '/etherscan_tx_his/' + addr
    if os.path.exists(dir_p) is False:
        os.mkdir(dir_p)
    files = [f for f in os.listdir(dir_p) if re.match(r"^[0-9]{1,8}\.[0-9]{1,10}.json$", f)]
    files.sort(key=lambda f: int(f.split('.')[0]), reverse=True) # From latest to oldest
    # Parse from file until max reached.
    txs = []
    max_num = kwargs.get('max') or -1
    if len(files) == 0:
        debug("No file exists", "cache/etherscan_tx_his/"+addr)
    for f1 in files:
        with open(dir_p+'/'+f1, 'r') as f:
            for l in f.readlines():
                txs.append(json.loads(l))
            if max_num > 0 and len(txs) >= max_num:
                break
    return txs # Sort txs again?

def addr_tx_append(addr, txs, from_blk, end_blk, **kwargs):
    addr = Web3.toChecksumAddress(addr)
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
    debug("Append", len(txs), "TX to", addr, from_blk, '->', end_blk)
    with open(f_path, 'w') as f:
        for tx in txs:
            f.write(json.dumps(tx))
            f.write("\n")
