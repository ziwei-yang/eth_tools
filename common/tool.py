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

def contract_abi(addr):
    abi_file = root_dir+'/data/abi/'+addr
    if os.path.exists(abi_file):
        with open(abi_file, 'r') as f:
            return f.read()
    with open(abi_file, 'w') as f:
        abi = _etherscan_contract_abi(addr)
        f.write(abi)
        return abi

# For contract_abi() only.
def _etherscan_contract_abi(addr):
    print("Fetching ABI from etherscan", addr)
    url = 'https://api.etherscan.io/api?module=contract&action=getabi&address=' + addr + '&apikey=' + os.environ['ETHERSCAN_KEY']
    ret = requests.get(url)
    json = json.loads(ret.text)
    if json['status'] == 1:
        return json['result']
    raise Exception("Failed in GET " + url + "\n" + ret.text)

def get_contract(addr):
    if addr in internal_contract_cache:
        return internal_contract_cache[addr]
    contract = w3.eth.contract(address=addr, abi=contract_abi(addr))
    internal_contract_cache[addr] = contract
    return internal_contract_cache[addr]

def eth_call(contract_addr, func, *args):
    print("Call", contract_addr, func, args)
    ret = get_contract(contract_addr).functions[func](args).call()

def token_addr_to_symbol(addr):
    if addr in token_addr_to_symbol_cache:
        return token_addr_to_symbol_cache[addr]

    token_addr_f = root_dir+'/cache/addr.'+addr+'.json'
    if os.path.exists(token_addr_f) == False:
        symbol = eth_call(token_addr, 'symbol')
        with open(token_addr_f, 'w') as f:
            f.write('{"symbol":"'+symbol+'"}')
        symbol_f = root_dir+'/cache/symbol.'+symbol
        with open(symbol_f, 'w') as f:
            f.write(addr)

    with open(token_addr_f, 'r') as f:
        info = json.loads(f.read())
        token_addr_to_symbol_cache[addr] = info['symbol']
        return info['symbol']

def token_symbol_to_addr(symbol):
    if symbol in token_symbol_to_addr_cache:
        return token_symbol_to_addr_cache[symbol]
    # Always assume symbol file exists.
    symbol_f = root_dir+'/cache/symbol.'+symbol
    with open(token_addr_f, 'r') as f:
        return f.read()

def get_balance(addr, token_addr_list=[]):
    bal = { 'ETH' : Web3.fromWei(w3.eth.getBalance(addr), 'ether') }
    for token_addr in token_addr_list:
        ret = eth_call(token_addr, 'balanceOf', addr)
        bal[token_addr] = Web3.fromWei(ret, 'ether')
    return bal
