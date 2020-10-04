import unittest
from eth_tool.common import etherscan, cache, web3_eth

class TestEtherscanAPI(unittest.TestCase):
    PICKLE_TOKEN = '0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5'
    CREAM_TOKEN = '0x2ba592F78dB6436527729929AAf6c908497cB200'
    BURN_ADDR = '0x000000000000000000000000000000000000dEaD'

    def test_contract_info(self):
        info = etherscan.contract_info(self.PICKLE_TOKEN)
        print(self.PICKLE_TOKEN, 'name', info['ContractName'])
        abi_cached = web3_eth.contract_abi(self.PICKLE_TOKEN)
        self.assertEqual(info['ABI'], abi_cached)

    def test_tx_his(self):
        txs = etherscan._raw_addr_tx(self.BURN_ADDR, 0, max=100)
        self.assertEqual(len(txs) > 20, True)

    def test_erc20_tx_his(self):
        txs = etherscan._raw_addr_erc20_tx(self.BURN_ADDR, 0, max=100)
        self.assertEqual(len(txs) > 20, True)

    def test_tx_update(self):
        etherscan.addr_tx_update(self.BURN_ADDR, verbose=True)
        txs = cache.addr_tx_get(self.BURN_ADDR, max=20)
        self.assertEqual(len(txs) > 20, True)

if __name__ == '__main__':
    unittest.main()
