import unittest

from btcutil.bech32.bech32 import *
from tests.utils import *

tests = [
    {"str": "A12UEL5L", "valid": True},
    {"str": "an83characterlonghumanreadablepartthatcontainsthenumber1andtheexcludedcharactersbio1tt5tgs",
     "valid": True},
    {"str": "abcdef1qpzry9x8gf2tvdw0s3jn54khce6mua7lmqqqxw", "valid": True},
    {"str": "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j",
     "valid": True},
    {"str": "split1checkupstagehandshakeupstreamerranterredcaperred2y9e3w", "valid": True},
    {"str": "split1checkupstagehandshakeupstreamerranterredcaperred2y9e2w", "valid": False},
    {"str": "s lit1checkupstagehandshakeupstreamerranterredcaperredp8hs2p", "valid": False},
    {"str": "spl" + str(127) + "t1checkupstagehandshakeupstreamerranterredcaperred2y9e3w", "valid": False},
    {"str": "split1cheo2y9e2w", "valid": False},
    {"str": "split1a2y9w", "valid": False},
    {"str": "1checkupstagehandshakeupstreamerranterredcaperred2y9e3w", "valid": False},
    {"str": "11qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqsqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc8247j",
     "valid": False},

]


class TestBech32(unittest.TestCase):
    def test_encode_and_decode(self):
        for test in tests:
            if test['valid']:
                hrp, decoded = decode(test['str'])
                encoded = encode(hrp, decoded)
                self.assertEqual(encoded, test['str'].lower())

                # Flip a bit in the string an make sure it is caught.
                pos = last_index_str(test['str'], "1")
                flipped = test['str'][:pos + 1] + chr(ord(test['str'][pos + 1]) ^ 1) + test['str'][pos + 2:]
                with self.assertRaises(Bech32DecodeError):
                    decode(flipped)

            else:
                with self.assertRaises(Bech32DecodeError):
                    decode(test['str'])
