import os
import re
import requests
import json

from . import cache

def is_verbose(kwargs):
    return kwargs.get('verbose') != False

def api(**kwargs):
    if is_verbose(kwargs):
        print("--> etherscan", kwargs.get('module'), kwargs.get('action'), kwargs.get('address'))
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

def contract_abi(addr, **kwargs):
    return api(module='contract', action='getabi', address=addr)

########################################
# tx querying for addr is expensive,
########################################
def addr_tx(addr, **kwargs):
    txs = cache.addr_tx_get(addr, **kwargs)
    if len(txs) == 0:
        addr_tx_update(addr, 0, **kwargs)

# Return any new TX got
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
    # Normal tx might not include erc20 events
    if is_verbose(kwargs):
        print("Get", len(normal_txs), "TX from", addr)
        print("Get", len(erc20_txs), "ERC20 events from", addr)
    max_blk = 0
    for tx in normal_txs: # Might match multiple erc_tx
        if int(tx['blockNumber']) >= max_blk:
            max_blk = int(tx['blockNumber'])
        match_erc20_txs = [erc_tx for erc_tx in erc20_txs if tx['hash'] == erc_tx['hash']]
        if len(match_erc20_txs) == 0:
            continue
        if is_verbose(kwargs):
            print("\t", len(match_erc20_txs), "ERC20 events", tx['hash'])
        events = []
        for erc_tx in match_erc20_txs:
            erc20_event = {}
            for k in ['from', 'to', 'value', 'tokenName', 'tokenSymbol', 'tokenDecimal']:
                erc20_event[k] = erc_tx[k]
            events.append(erc20_event)
        tx['_erc20_events'] = events
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
    return api(module='account', action='txlist', address=addr,
            startblock=from_blk, endblock=99999999, sort='desc')

# ERC20 event in etherscan:
# blockNumber timeStamp confirmations
# hash nonce blockHash
# gas gasPrice cumulativeGasUsed gasUsed
# from to ( of ERC20 )
# value ( of ERC20 )
# tokenName tokenSymbol tokenDecimal
def _raw_addr_erc20_tx(addr, from_blk, **kwargs):
    return api(module='account', action='tokentx', address=addr,
            startblock=from_blk, endblock=99999999, sort='desc')

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
    l = ["\t"]
    # From - To
    if addr is not None and addr.lower() == j['from'].lower():
        l.append('-->')
        l.append(j['to'])
    elif addr is not None and addr.lower() == j['to'].lower():
        l.append('<--')
        l.append(j['from'])
    else: # Should not happen
        l.append(j['from'])
        l.append(j['to'])
    # Gas price
    l.append('GAS'),
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

    # ERC20 events
    if '_erc20_events' not in j:
        return "\n".join(lines)
    for e in j['_erc20_events']:
        l = [
                "\t",
                e['tokenSymbol'].ljust(12),
                ("%.8f" % (int(e['value']) / (10**int(e['tokenDecimal'])))).ljust(20)
            ]
        if addr is not None and addr.lower() == e['from'].lower():
            l.append('-->')
            l.append(e['to'])
        elif addr is not None and addr.lower() == e['to'].lower():
            l.append('<--')
            l.append(e['from'])
        else: # Might happen in ERC20 event
            l.append(e['from'])
            l.append(e['to'])
        lines.append(' '.join(l))
    return "\n".join(lines)
