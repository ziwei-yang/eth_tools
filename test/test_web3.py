import unittest
from eth_tool.common import web3_eth, cache

class TestStringMethods(unittest.TestCase):
    PICKLE_TOKEN = '0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5'
    CREAM_TOKEN = '0x2ba592F78dB6436527729929AAf6c908497cB200'
    BURN_ADDR = '0x000000000000000000000000000000000000dEaD'

    def test_token_info(self):
        symbol = web3_eth.call_contract(self.PICKLE_TOKEN, 'symbol')
        self.assertEqual(symbol, 'PICKLE')
        self.assertEqual(cache.token_cache_get(self.PICKLE_TOKEN)['symbol'], 'PICKLE')

    def test_token_balance(self):
        bal_raw = web3_eth.call_contract(self.PICKLE_TOKEN, 'balanceOf', self.BURN_ADDR)
        bal = web3_eth.token_balance(self.PICKLE_TOKEN, self.BURN_ADDR)
        decimals = cache.token_cache_get(self.PICKLE_TOKEN)['decimals']
        self.assertEqual(bal_raw/(10**decimals), bal)

        bal_map_1 = web3_eth.scan_balance(self.BURN_ADDR, [self.PICKLE_TOKEN, self.CREAM_TOKEN])
        bal_map_2 = web3_eth.scan_balance(self.BURN_ADDR, ['PICKLE', 'CREAM'])
        for k in ['ETH', 'PICKLE', 'CREAM']:
            self.assertEqual(bal_map_1[k], bal_map_2[k])
        web3_eth.print_balance(self.BURN_ADDR, [self.PICKLE_TOKEN, self.CREAM_TOKEN])

if __name__ == '__main__':
    unittest.main()
