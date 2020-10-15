import os
import requests
import json
import datetime
import time
from web3 import Web3

from . import cache, logger, webbrowser
from .logger import log, debug, error

def is_verbose(kwargs):
    return kwargs.get('verbose') != False

def api(**kwargs):
    if is_verbose(kwargs):
        debug("--> etherscan", kwargs)
    kwargs['apikey'] = os.environ['ETHERSCAN_KEY']
    args = filter(lambda kv: kv[0] != 'verbose', kwargs.items())
    arg_str = '&'.join(
            map(lambda kv: str(kv[0]) + '=' + str(kv[1]), args)
            )
    kwargs.pop('apikey')
    url = 'https://api.etherscan.io/api?' + arg_str
    ret = requests.get(url)
    j = json.loads(ret.text)
    debug('<-- etherscan', j['status'], j['message'])
    if j['status'] == "1":
        return j['result']
    elif j['status'] == "0":
        if j['message'] == 'No transactions found':
            return j['result']
        if j['message'].startswith('Query Timeout'): # Retry
            return api(**kwargs)
    raise Exception("Failed in GET", url, "status:", j['status'],"\n", ret.text)

# ABI only, use contract_info() instead.
# def contract_abi(addr, **kwargs):
#     return api(module='contract', action='getabi', address=addr)

# Fetch below data for contract:
# SourceCode
# ABI
# ContractName
# CompilerVersion
# ConstructorArguments
# SwarmSource
def contract_info(addr, **kwargs):
    contract_info = cache.contract_info(addr)
    if contract_info is not None:
        if len(contract_info) == 0: # Queried but no result.
            return None
        return contract_info
    info = api(module='contract', action='getsourcecode', address=addr)
    if len(info) == 0: # Queried but no result.
        cache.contract_info_set(addr, {})
        return None
    info = info[0]
    if len(info['SourceCode']) == 0: # Contract source code not verified.
        cache.contract_info_set(addr, {})
        return None
    cache.contract_info_set(addr, info)
    return info

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
        debug("Update TX for", addr, "from", from_blk)

    normal_txs = _raw_addr_tx(addr, from_blk, **kwargs)
    if len(normal_txs) == 0:
        if is_verbose(kwargs):
            debug("Get", len(normal_txs), "TX from", addr)
        return []

    erc20_txs = _raw_addr_erc20_tx(addr, from_blk, **kwargs)
    internal_txs = _raw_addr_internal_tx(addr, from_blk, **kwargs)

    # Normal tx might not include erc20 events
    # ERC20 events and internal TXs might not be in normal TXs
    if is_verbose(kwargs):
        debug("Get", len(normal_txs), "TX from", addr)
        debug("Get", len(erc20_txs), "ERC20 events")
        debug("Get", len(internal_txs), "internal events")

    tx_by_hash = {} # Collect all info for TX
    # Scan normal_txs, then erc20_txs and internal_txs to make sure max info is extract for TX.
    for tx in normal_txs:
        tx_by_hash[tx['hash']] = tx
    for erc20_tx in erc20_txs:
        i = erc20_tx['hash']
        normal_tx = {}
        if i not in tx_by_hash: # Extract basic TX info.
            for k in ['blockNumber', 'timeStamp', 'confirmations', 'hash',
                'nonce', 'blockHash', 'gas', 'gasPrice', 'cumulativeGasUsed',
                'gasUsed']:
                normal_tx[k] = erc20_tx[k]
            tx_by_hash[i] = normal_tx
        else:
            normal_tx = tx_by_hash[i]
        # Append data into _erc20_events
        if '_erc20_events' not in normal_tx:
            normal_tx['_erc20_events'] = []
        erc20_event = {}
        for k in ['from', 'to', 'value', 'tokenName', 'tokenSymbol', 'tokenDecimal', 'contractAddress']:
            erc20_event[k] = erc20_tx[k]
        normal_tx['_erc20_events'].append(erc20_event)
    for int_tx in internal_txs:
        i = int_tx['hash']
        normal_tx = {}
        if i not in tx_by_hash: # Extract basic TX info.
            for k in ['blockNumber', 'timeStamp', 'hash', 'gas', 'gasUsed']:
                normal_tx[k] = int_tx[k]
            tx_by_hash[i] = normal_tx
        else:
            normal_tx = tx_by_hash[i]
        # Append data into _erc20_events
        if '_internal_txs' not in normal_tx:
            normal_tx['_internal_txs'] = []
        int_event = {}
        for k in ['from', 'to', 'value', 'isError', 'input', 'contractAddress']:
            int_event[k] = int_tx[k]
        normal_tx['_internal_txs'].append(int_event)

    # Sort normal_tx by blockNumber
    txs = sorted(tx_by_hash.values(), key=lambda tx: int(tx['blockNumber']))

    # Save txs each 1000 per file.
    ct = 0
    max_blk = from_blk
    ttl_save_txs = [] # Order by timestamp desc.
    save_txs = [] # Order by timestamp asc until reversed.
    for tx in txs:
        ct = ct + 1
        if int(tx['blockNumber']) == max_blk:
            save_txs.append(tx) # Keep saving TX in same block.
            continue
        elif int(tx['blockNumber']) < max_blk:
            raise Exception("tx should be sorted by blockNumber")
        # Larger blockNumber happened, save to cache if needed.
        max_blk = int(tx['blockNumber'])
        if ct >= 1000:
            save_txs.reverse()
            cache.addr_tx_append(addr, save_txs, int(save_txs[0]['blockNumber']), max_blk, **kwargs)
            ttl_save_txs = save_txs + ttl_save_txs
            save_txs = []
            ct = 0
        save_txs.append(tx)
    # Save last batch.
    if ct > 0:
        save_txs.reverse()
        cache.addr_tx_append(addr, save_txs, int(save_txs[0]['blockNumber']), max_blk, **kwargs)
        ttl_save_txs = save_txs + ttl_save_txs

    return ttl_save_txs

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
# tokenName tokenSymbol tokenDecimal contractAddress
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
    debug("Etherscan result reached max 10000, trimmed to", len(trimmed_txs), "oldest blk", oldest_blk)
    return (trimmed_txs, oldest_blk)

def involved_tokens(tx_list):
    tokens = {}
    for j in tx_list:
        if '_erc20_events' not in j:
            continue
        for e in j['_erc20_events']:
            contract = Web3.toChecksumAddress(e['contractAddress'])
            if contract in tokens:
                continue
            tokens[contract] = {}
            for k in ['tokenName', 'tokenSymbol', 'tokenDecimal', 'contractAddress']:
                tokens[contract][k] = e[k]
            tokens[contract]['tokenDecimal'] = int(tokens[contract]['tokenDecimal'])
            cache.token_cache_set(contract, e['tokenSymbol'], e['tokenName'], int(e['tokenDecimal']))
    return tokens

def tx_tokens(tx):
    if '_erc20_events' not in tx:
        return []
    return list(set(map(lambda e: e['tokenSymbol'], tx['_erc20_events'])))

def tx_token_value(tx, token):
    if '_erc20_events' not in tx:
        return 0
    value = 0
    decimals = None
    for e in tx['_erc20_events']:
        if e['tokenSymbol'] == token:
            value = value + int(e['value'])
            decimals = e['tokenDecimal']
    if value == 0:
        return 0
    return value / (10**int(e['tokenDecimal']))

# Return a hashmap contains:
# { addr: net_value }
# Mark value as positive if is transferred to addr
def tx_token_netvalue(tx, token, **kwargs):
    if '_erc20_events' not in tx:
        return {}
    net_value_map = kwargs.get('net_value_map') or {}
    decimals = None
    for e in tx['_erc20_events']:
        if e['tokenSymbol'] == token:
            from_addr = Web3.toChecksumAddress(e['from'])
            to_addr = Web3.toChecksumAddress(e['to'])
            decimals = decimals or e['tokenDecimal']
            value = int(e['value']) / (10**int(decimals))
            net_value_map[from_addr] = 0 - value + (net_value_map.get(from_addr) or 0)
            net_value_map[to_addr] = value + (net_value_map.get(to_addr) or 0)
    return net_value_map

# Return [(SYMBOL, ±value, from/to), ...]
# Extract transfer info from TX when:
# TX is for sending ETH
# TX is for transferring ERC20
# Value is positive when addr <-- from_addr
# Value is negative when addr --> to_addr
# If kwargs[mode] is 'peer':
#   Only returns info that seems to be a single xfr between peers,
#   Discard when multiple xfr happens.
#   Discard when from/to is a contract.
def tx_xfr_info(tx, addr, **kwargs):
    addr = Web3.toChecksumAddress(addr)
    info = []
    if 'value' in tx and int(tx['value']) > 0:
        v = Web3.fromWei(int(tx['value']), 'ether')
        if addr == Web3.toChecksumAddress(tx['from']):
            info.append(['ETH', 0-v, tx['to']])
        elif addr == Web3.toChecksumAddress(tx['to']):
            info.append(['ETH', v, tx['from']])
    # ERC20 events
    for e in tx.get('_erc20_events') or []:
        v = int(e['value']) / (10**int(e['tokenDecimal']))
        if addr == Web3.toChecksumAddress(e['from']):
            info.append([e['tokenSymbol'], 0-v, e['to']])
        elif addr == Web3.toChecksumAddress(e['to']):
            info.append([e['tokenSymbol'], v, e['from']])
    # Internal transactions
    for e in tx.get('_internal_txs') or []:
        v = Web3.fromWei(int(e['value']), 'ether')
        if addr == Web3.toChecksumAddress(e['from']):
            info.append(['ETH', 0-v, e['to']])
        elif addr == Web3.toChecksumAddress(e['to']):
            info.append(['ETH', v, e['from']])
    # Filter by mode.
    if kwargs.get('mode') == 'peer':
        if tx.get('input') == '0x': # ETH xfr only.
            return info
        if len(info) is not 1:
            return []
        if contract_info(info[0][2]) is not None:
            return [] # Skip when receiver is a contract.
        return info
    return info

def format_tx(j, addr=None, **kwargs):
    # Time
    l = [
            datetime.datetime.utcfromtimestamp(int(j['timeStamp'])-time.timezone).strftime('%Y%m%d %H:%M:%S'),
            j['hash']
        ]
    lines = [' '.join(l)]

    if addr is not None:
        addr = Web3.toChecksumAddress(addr)
        if kwargs.get('show_owner') is True:
            lines.append(render_addr(addr))

    if 'value' in j and int(j['value']) > 0:
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
    if 'from' not in j or 'to' not in j:
        l.append('? --> ?')
    elif addr is not None:
        if addr.lower() == j['from'].lower() and addr.lower() == j['to'].lower():
            if j.get('input') == '0x':
                l.append('-x-')
                l.append('SELF cancel TX'.ljust(len(addr)))
            else:
                l.append('---')
                l.append('SELF'.ljust(len(addr)))
        elif addr is not None and addr.lower() == j['from'].lower():
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
    if 'gasPrice' in j:
        l.append(str(Web3.fromWei(int(j['gasPrice']), 'gwei')).ljust(5))
    else:
        l.append(logger.on_red('??'.ljust(5)))
    # Status
    is_error = False
    if 'isError' not in j:
        l.append(' ')
    elif j['isError'] == '0':
        if j['txreceipt_status'] == '1':
            l.append(' ')
        else:
            l.append('…')
    else:
        l.append('X')
        is_error = True
    lines.append(' '.join(l))
    if is_error:
        lines = list(map(lambda s: logger.red(s), lines))

    if 'contractAddress' in j and len(j['contractAddress']) > 0:
        lines.append('Contract '+j['contractAddress'])

    # lines.append(json.dumps(j)) # Debug

    # ERC20 events
    for e in j.get('_erc20_events') or []:
        l = [
                "\t",
                e['tokenSymbol'].ljust(12),
                ("%.8f" % (int(e['value']) / (10**int(e['tokenDecimal'])))).ljust(20)
            ]
        if addr is not None and addr.lower() == e['from'].lower():
            l.append('-->')
            l.append(render_addr(e['to']))
        elif addr is not None and addr.lower() == e['to'].lower():
            l.append('<--')
            l.append(render_addr(e['from']))
            # Render incoming in green
            l = list(map(lambda s: logger.light_green(s), l))
        else: # Might happen in ERC20 event
            l.append(render_addr(e['from']))
            l.append(render_addr(e['to']))
        lines.append(' '.join(l))

    # Internal transactions
    for e in j.get('_internal_txs') or []:
        l = [
                "\t",
                'ETH'.ljust(12),
                ("%.8f" % (Web3.fromWei(int(e['value']), 'ether'))).ljust(20)
            ]
        if addr is not None and addr.lower() == e['from'].lower():
            l.append('-->')
            l.append(render_addr(e['to']))
        elif addr is not None and addr.lower() == e['to'].lower():
            l.append('<--')
            l.append(render_addr(e['from']))
            # Render incoming in green
            l = list(map(lambda s: logger.light_green(s), l))
        else: # Might happen in ERC20 event
            l.append(render_addr(e['from']))
            l.append(render_addr(e['to']))
        # Status
        if e['isError'] == '0':
            l.append(' ')
        else:
            l.append('X')
        lines.append(' '.join(l))

    return "\n".join(lines)

def render_addr(addr):
    if addr == '0x0000000000000000000000000000000000000000':
        return '0x00'
    if addr == '0x0000000000000000000000000000000000000001':
        return '0x01'
    if cache.contract_name(addr) is not None:
        if len(cache.contract_name(addr)) > 0:
            return (cache.contract_name(addr) + " " + addr[0:10]).ljust(len(addr))
    info = contract_info(addr)
    if info is not None:
        if info['ContractName'] is not None:
            if len(info['ContractName']) > 0:
                return info['ContractName']
    addr = Web3.toChecksumAddress(addr)
    tag = cache.address_nametag(addr)
    if tag is not None:
        return logger.reverse(tag.ljust(42))
    return addr

########################################
# Gas Tracker and other data that could only got in browser.
########################################
def __gas_tracker_parser(browser, **kwargs):
    status = kwargs.get("status_data") or {}
    ui = kwargs.get("ui")
    by = kwargs.get("by")
    webdriver = kwargs.get("webdriver")
    
    page_no = status.get("page_no") or 1
    # Find 'Next' link
    el_list = browser.find_elements_by_xpath("//*/a[@class='page-link']")
    select_els = list(filter(lambda e: e.text == "Next", el_list))
    if len(select_els) != 1:
        status["error"] = "To many/less <a class='page-link'> elements " + str(len(select_els))
        return (True, status)

    # Parse records.
    rows = browser.find_elements_by_xpath("//*/table[@id='mytable']/tbody/tr[@role='row']/td[2]")
    data = status.get("data") or []
    for r in rows:
        href_els = r.find_elements(by.TAG_NAME, 'a')
        if len(href_els) != 1:
            error("Too many/less href for", r.text)
            continue
        href = href_els[0].get_attribute('href')
        if href.startswith('https://etherscan.io/address/') is not True:
            error("Unexpected href", href, 'for', r.text)
            continue
        address = href.split('https://etherscan.io/address/')[1]
        data.append([r.text, address])
        debug(r.text.ljust(44), address)
    status['data'] = data

    if page_no > 3:
        return (True, status)
    status['page_no'] = (page_no + 1)
    # Scroll down
    webbrowser.move_to_element(browser, select_els[0])
    time.sleep(1)
    # Click 'Next'
    webdriver.ActionChains(browser).click_and_hold(select_els[0]).perform()
    webdriver.ActionChains(browser).release().perform()
    return (False, status)

# Better use gas_tracker_or_cached() for faster response with cache support.
def gas_tracker():
    ret, data = webbrowser.render_with_firefox(
            "https://etherscan.io/gasTracker",
            block=__gas_tracker_parser
            )
    if data.get("error") is None:
        return data['data']
    raise Exception(data["error"])

def gas_tracker_or_cached(max_diff_seconds=1200):
    utcnow = datetime.datetime.utcnow()
    data = cache.last_gas_tracker()
    need_update = True
    if data is not None:
        last_t = data['time_utc']
        diff_sec = utcnow.timestamp() - last_t
        if diff_sec <= max_diff_seconds:
            need_update = False
    if need_update:
        cache.save_gas_tracker(gas_tracker())
        data = cache.last_gas_tracker()
    return data
