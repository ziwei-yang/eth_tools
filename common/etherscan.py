import os
import requests
import json

def is_verbose(**kwargs):
    return kwargs.get('verbose') != False

def api(**kwargs):
    if is_verbose(**kwargs):
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
    raise Exception("Failed in GET", url, "status:", j['status'],"\n", ret.text)

def contract_abi(addr, **kwargs):
    return api(module='contract', action='getabi', address=addr)

def addr_tx(addr, **kwargs):
    return api(module='account', action='txlist', address=addr,
            startblock=0, endblock=99999999, sort='desc')

def addr_erc20_tx(addr, **kwargs):
    return api(module='account', action='tokentx', address=addr,
            startblock=0, endblock=99999999, sort='desc')

from datetime import datetime
def format_etherscan_erc20_tx(json):
    offset = 8*3600 # GMT+8
    l = [
            datetime.utcfromtimestamp(offset+int(json['timeStamp'])).strftime('%Y%m%d %H:%M:%S'),
            json['tokenSymbol'].ljust(12),
            ("%.8f" % (int(json['value']) / (10**int(json['tokenDecimal'])))).ljust(20),
            json['from'],
            json['to']
        ]
    return ' '.join(l)
