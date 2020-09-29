import unittest
from eth_tool.common import etherscan

class TestEtherscanAPI(unittest.TestCase):
    PICKLE_TOKEN = '0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5'
    CREAM_TOKEN = '0x2ba592F78dB6436527729929AAf6c908497cB200'
    BURN_ADDR = '0x000000000000000000000000000000000000dEaD'

#     def test_contract_abi(self):
#         etherscan.contract_abi(self.PICKLE_TOKEN)
#         self.assertEqual(len(txs) > 5, True)
# 
#     def test_tx_his(self):
#         txs = etherscan.addr_tx(self.BURN_ADDR)
#         self.assertEqual(len(txs) > 20, True)
# 
    def test_erc20_tx_his(self):
        txs = etherscan.addr_erc20_tx(self.BURN_ADDR)
        self.assertEqual(len(txs) > 20, True)
        for tx in txs[0:29]:
            print(etherscan.format_etherscan_erc20_tx(tx, self.BURN_ADDR))

if __name__ == '__main__':
    unittest.main()
