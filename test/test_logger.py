import unittest
from eth_tool.common import logger

class TestLogger(unittest.TestCase):
    def test_token_info(self):
        ret = logger.log('logger', 'test')
        self.assertEqual(ret[1:4], ['test_logger:6', 'logger', 'test'])
        logger.log('logger', 'test', color='blue')
        logger.log('logger', 'test', color='red')
        logger.log('logger', 'test', color='on_green')

    def test_color(self):
        s = logger.green('GREEN')
        print(s)
        s = logger.on_green('ON GREEN')
        print(s)

if __name__ == '__main__':
    unittest.main()
