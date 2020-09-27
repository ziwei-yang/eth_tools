import os

from web3 import Web3
from web3.gas_strategies.time_based import medium_gas_price_strategy

w3 = Web3(Web3.HTTPProvider(
    'https://mainnet.infura.io/v3/' + os.environ['INFURA_ID']))
rootDir = os.environ['ETH_TOOLS_DIR']

print("Latest block number is :", w3.eth.blockNumber)
# print(w3.eth.getBlock('latest'))

# w3.eth.setGasPriceStrategy(medium_gas_price_strategy)
# print(w3.eth.generateGasPrice())

addr = '0xAC07e7b2BfBfAddB7a2D6e63C20a68Cc0b2fe10a'
print("Addr:", addr)
print("ETH:", Web3.fromWei(w3.eth.getBalance(addr), 'ether'))

def get_contract(addr):
    with open(rootDir+'/data/abi/'+addr, 'r') as f:
        abi = f.read()
        return w3.eth.contract(address=addr, abi=abi)


pickle_contract = get_contract('0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5')
ret = pickle_contract.functions['balanceOf'](addr).call()
pickle_bal = Web3.fromWei(ret, 'ether')
print("Pickle:", pickle_bal)
