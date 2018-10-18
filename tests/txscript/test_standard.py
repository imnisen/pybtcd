import unittest
from tests.txscript.test_reference import *
from txscript.standard import *
from tests.txscript.test_script_num import hex_to_bytes
from tests.utils import *
import btcutil
import chaincfg


def must_parse_short_form(script: str):
    return parse_short_form(script)


class TestStandard(unittest.TestCase):
    def test_PushedData(self):
        tests = [
            {
                "script": "0 IF 0 ELSE 2 ENDIF",
                "out": [bytes(), bytes()],
                "valid": True
            },

            {
                "script": "16777216 10000000",
                "out": [bytes([0x00, 0x00, 0x00, 0x01]),  # 16777216
                        bytes([0x80, 0x96, 0x98, 0x00])],  # 10000000
                "valid": True
            },
            {
                "script": "DUP HASH160 '17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem' EQUALVERIFY CHECKSIG",
                "out": [bytes([
                    # 17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem
                    0x31, 0x37, 0x56, 0x5a, 0x4e, 0x58, 0x31, 0x53, 0x4e, 0x35,
                    0x4e, 0x74, 0x4b, 0x61, 0x38, 0x55, 0x51, 0x46, 0x78, 0x77,
                    0x51, 0x62, 0x46, 0x65, 0x46, 0x63, 0x33, 0x69, 0x71, 0x52,
                    0x59, 0x68, 0x65, 0x6d,
                ])],
                "valid": True
            },

            {
                "script": "PUSHDATA4 1000 EQUAL",
                "out": None,
                "valid": False
            },

        ]

        for test in tests:
            script = must_parse_short_form(test['script'])

            if test['valid']:
                data = pushed_data(script)
                self.assertEqual(data, test['out'])
            else:
                with self.assertRaises(Exception):
                    pushed_data(script)


def newAddressPubKey(serializedPubKey):
    """

    :param []byte serializedPubKey:
    :return:
    """
    return btcutil.new_address_pub_key(serializedPubKey, chaincfg.MainNetParams)


def newAddressPubKeyHash(pkHash):
    """

    :param []byte pkHash:
    :return:
    """
    return btcutil.new_address_pub_key_hash(pkHash, chaincfg.MainNetParams)


def newAddressScriptHash(scriptHash):
    """

    :param scriptHash:
    :return:
    """
    return btcutil.new_address_script_hash_from_hash(scriptHash, chaincfg.MainNetParams)


class TestExtractPkScriptAddrs(unittest.TestCase):
    def test_extract_pk_script_addrs(self):
        tests = [
            {
                "name": "standard p2pk with compressed pubkey (0x02)",
                "script": hex_to_bytes("2102192d74d0cb94344c9569c2e779015" +
                                       "73d8d7903c3ebec3a957724895dca52c6b4ac"),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("02192d74d0cb9434" +
                                                  "4c9569c2e77901573d8d7903c3ebec3a9577" +
                                                  "24895dca52c6b4")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.PubKeyTy
            },

            {
                "name": "standard p2pk with uncompressed pubkey (0x04)",
                "script": hex_to_bytes("410411db93e1dcdb8a016b49840f8c53b" +
                                       "c1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddf" +
                                       "b84ccf9744464f82e160bfa9b8b64f9d4c03f999b864" +
                                       "3f656b412a3ac"),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("0411db93e1dcdb8a" +
                                                  "016b49840f8c53bc1eb68a382e97b1482eca" +
                                                  "d7b148a6909a5cb2e0eaddfb84ccf9744464" +
                                                  "f82e160bfa9b8b64f9d4c03f999b8643f656" +
                                                  "b412a3")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.PubKeyTy
            },

            {
                "name": "standard p2pk with hybrid pubkey (0x06)",
                "script": hex_to_bytes("4106192d74d0cb94344c9569c2e779015" +
                                       "73d8d7903c3ebec3a957724895dca52c6b40d4526483" +
                                       "8c0bd96852662ce6a847b197376830160c6d2eb5e6a4" +
                                       "c44d33f453eac"),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("06192d74d0cb9434" +
                                                  "4c9569c2e77901573d8d7903c3ebec3a9577" +
                                                  "24895dca52c6b40d45264838c0bd96852662" +
                                                  "ce6a847b197376830160c6d2eb5e6a4c44d3" +
                                                  "3f453e")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.PubKeyTy
            },

            {
                "name": "standard p2pk with compressed pubkey (0x03)",
                "script": hex_to_bytes("2103b0bd634234abbb1ba1e986e884185" +
                                       "c61cf43e001f9137f23c2c409273eb16e65ac"),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("03b0bd634234abbb" +
                                                  "1ba1e986e884185c61cf43e001f9137f23c2" +
                                                  "c409273eb16e65")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.PubKeyTy
            },

            {
                "name": "2nd standard p2pk with uncompressed pubkey (0x04)",
                "script": hex_to_bytes("4104b0bd634234abbb1ba1e986e884185" +
                                       "c61cf43e001f9137f23c2c409273eb16e6537a576782" +
                                       "eba668a7ef8bd3b3cfb1edb7117ab65129b8a2e681f3" +
                                       "c1e0908ef7bac"),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("04b0bd634234abbb" +
                                                  "1ba1e986e884185c61cf43e001f9137f23c2" +
                                                  "c409273eb16e6537a576782eba668a7ef8bd" +
                                                  "3b3cfb1edb7117ab65129b8a2e681f3c1e09" +
                                                  "08ef7b")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.PubKeyTy
            },

            {
                "name": "standard p2pk with hybrid pubkey (0x07)",
                "script": hex_to_bytes("4107b0bd634234abbb1ba1e986e884185" +
                                       "c61cf43e001f9137f23c2c409273eb16e6537a576782" +
                                       "eba668a7ef8bd3b3cfb1edb7117ab65129b8a2e681f3" +
                                       "c1e0908ef7bac"),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("07b0bd634234abbb" +
                                                  "1ba1e986e884185c61cf43e001f9137f23c2" +
                                                  "c409273eb16e6537a576782eba668a7ef8bd" +
                                                  "3b3cfb1edb7117ab65129b8a2e681f3c1e09" +
                                                  "08ef7b")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.PubKeyTy
            },

            {
                "name": "standard p2pkh",
                "script": hex_to_bytes("76a914ad06dd6ddee55cbca9a9e3713bd" +
                                       "7587509a3056488ac"),
                "addrs": [
                    newAddressPubKeyHash(hex_to_bytes("ad06dd6ddee5" +
                                                      "5cbca9a9e3713bd7587509a30564")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.PubKeyHashTy
            },

            {
                "name": "standard p2sh",
                "script": hex_to_bytes("a91463bcc565f9e68ee0189dd5cc67f1b" +
                                       "0e5f02f45cb87"),
                "addrs": [
                    newAddressScriptHash(hex_to_bytes("63bcc565f9e6" +
                                                      "8ee0189dd5cc67f1b0e5f02f45cb")),

                ],
                "reqSigs": 1,
                "class": ScriptClass.ScriptHashTy
            },

            # from real tx 60a20bd93aa49ab4b28d514ec10b06e1829ce6818ec06cd3aabd013ebcdc4bb1, vout 0
            {
                "name": "standard 1 of 2 multisig",
                "script": hex_to_bytes("514104cc71eb30d653c0c3163990c47b9" +
                                       "76f3fb3f37cccdcbedb169a1dfef58bbfbfaff7d8a47" +
                                       "3e7e2e6d317b87bafe8bde97e3cf8f065dec022b51d1" +
                                       "1fcdd0d348ac4410461cbdcc5409fb4b4d42b51d3338" +
                                       "1354d80e550078cb532a34bfa2fcfdeb7d76519aecc6" +
                                       "2770f5b0e4ef8551946d8a540911abe3e7854a26f39f" +
                                       "58b25c15342af52ae"
                                       ),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("04cc71eb30d653c0" +
                                                  "c3163990c47b976f3fb3f37cccdcbedb169a" +
                                                  "1dfef58bbfbfaff7d8a473e7e2e6d317b87b" +
                                                  "afe8bde97e3cf8f065dec022b51d11fcdd0d" +
                                                  "348ac4")),
                    newAddressPubKey(hex_to_bytes("0461cbdcc5409fb4" +
                                                  "b4d42b51d33381354d80e550078cb532a34b" +
                                                  "fa2fcfdeb7d76519aecc62770f5b0e4ef855" +
                                                  "1946d8a540911abe3e7854a26f39f58b25c1" +
                                                  "5342af"))

                ],
                "reqSigs": 1,
                "class": ScriptClass.MultiSigTy
            },

            # from real tx d646f82bd5fbdb94a36872ce460f97662b80c3050ad3209bef9d1e398ea277ab, vin 1
            {
                "name": "standard 2 of 3 multisig",
                "script": hex_to_bytes("524104cb9c3c222c5f7a7d3b9bd152f36" +
                                       "3a0b6d54c9eb312c4d4f9af1e8551b6c421a6a4ab0e2" +
                                       "9105f24de20ff463c1c91fcf3bf662cdde4783d4799f" +
                                       "787cb7c08869b4104ccc588420deeebea22a7e900cc8" +
                                       "b68620d2212c374604e3487ca08f1ff3ae12bdc63951" +
                                       "4d0ec8612a2d3c519f084d9a00cbbe3b53d071e9b09e" +
                                       "71e610b036aa24104ab47ad1939edcb3db65f7fedea6" +
                                       "2bbf781c5410d3f22a7a3a56ffefb2238af8627363bd" +
                                       "f2ed97c1f89784a1aecdb43384f11d2acc64443c7fc2" +
                                       "99cef0400421a53ae"
                                       ),
                "addrs": [
                    newAddressPubKey(hex_to_bytes("04cb9c3c222c5f7a" +
                                                  "7d3b9bd152f363a0b6d54c9eb312c4d4f9af" +
                                                  "1e8551b6c421a6a4ab0e29105f24de20ff46" +
                                                  "3c1c91fcf3bf662cdde4783d4799f787cb7c" +
                                                  "08869b")),
                    newAddressPubKey(hex_to_bytes("04ccc588420deeeb" +
                                                  "ea22a7e900cc8b68620d2212c374604e3487" +
                                                  "ca08f1ff3ae12bdc639514d0ec8612a2d3c5" +
                                                  "19f084d9a00cbbe3b53d071e9b09e71e610b" +
                                                  "036aa2")),
                    newAddressPubKey(hex_to_bytes("04ab47ad1939edcb" +
                                                  "3db65f7fedea62bbf781c5410d3f22a7a3a5" +
                                                  "6ffefb2238af8627363bdf2ed97c1f89784a" +
                                                  "1aecdb43384f11d2acc64443c7fc299cef04" +
                                                  "00421a")),

                ],
                "reqSigs": 2,
                "class": ScriptClass.MultiSigTy
            },

            # The below are nonstandard script due to things such as
            # invalid pubkeys, failure to parse, and not being of a
            # standard form.
            {
                "name": "p2pk with uncompressed pk missing OP_CHECKSIG",
                "script": hex_to_bytes("410411db93e1dcdb8a016b49840f8c53b" +
                                       "c1eb68a382e97b1482ecad7b148a6909a5cb2e0eaddf" +
                                       "b84ccf9744464f82e160bfa9b8b64f9d4c03f999b864" +
                                       "3f656b412a3"),
                "addrs": [],
                "reqSigs": 0,
                "class": ScriptClass.NonStandardTy
            },

            {
                "name": "valid signature from a sigscript - no addresses",
                "script": hex_to_bytes("47304402204e45e16932b8af514961a1d" +
                                       "3a1a25fdf3f4f7732e9d624c6c61548ab5fb8cd41022" +
                                       "0181522ec8eca07de4860a4acdd12909d831cc56cbba" +
                                       "c4622082221a8768d1d0901"),
                "addrs": [],
                "reqSigs": 0,
                "class": ScriptClass.NonStandardTy
            },

            # Note the technically the pubkey is the second item on the
            # stack, but since the address extraction intentionally only
            # works with standard PkScripts, this should not return any
            # addresses.
            {
                "name": "valid sigscript to reedeem p2pk - no addresses",
                "script": hex_to_bytes("493046022100ddc69738bf2336318e4e0" +
                                       "41a5a77f305da87428ab1606f023260017854350ddc0" +
                                       "22100817af09d2eec36862d16009852b7e3a0f6dd765" +
                                       "98290b7834e1453660367e07a014104cd4240c198e12" +
                                       "523b6f9cb9f5bed06de1ba37e96a1bbd13745fcf9d11" +
                                       "c25b1dff9a519675d198804ba9962d3eca2d5937d58e" +
                                       "5a75a71042d40388a4d307f887d"),
                "addrs": [],
                "reqSigs": 0,
                "class": ScriptClass.NonStandardTy
            },

            # from real tx 691dd277dc0e90a462a3d652a1171686de49cf19067cd33c7df0392833fb986a, vout 0
            # invalid public keys
            {
                "name": "1 of 3 multisig with invalid pubkeys",
                "script": hex_to_bytes("51411c2200007353455857696b696c656" +
                                       "16b73204361626c6567617465204261636b75700a0a6" +
                                       "361626c65676174652d3230313031323034313831312" +
                                       "e377a0a0a446f41776e6c6f61642074686520666f6c6" +
                                       "c6f77696e67207472616e73616374696f6e732077697" +
                                       "468205361746f736869204e616b616d6f746f2773206" +
                                       "46f776e6c6f61416420746f6f6c2077686963680a636" +
                                       "16e20626520666f756e6420696e207472616e7361637" +
                                       "4696f6e2036633533636439383731313965663739376" +
                                       "435616463636453ae"),
                "addrs": [],
                "reqSigs": 1,
                "class": ScriptClass.MultiSigTy
            },

            # from real tx: 691dd277dc0e90a462a3d652a1171686de49cf19067cd33c7df0392833fb986a, vout 44
            # invalid public keys
            {
                "name": "1 of 3 multisig with invalid pubkeys 2",
                "script": hex_to_bytes("514134633365633235396337346461636" +
                                       "536666430383862343463656638630a6336366263313" +
                                       "93936633862393461333831316233363536313866653" +
                                       "16539623162354136636163636539393361333938386" +
                                       "134363966636336643664616266640a3236363363666" +
                                       "13963663463303363363039633539336333653931666" +
                                       "56465373032392131323364643432643235363339643" +
                                       "338613663663530616234636434340a00000053ae"),
                "addrs": [],
                "reqSigs": 1,
                "class": ScriptClass.MultiSigTy
            },

            {
                "name": "empty script",
                "script": bytes(),
                "addrs": [],
                "reqSigs": 0,
                "class": ScriptClass.NonStandardTy
            },

            {
                "name": "script that does not parse",
                "script": bytes([OP_DATA_45]),
                "addrs": [],
                "reqSigs": 0,
                "class": ScriptClass.NonStandardTy
            },


        ]

        for test in tests:
            klass, addrs, reqSigs = extract_pk_script_addrs(test['script'], chaincfg.MainNetParams)
            self.assertEqual(klass, test['class'])
            self.assertTrue(list_equal(addrs, test['addrs']))
            self.assertEqual(reqSigs, test['reqSigs'])
