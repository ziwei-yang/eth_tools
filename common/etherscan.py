import os
import re
import requests
import json

from . import cache

def is_verbose(kwargs):
    return kwargs.get('verbose') != False

def api(**kwargs):
    if is_verbose(kwargs):
        print("--> etherscan", kwargs)
    kwargs['apikey'] = os.environ['ETHERSCAN_KEY']
    args = filter(lambda kv: kv[0] != 'verbose', kwargs.items())
    arg_str = '&'.join(
            map(lambda kv: str(kv[0]) + '=' + str(kv[1]), args)
            )
    kwargs.pop('apikey')
    url = 'https://api.etherscan.io/api?' + arg_str
    ret = requests.get(url)
    j = json.loads(ret.text)
    if j['status'] == "1":
        return j['result']
    elif j['status'] == "0" and j['message'] == 'No transactions found':
        return j['result']
    raise Exception("Failed in GET", url, "status:", j['status'],"\n", ret.text)

# ABI only
def contract_abi(addr, **kwargs):
    return api(module='contract', action='getabi', address=addr)

# Fetch below data for contract:
# SourceCode
# ABI
# ContractName
# CompilerVersion
# ConstructorArguments
# SwarmSource
def contract_info(addr, **kwargs):
    info = api(module='contract', action='getsourcecode', address=addr)
    return info[0]

########################################
# tx querying for addr is expensive,
########################################
def addr_tx(addr, **kwargs):
    txs = cache.addr_tx_get(addr, **kwargs)
    if len(txs) == 0:
        addr_tx_update(addr, 0, **kwargs)

# Query normal + internal + erc20 TX and merge them.
def addr_tx_update(addr, **kwargs):
    latest_cached_blk = -1
    latest_cached_txs = cache.addr_tx_get(addr, max=1)
    if len(latest_cached_txs) > 0:
        latest_cached_blk = latest_cached_txs[0]['blockNumber']
    from_blk = int(latest_cached_blk) + 1
    if is_verbose(kwargs):
        print("Update TX for", addr, "from", from_blk)

    normal_txs = _raw_addr_tx(addr, from_blk, **kwargs)
    if len(normal_txs) == 0:
        if is_verbose(kwargs):
            print("Get", len(normal_txs), "TX from", addr)
        return []

    erc20_txs = _raw_addr_erc20_tx(addr, from_blk, **kwargs)
    internal_txs = _raw_addr_internal_tx(addr, from_blk, **kwargs)

    # Normal tx might not include erc20 events
    if is_verbose(kwargs):
        print("Get", len(normal_txs), "TX from", addr)
        print("Get", len(erc20_txs), "ERC20 events")
        print("Get", len(internal_txs), "internal events")
    max_blk = 0
    for tx in normal_txs: # Might match multiple erc_tx
        if int(tx['blockNumber']) >= max_blk:
            max_blk = int(tx['blockNumber'])
        match_erc20_txs = [erc_tx for erc_tx in erc20_txs if tx['hash'] == erc_tx['hash']]
        if is_verbose(kwargs) and len(match_erc20_txs) > 0:
            print("\t", len(match_erc20_txs), "ERC20 events", tx['hash'])
        events = []
        for erc_tx in match_erc20_txs:
            erc20_event = {}
            for k in ['from', 'to', 'value', 'tokenName', 'tokenSymbol', 'tokenDecimal']:
                erc20_event[k] = erc_tx[k]
            events.append(erc20_event)
        tx['_erc20_events'] = events

        match_int_txs = [int_tx for int_tx in internal_txs if tx['hash'] == int_tx['hash']]
        if is_verbose(kwargs) and len(match_int_txs) > 0:
            print("\t", len(match_int_txs), "internal events", tx['hash'])
        events = []
        for int_tx in match_int_txs:
            int_event = {}
            for k in ['from', 'to', 'value', 'isError', 'input', 'contractAddress']:
                int_event[k] = int_tx[k]
            events.append(int_event)
        tx['_internal_txs'] = events

    # Save TX into cache.
    cache.addr_tx_append(addr, normal_txs, from_blk, max_blk, **kwargs)
    return normal_txs

# Normal TX in etherscan:
# blockNumber timeStamp confirmations
# hash nonce blockHash
# gas gasPrice cumulativeGasUsed gasUsed
# transactionIndex
# from to
# value ( of ETH )
# isError '0'
# txreceipt_status '1' confirmed
# input ( message )
# contractAddress
def _raw_addr_tx(addr, from_blk, **kwargs):
    all_txs = []
    to_blk = 99999999
    while to_blk is not None:
        txs = api(module='account', action='txlist', address=addr,
                startblock=from_blk, endblock=to_blk, sort='desc')
        trimmed_txs, to_blk = _check_if_tx_reach_limit(txs)
        all_txs = all_txs + trimmed_txs
        if 'max' in kwargs:
            if kwargs['max'] <= len(all_txs):
                break
    return all_txs

# ERC20 event in etherscan:
# blockNumber timeStamp confirmations
# hash nonce blockHash
# gas gasPrice cumulativeGasUsed gasUsed
# from to ( of ERC20 )
# value ( of ERC20 )
# tokenName tokenSymbol tokenDecimal
def _raw_addr_erc20_tx(addr, from_blk, **kwargs):
    all_txs = []
    to_blk = 99999999
    while to_blk is not None:
        txs = api(module='account', action='tokentx', address=addr,
                startblock=from_blk, endblock=to_blk, sort='desc')
        trimmed_txs, to_blk = _check_if_tx_reach_limit(txs)
        all_txs = all_txs + trimmed_txs
        if 'max' in kwargs:
            if kwargs['max'] <= len(all_txs):
                break
    return all_txs

# Internal event in etherscan:
# blockNumber timeStamp
# hash
# gas gasUsed
# from to ( of ETH )
# value ( of ETH )
# isError '0'
# input ( message )
# contractAddress
def _raw_addr_internal_tx(addr, from_blk, **kwargs):
    all_txs = []
    to_blk = 99999999
    while to_blk is not None:
        txs = api(module='account', action='txlistinternal', address=addr,
                startblock=from_blk, endblock=to_blk, sort='desc')
        trimmed_txs, to_blk = _check_if_tx_reach_limit(txs)
        all_txs = all_txs + trimmed_txs
        if 'max' in kwargs:
            if kwargs['max'] <= len(all_txs):
                break
    return all_txs

# Assume TX list is ordered by nonce+blockNUmber, desc
# Returns up to a maximum of the last 10000 transactions only
# Return (Trimed TX list, next query end_blk)
def _check_if_tx_reach_limit(txs):
    if len(txs) < 10000:
        return (txs, None)
    oldest_blk = int(txs[-1]['blockNumber'])
    trimmed_txs = list(filter(lambda tx: int(tx['blockNumber']) > oldest_blk, txs))
    print("Etherscan result reached max 10000, trimmed to", len(trimmed_txs), "oldest blk", oldest_blk)
    return (trimmed_txs, oldest_blk)

from datetime import datetime
from web3 import Web3
def format_tx(j, addr=None):
    offset = 8 # GMT+8
    # Time
    l = [
            datetime.utcfromtimestamp(offset*3600+int(j['timeStamp'])).strftime('%Y%m%d %H:%M:%S'),
            '+0800',
            j['hash']
        ]
    lines = [' '.join(l)]
    if int(j['value']) > 0:
        l = [
                "\t",
                'ETH'.ljust(12),
                ("%.8f" % (Web3.fromWei(int(j['value']), 'ether'))).ljust(20)
            ]
    else:
        l = [
                "\t",
                ''.ljust(12),
                ''.ljust(20)
            ]
    # From - To
    if addr is not None and addr.lower() == j['from'].lower():
        l.append('-->')
        l.append(render_addr(j['to']))
    elif addr is not None and addr.lower() == j['to'].lower():
        l.append('<--')
        l.append(render_addr(j['from']))
    else: # Should not happen
        l.append(render_addr(j['from']))
        l.append(render_addr(j['to']))
    # Gas price
    l.append('Gas')
    l.append(str(Web3.fromWei(int(j['gasPrice']), 'gwei')).ljust(5))
    # Status
    if j['isError'] == '0':
        if j['txreceipt_status'] == '1':
            l.append(' ')
        else:
            l.append('…')
    else:
        l.append('X')
    lines.append(' '.join(l))

    if len(j['contractAddress']) > 0:
        lines.append('Contract '+j['contractAddress'])

    # lines.append(json.dumps(j)) # Debug

    # ERC20 events
    for e in j['_erc20_events']:
        l = [
                "\t",
                e['tokenSymbol'].ljust(12),
                ("%.8f" % (int(e['value']) / (10**int(e['tokenDecimal'])))).ljust(20)
            ]
        if addr is not None and addr.lower() == e['from'].lower():
            l.append('-->')
            l.append(render_addr(j['to']))
        elif addr is not None and addr.lower() == e['to'].lower():
            l.append('<--')
            l.append(render_addr(j['from']))
        else: # Might happen in ERC20 event
            l.append(render_addr(j['from']))
            l.append(render_addr(j['to']))
        lines.append(' '.join(l))

    # Internal transactions
    for e in j['_internal_txs']:
        l = [
                "\t",
                'ETH'.ljust(12),
                ("%.8f" % (Web3.fromWei(int(e['value']), 'ether'))).ljust(20)
            ]
        if addr is not None and addr.lower() == e['from'].lower():
            l.append('-->')
            l.append(render_addr(j['to']))
        elif addr is not None and addr.lower() == e['to'].lower():
            l.append('<--')
            l.append(render_addr(j['from']))
        else: # Might happen in ERC20 event
            l.append(render_addr(j['from']))
            l.append(render_addr(j['to']))
        # Status
        if e['isError'] == '0':
            l.append(' ')
        else:
            l.append('X')
        lines.append(' '.join(l))

    return "\n".join(lines)

def render_addr(addr):
    if cache.contract_name(addr) is not None:
        return cache.contract_name(addr).ljust(len(addr))
    return addr
