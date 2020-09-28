import os
import requests
import json
from web3 import Web3

w3 = Web3(Web3.HTTPProvider(
    'https://mainnet.infura.io/v3/' + os.environ['INFURA_ID']))
root_dir = os.environ['ETH_TOOLS_DIR']

internal_contract_cache = {}

token_symbol_to_addr_cache = {}
token_addr_to_symbol_cache = {}

def is_verbose(**kwargs):
    return kwargs.get('verbose') != False

def clear_abi_cache(addr):
    abi_file = root_dir+'/data/abi/'+addr
    if os.path.exists(abi_file):
        os.remove(abi_file)

def contract_abi(addr, **kwargs):
    abi_file = root_dir+'/data/abi/'+addr
    if os.path.exists(abi_file):
        with open(abi_file, 'r') as f:
            return f.read()
    with open(abi_file, 'w') as f:
        abi = _etherscan_contract_abi(addr, **kwargs)
        f.write(abi)
        return abi

# For contract_abi() only.
def _etherscan_contract_abi(addr, **kwargs):
    if is_verbose(**kwargs):
        print("--> Fetching ABI from etherscan", addr)
    url = 'https://api.etherscan.io/api?module=contract&action=getabi&address=' + addr + '&apikey=' + os.environ['ETHERSCAN_KEY']
    ret = requests.get(url)
    j = json.loads(ret.text)
    if j['status'] == "1":
        return j['result']
    raise Exception("Failed in GET", url, "status:", j['status'],"\n", ret.text)

def get_contract(addr):
    if addr in internal_contract_cache:
        return internal_contract_cache[addr]
    contract = w3.eth.contract(address=addr, abi=contract_abi(addr))
    internal_contract_cache[addr] = contract
    return internal_contract_cache[addr]

def call_contract(contract_addr, func, *args, **kwargs):
    if contract_addr in token_addr_to_symbol_cache:
        symbol = token_addr_to_symbol_cache[contract_addr]
        if is_verbose(**kwargs):
            print("Call", symbol, func, *args)
    else:
        if is_verbose(**kwargs):
            print("Call", contract_addr, func, *args)
    return get_contract(contract_addr).functions[func](*args).call()

def token_symbol(addr, **kwargs):
    if addr in token_addr_to_symbol_cache:
        return token_addr_to_symbol_cache[addr]

    token_addr_f = root_dir+'/cache/addr.'+addr+'.json'
    if os.path.exists(token_addr_f) == False:
        symbol = call_contract(addr, 'symbol', **kwargs)
        with open(token_addr_f, 'w') as f:
            f.write('{"symbol":"'+symbol+'"}')
        symbol_f = root_dir+'/cache/symbol.'+symbol
        with open(symbol_f, 'w') as f:
            f.write(addr)

    with open(token_addr_f, 'r') as f:
        info = json.loads(f.read())
        token_addr_to_symbol_cache[addr] = info['symbol']
        return info['symbol']

def token_addr(symbol):
    if symbol in token_symbol_to_addr_cache:
        return token_symbol_to_addr_cache[symbol]
    # Always assume symbol file exists.
    symbol_f = root_dir+'/cache/symbol.'+symbol
    with open(symbol_f, 'r') as f:
        return f.read()

def token_balance(addr_or_name, addr, **kwargs):
    t_addr = addr_or_name
    if Web3.isAddress(addr_or_name):
        token_symbol(addr_or_name, **kwargs) # Cache symbol <-> balance map
    else: # name as arg
        t_addr = token_addr(addr_or_name)
    ret = call_contract(t_addr, 'balanceOf', addr, **kwargs)
    return Web3.fromWei(ret, 'ether')

def scan_balance(addr, token_addr_or_name=[], **kwargs):
    bal = { 'ETH' : Web3.fromWei(w3.eth.getBalance(addr), 'ether') }
    for addr_or_name in token_addr_or_name:
        b = token_balance(addr_or_name, addr, **kwargs)
        bal[addr_or_name] = b
        if Web3.isAddress(addr_or_name): # Also write as symbol
            bal[token_symbol(addr_or_name)] = b
    return bal

def print_balance(addr, token_addr_or_name=[]):
    bal_map = scan_balance(addr, token_addr_or_name)
    print('----', 'Bal', addr, '----')
    for k in bal_map:
        if Web3.isAddress(k) == False:
            print(k.ljust(12), bal_map[k])
