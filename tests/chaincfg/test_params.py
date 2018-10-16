import unittest
import chaincfg
from chaincfg.params import *

mockNetParams = Params(
    name="mocknet",
    net=(1 << 32) - 1,
    pub_key_hash_addr_id=0x9f,
    script_hash_addr_id=0xf9,
    bech32_hrp_segwit="tc",
    hd_private_key_id=bytes([0x01, 0x02, 0x03, 0x04]),
    hd_public_key_id=bytes([0x05, 0x06, 0x07, 0x08]),

)


class TestParams(unittest.TestCase):
    def test_register(self):
        self.tests = [
            {
                "name": "default networks",
                "register": [
                    {
                        "name": "duplicate mainnet",
                        "params": MainNetParams,
                        "err": ErrDuplicateNet,
                    },
                    {
                        "name": "duplicate regtest",
                        "params": RegressionNetParams,
                        "err": ErrDuplicateNet,
                    },
                    {
                        "name": "duplicate testnet3",
                        "params": TestNet3Params,
                        "err": ErrDuplicateNet,
                    },
                    {
                        "name": "duplicate simnet",
                        "params": SimNetParams,
                        "err": ErrDuplicateNet,
                    },
                ],
                "p2pkhMagics": [
                    {
                        "magic": MainNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": TestNet3Params.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": RegressionNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": SimNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": mockNetParams.pub_key_hash_addr_id,
                        "valid": False,
                    },
                    {
                        "magic": 0xFF,
                        "valid": False,
                    },
                ],
                "p2shMagics": [
                    {
                        "magic": MainNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": TestNet3Params.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": RegressionNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": SimNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": mockNetParams.script_hash_addr_id,
                        "valid": False,
                    },
                    {
                        "magic": 0xFF,
                        "valid": False,
                    },
                ],
                "segwitPrefixes": [

                    {
                        "prefix": MainNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": TestNet3Params.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": RegressionNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": SimNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": (MainNetParams.bech32_hrp_segwit + "1").upper(),
                        "valid": True,
                    },
                    {
                        "prefix": mockNetParams.bech32_hrp_segwit + "1",
                        "valid": False,
                    },
                    {
                        "prefix": "abc1",
                        "valid": False,
                    },
                    {
                        "prefix": "1",
                        "valid": False,
                    },
                    {
                        "prefix": MainNetParams.bech32_hrp_segwit,
                        "valid": False,
                    },
                ],
                "hdMagics": [

                    {
                        "priv": MainNetParams.hd_private_key_id,
                        "want": MainNetParams.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": TestNet3Params.hd_private_key_id,
                        "want": TestNet3Params.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": RegressionNetParams.hd_private_key_id,
                        "want": RegressionNetParams.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": SimNetParams.hd_private_key_id,
                        "want": SimNetParams.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": mockNetParams.hd_private_key_id,
                        "err": ErrUnknownHDKeyID,
                    },
                    {
                        "priv": bytes([0xff, 0xff, 0xff, 0xff]),
                        "err": ErrUnknownHDKeyID,
                    },
                    {
                        "priv": bytes([0xff]),
                        "err": ErrUnknownHDKeyID,
                    },
                ]
            },

            {
                "name": "register mocknet",
                "register": [
                    {
                        "name": "mocknet",
                        "params": mockNetParams,
                        "err": None,
                    },
                ],
                "p2pkhMagics": [
                    {
                        "magic": MainNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": TestNet3Params.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": RegressionNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": SimNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": mockNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": 0xFF,
                        "valid": False,
                    },
                ],
                "p2shMagics": [
                    {
                        "magic": MainNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": TestNet3Params.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": RegressionNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": SimNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": mockNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": 0xFF,
                        "valid": False,
                    },
                ],
                "segwitPrefixes": [

                    {
                        "prefix": MainNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": TestNet3Params.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": RegressionNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": SimNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": (MainNetParams.bech32_hrp_segwit + "1").upper(),
                        "valid": True,
                    },
                    {
                        "prefix": mockNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": "abc1",
                        "valid": False,
                    },
                    {
                        "prefix": "1",
                        "valid": False,
                    },
                    {
                        "prefix": MainNetParams.bech32_hrp_segwit,
                        "valid": False,
                    },
                ],
                "hdMagics": [

                    {
                        "priv": mockNetParams.hd_private_key_id,
                        "want": mockNetParams.hd_public_key_id,
                        "err": None,
                    },
                ]
            },

            {
                "name": "more duplicates",
                "register": [
                    {
                        "name": "duplicate mainnet",
                        "params": MainNetParams,
                        "err": ErrDuplicateNet,
                    },
                    {
                        "name": "duplicate regtest",
                        "params": RegressionNetParams,
                        "err": ErrDuplicateNet,
                    },
                    {
                        "name": "duplicate testnet3",
                        "params": TestNet3Params,
                        "err": ErrDuplicateNet,
                    },
                    {
                        "name": "duplicate simnet",
                        "params": SimNetParams,
                        "err": ErrDuplicateNet,
                    },
                    {
                        "name": "duplicate mocknet",
                        "params": mockNetParams,
                        "err": ErrDuplicateNet,
                    },
                ],
                "p2pkhMagics": [
                    {
                        "magic": MainNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": TestNet3Params.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": RegressionNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": SimNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": mockNetParams.pub_key_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": 0xFF,
                        "valid": False,
                    },

                ],
                "p2shMagics": [
                    {
                        "magic": MainNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": TestNet3Params.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": RegressionNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": SimNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": mockNetParams.script_hash_addr_id,
                        "valid": True,
                    },
                    {
                        "magic": 0xFF,
                        "valid": False,
                    },

                ],
                "segwitPrefixes": [

                    {
                        "prefix": MainNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": TestNet3Params.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": RegressionNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": SimNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": (MainNetParams.bech32_hrp_segwit + "1").upper(),
                        "valid": True,
                    },
                    {
                        "prefix": mockNetParams.bech32_hrp_segwit + "1",
                        "valid": True,
                    },
                    {
                        "prefix": "abc1",
                        "valid": False,
                    },
                    {
                        "prefix": "1",
                        "valid": False,
                    },
                    {
                        "prefix": MainNetParams.bech32_hrp_segwit,
                        "valid": False,
                    },
                ],
                "hdMagics": [
                    {
                        "priv": MainNetParams.hd_private_key_id,
                        "want": MainNetParams.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": TestNet3Params.hd_private_key_id,
                        "want": TestNet3Params.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": RegressionNetParams.hd_private_key_id,
                        "want": RegressionNetParams.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": SimNetParams.hd_private_key_id,
                        "want": SimNetParams.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": mockNetParams.hd_private_key_id,
                        "want": mockNetParams.hd_public_key_id,
                        "err": None,
                    },
                    {
                        "priv": bytes([0xff, 0xff, 0xff, 0xff]),
                        "err": ErrUnknownHDKeyID,
                    },
                    {
                        "priv": bytes([0xff]),
                        "err": ErrUnknownHDKeyID,
                    },

                ]
            }

        ]

        for test in self.tests:
            for c in test['register']:
                if c['err']:
                    with self.assertRaises(c['err']):
                        register(c['params'])
                else:
                    register(c['params'])

            for c in test['p2pkhMagics']:
                self.assertEqual(is_pub_key_hash_addr_id(c['magic']), c['valid'])

            for c in test['p2shMagics']:
                self.assertEqual(is_script_hash_addr_id(c['magic']), c['valid'])

            for c in test['segwitPrefixes']:
                self.assertEqual(is_bech32_segwit_prefix(c['prefix']), c['valid'])

            for c in test['hdMagics']:
                if c['err']:
                    with self.assertRaises(c['err']):
                        hd_private_key_to_public_key_id(c['priv'])
                else:
                    self.assertEqual(hd_private_key_to_public_key_id(c['priv']), c['want'])



