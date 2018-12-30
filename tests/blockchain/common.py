import os
import bz2
import shutil
import copy
from blockchain.chain import *
import database
from txscript import SigCache
from typing import Callable


# testDbType is the database backend type to use for the tests.
testDbType = "ffldb"

# testDbRoot is the root directory used to create all test databases.
testDbRoot = "testdbs"

# blockDataNet is the expected network in the test block data.
blockDataNet = wire.BitcoinNet.MainNet


# loadBlocks reads files containing bitcoin block data (gzipped but otherwise
# in the format bitcoind writes) from disk and returns them as an array of
# btcutil.Block.  This is largely borrowed from the test code in btcdb.
def load_blocks(filename: str) -> [btcutil.Block]:
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata", filename)
    network = wire.BitcoinNet.MainNet
    if filename.endswith(".bz2"):
        f = bz2.open(filename, 'rb')
    else:
        f = open(filename, 'rb')

    try:
        blocks = []
        while True:
            # read network
            b = f.read(4)
            if len(b) < 4:
                # print("1")
                break

            net = wire.BitcoinNet.from_int(int.from_bytes(b, byteorder="little"))
            if net != network:
                break

            # read block len
            b = f.read(4)
            if len(b) < 4:
                # print("2")
                break
            block_len = int.from_bytes(b, byteorder="little")

            # read block
            b = f.read(block_len)
            if len(b) < block_len:
                # print("3")
                break

            try:
                block = btcutil.Block.from_bytes(b)
            except Exception as e:
                # print('4')
                print(e)
                break

            blocks.append(block)
        return blocks

    finally:
        f.close()



# isSupportedDbType returns whether or not the passed database type is
# currently supported.
def is_supported_db_type(db_type: str) -> bool:
    supported_drivers = database.supported_drivers()
    return db_type in supported_drivers


# chainSetup is used to create a new db and chain instance with the genesis
# block already inserted.  In addition to the new chain instance, it returns
# a teardown function the caller should invoke when done testing to clean up.
def chain_setup(db_name: str, params: chaincfg.Params) -> (BlockChain, Callable):
    if not is_supported_db_type(testDbType):
        raise Exception("unsupported db type %s" % testDbType)

    # Handle memory database specially since it doesn't need the disk
    # specific handling.
    db = None
    teardown = None

    if testDbType == "memdb":
        ndb = database.create(testDbType)
        db = ndb

        # Setup a teardown function for cleaning up.  This function is
        # returned to the caller to be invoked when it is done testing.
        def fn_teardown():
            db.close()

        teardown = fn_teardown

    else:
        # Create the root directory for test databases.
        if not os.path.exists(testDbRoot):
            os.makedirs(testDbRoot, mode=0o700)

        # Create a new database to store the accepted blocks into.
        db_path = os.path.join(testDbRoot, db_name)
        if os.path.exists(db_path):
            shutil.rmtree(db_path)

        ndb = database.create(testDbType, db_path, blockDataNet)  #TOCHECK the db_path correctness

        db = ndb

        # Setup a teardown function for cleaning up.  This function is
        # returned to the caller to be invoked when it is done testing.

        def fn_teardown():
            db.close()
            shutil.rmtree(db_path)
            shutil.rmtree(testDbRoot)

        teardown = fn_teardown

    # Copy the chain params to ensure any modifications the tests do to
    # the chain parameters do not affect the global instance.
    params_copy = copy.deepcopy(params)

    # Create the main chain instance.
    try:
        chain = Config(
            db=db,
            chain_params=params_copy,
            checkpoints=None,
            time_source=MedianTime(),
            sig_cache=SigCache()
        ).new_block_chain()
    except Exception as e:
        teardown()
        raise e

    return chain, teardown


# loadUtxoView returns a utxo view loaded from a file.
def load_utxo_view(filename: str) -> UtxoViewpoint:
    # The utxostore file format is:
    # <tx hash><output index><serialized utxo len><serialized utxo>
    #
    # The output index and serialized utxo len are little endian uint32s
    # and the serialized utxo uses the format described in chainio.go.
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "testdata", filename)
    network = wire.BitcoinNet.MainNet
    if filename.endswith(".bz2"):
        f = bz2.open(filename, 'rb')
    else:
        f = open(filename, 'rb')

    try:
        view = UtxoViewpoint()
        while True:
            # read hash of the utxo entry.
            b = f.read(chainhash.HashSize)
            if len(b) < chainhash.HashSize:
                # print("1")
                break
            hash = chainhash.Hash(b)

            # read output index of the utxo entry.
            b = f.read(4)
            if len(b) < 4:
                # print("2")
                break
            index = int.from_bytes(b, byteorder="little")

            # Num of serialized utxo entry bytes.
            b = f.read(4)
            if len(b) < 4:
                # print("3")
                break
            num_bytes = int.from_bytes(b, byteorder="little")

            b = f.read(num_bytes)
            if len(b) < num_bytes:
                # print("4")
                break

            # Deserialize it and add it to the view.
            entry = deserialize_utxo_entry(b)

            view.entries[wire.OutPoint(hash=hash, index=index)] = entry

        return view
    finally:
        f.close()


# Block100000 defines block 100,000 of the block chain.  It is used to
# test Block operations.
Block100000 = wire.MsgBlock(
    header=wire.BlockHeader(
        version=1,
        prev_block=chainhash.Hash(bytes([
            0x50, 0x12, 0x01, 0x19, 0x17, 0x2a, 0x61, 0x04,
            0x21, 0xa6, 0xc3, 0x01, 0x1d, 0xd3, 0x30, 0xd9,
            0xdf, 0x07, 0xb6, 0x36, 0x16, 0xc2, 0xcc, 0x1f,
            0x1c, 0xd0, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00,
        ])),  # 000000000002d01c1fccc21636b607dfd930d31d01c3a62104612a1719011250
        merkle_root=chainhash.Hash(bytes([
            0x66, 0x57, 0xa9, 0x25, 0x2a, 0xac, 0xd5, 0xc0,
            0xb2, 0x94, 0x09, 0x96, 0xec, 0xff, 0x95, 0x22,
            0x28, 0xc3, 0x06, 0x7c, 0xc3, 0x8d, 0x48, 0x85,
            0xef, 0xb5, 0xa4, 0xac, 0x42, 0x47, 0xe9, 0xf3,
        ])),  # f3e94742aca4b5ef85488dc37c06c3282295ffec960994b2c0d5ac2a25a95766
        timestamp=1293623863,  # 2010-12-29 11:57:43 +0000 UTC
        bits=0x1b04864c,  # 453281356
        nonce=0x10572b0f,  # 274148111
    ),
    transactions=[
        wire.MsgTx(
            version=1,
            tx_ins=[
                wire.TxIn(
                    previous_out_point=wire.OutPoint(
                        hash=chainhash.Hash(),
                        index=0xffffffff
                    ),
                    signature_script=bytes([0x04, 0x4c, 0x86, 0x04, 0x1b, 0x02, 0x06, 0x02, ]),
                    sequence=0xffffffff
                )
            ],
            tx_outs=[
                wire.TxOut(
                    value=0x12a05f200,  # 5000000000
                    pk_script=bytes([
                        0x41,  # OP_DATA_65
                        0x04, 0x1b, 0x0e, 0x8c, 0x25, 0x67, 0xc1, 0x25,
                        0x36, 0xaa, 0x13, 0x35, 0x7b, 0x79, 0xa0, 0x73,
                        0xdc, 0x44, 0x44, 0xac, 0xb8, 0x3c, 0x4e, 0xc7,
                        0xa0, 0xe2, 0xf9, 0x9d, 0xd7, 0x45, 0x75, 0x16,
                        0xc5, 0x81, 0x72, 0x42, 0xda, 0x79, 0x69, 0x24,
                        0xca, 0x4e, 0x99, 0x94, 0x7d, 0x08, 0x7f, 0xed,
                        0xf9, 0xce, 0x46, 0x7c, 0xb9, 0xf7, 0xc6, 0x28,
                        0x70, 0x78, 0xf8, 0x01, 0xdf, 0x27, 0x6f, 0xdf,
                        0x84,  # 65-byte signature
                        0xac,  # OP_CHECKSIG
                    ])
                )
            ],
            lock_time=0
        ),

        wire.MsgTx(
            version=1,
            tx_ins=[
                wire.TxIn(
                    previous_out_point=wire.OutPoint(
                        hash=chainhash.Hash(bytes([
                            0x03, 0x2e, 0x38, 0xe9, 0xc0, 0xa8, 0x4c, 0x60,
                            0x46, 0xd6, 0x87, 0xd1, 0x05, 0x56, 0xdc, 0xac,
                            0xc4, 0x1d, 0x27, 0x5e, 0xc5, 0x5f, 0xc0, 0x07,
                            0x79, 0xac, 0x88, 0xfd, 0xf3, 0x57, 0xa1, 0x87,
                        ])),  # 87a157f3fd88ac7907c05fc55e271dc4acdc5605d187d646604ca8c0e9382e03
                        index=0
                    ),
                    signature_script=bytes([
                        0x49,  # OP_DATA_73
                        0x30, 0x46, 0x02, 0x21, 0x00, 0xc3, 0x52, 0xd3,
                        0xdd, 0x99, 0x3a, 0x98, 0x1b, 0xeb, 0xa4, 0xa6,
                        0x3a, 0xd1, 0x5c, 0x20, 0x92, 0x75, 0xca, 0x94,
                        0x70, 0xab, 0xfc, 0xd5, 0x7d, 0xa9, 0x3b, 0x58,
                        0xe4, 0xeb, 0x5d, 0xce, 0x82, 0x02, 0x21, 0x00,
                        0x84, 0x07, 0x92, 0xbc, 0x1f, 0x45, 0x60, 0x62,
                        0x81, 0x9f, 0x15, 0xd3, 0x3e, 0xe7, 0x05, 0x5c,
                        0xf7, 0xb5, 0xee, 0x1a, 0xf1, 0xeb, 0xcc, 0x60,
                        0x28, 0xd9, 0xcd, 0xb1, 0xc3, 0xaf, 0x77, 0x48,
                        0x01,  # 73-byte signature
                        0x41,  # OP_DATA_65
                        0x04, 0xf4, 0x6d, 0xb5, 0xe9, 0xd6, 0x1a, 0x9d,
                        0xc2, 0x7b, 0x8d, 0x64, 0xad, 0x23, 0xe7, 0x38,
                        0x3a, 0x4e, 0x6c, 0xa1, 0x64, 0x59, 0x3c, 0x25,
                        0x27, 0xc0, 0x38, 0xc0, 0x85, 0x7e, 0xb6, 0x7e,
                        0xe8, 0xe8, 0x25, 0xdc, 0xa6, 0x50, 0x46, 0xb8,
                        0x2c, 0x93, 0x31, 0x58, 0x6c, 0x82, 0xe0, 0xfd,
                        0x1f, 0x63, 0x3f, 0x25, 0xf8, 0x7c, 0x16, 0x1b,
                        0xc6, 0xf8, 0xa6, 0x30, 0x12, 0x1d, 0xf2, 0xb3,
                        0xd3,  # 65-byte pubkey
                    ]),
                    sequence=0xffffffff
                )
            ],
            tx_outs=[
                wire.TxOut(
                    value=0x2123e300,  # 556000000
                    pk_script=bytes([
                        0x76,  # OP_DUP
                        0xa9,  # OP_HASH160
                        0x14,  # OP_DATA_20
                        0xc3, 0x98, 0xef, 0xa9, 0xc3, 0x92, 0xba, 0x60,
                        0x13, 0xc5, 0xe0, 0x4e, 0xe7, 0x29, 0x75, 0x5e,
                        0xf7, 0xf5, 0x8b, 0x32,
                        0x88,  # OP_EQUALVERIFY
                        0xac,  # OP_CHECKSIG
                    ])
                ),

                wire.TxOut(
                    value=0x108e20f00,  # 4444000000
                    pk_script=bytes([
                        0x76,  # OP_DUP
                        0xa9,  # OP_HASH160
                        0x14,  # OP_DATA_20
                        0x94, 0x8c, 0x76, 0x5a, 0x69, 0x14, 0xd4, 0x3f,
                        0x2a, 0x7a, 0xc1, 0x77, 0xda, 0x2c, 0x2f, 0x6b,
                        0x52, 0xde, 0x3d, 0x7c,
                        0x88,  # OP_EQUALVERIFY
                        0xac,  # OP_CHECKSIG
                    ])
                ),

            ],
            lock_time=0
        ),

        wire.MsgTx(
            version=1,
            tx_ins=[
                wire.TxIn(
                    previous_out_point=wire.OutPoint(
                        hash=chainhash.Hash(bytes([
                            0xc3, 0x3e, 0xbf, 0xf2, 0xa7, 0x09, 0xf1, 0x3d,
                            0x9f, 0x9a, 0x75, 0x69, 0xab, 0x16, 0xa3, 0x27,
                            0x86, 0xaf, 0x7d, 0x7e, 0x2d, 0xe0, 0x92, 0x65,
                            0xe4, 0x1c, 0x61, 0xd0, 0x78, 0x29, 0x4e, 0xcf,
                        ])),  # cf4e2978d0611ce46592e02d7e7daf8627a316ab69759a9f3df109a7f2bf3ec3
                        index=1
                    ),
                    signature_script=bytes([
                        0x47,  # OP_DATA_71
                        0x30, 0x44, 0x02, 0x20, 0x03, 0x2d, 0x30, 0xdf,
                        0x5e, 0xe6, 0xf5, 0x7f, 0xa4, 0x6c, 0xdd, 0xb5,
                        0xeb, 0x8d, 0x0d, 0x9f, 0xe8, 0xde, 0x6b, 0x34,
                        0x2d, 0x27, 0x94, 0x2a, 0xe9, 0x0a, 0x32, 0x31,
                        0xe0, 0xba, 0x33, 0x3e, 0x02, 0x20, 0x3d, 0xee,
                        0xe8, 0x06, 0x0f, 0xdc, 0x70, 0x23, 0x0a, 0x7f,
                        0x5b, 0x4a, 0xd7, 0xd7, 0xbc, 0x3e, 0x62, 0x8c,
                        0xbe, 0x21, 0x9a, 0x88, 0x6b, 0x84, 0x26, 0x9e,
                        0xae, 0xb8, 0x1e, 0x26, 0xb4, 0xfe, 0x01,
                        0x41,  # OP_DATA_65
                        0x04, 0xae, 0x31, 0xc3, 0x1b, 0xf9, 0x12, 0x78,
                        0xd9, 0x9b, 0x83, 0x77, 0xa3, 0x5b, 0xbc, 0xe5,
                        0xb2, 0x7d, 0x9f, 0xff, 0x15, 0x45, 0x68, 0x39,
                        0xe9, 0x19, 0x45, 0x3f, 0xc7, 0xb3, 0xf7, 0x21,
                        0xf0, 0xba, 0x40, 0x3f, 0xf9, 0x6c, 0x9d, 0xee,
                        0xb6, 0x80, 0xe5, 0xfd, 0x34, 0x1c, 0x0f, 0xc3,
                        0xa7, 0xb9, 0x0d, 0xa4, 0x63, 0x1e, 0xe3, 0x95,
                        0x60, 0x63, 0x9d, 0xb4, 0x62, 0xe9, 0xcb, 0x85,
                        0x0f,  # 65-byte pubkey
                    ]),
                    sequence=0xffffffff
                )
            ],
            tx_outs=[
                wire.TxOut(
                    value=0xf4240,  # 1000000
                    pk_script=bytes([
                        0x76,  # OP_DUP
                        0xa9,  # OP_HASH160
                        0x14,  # OP_DATA_20
                        0xb0, 0xdc, 0xbf, 0x97, 0xea, 0xbf, 0x44, 0x04,
                        0xe3, 0x1d, 0x95, 0x24, 0x77, 0xce, 0x82, 0x2d,
                        0xad, 0xbe, 0x7e, 0x10,
                        0x88,  # OP_EQUALVERIFY
                        0xac,  # OP_CHECKSIG
                    ])
                ),

                wire.TxOut(
                    value=0x11d260c0,  # 299000000
                    pk_script=bytes([
                        0x76,  # OP_DUP
                        0xa9,  # OP_HASH160
                        0x14,  # OP_DATA_20
                        0x6b, 0x12, 0x81, 0xee, 0xc2, 0x5a, 0xb4, 0xe1,
                        0xe0, 0x79, 0x3f, 0xf4, 0xe0, 0x8a, 0xb1, 0xab,
                        0xb3, 0x40, 0x9c, 0xd9,
                        0x88,  # OP_EQUALVERIFY
                        0xac,  # OP_CHECKSIG
                    ])
                ),

            ],
            lock_time=0
        ),

        wire.MsgTx(
            version=1,
            tx_ins=[
                wire.TxIn(
                    previous_out_point=wire.OutPoint(
                        hash=chainhash.Hash(bytes([
                            0x0b, 0x60, 0x72, 0xb3, 0x86, 0xd4, 0xa7, 0x73,
                            0x23, 0x52, 0x37, 0xf6, 0x4c, 0x11, 0x26, 0xac,
                            0x3b, 0x24, 0x0c, 0x84, 0xb9, 0x17, 0xa3, 0x90,
                            0x9b, 0xa1, 0xc4, 0x3d, 0xed, 0x5f, 0x51, 0xf4,
                        ])),  # f4515fed3dc4a19b90a317b9840c243bac26114cf637522373a7d486b372600b
                        index=0
                    ),
                    signature_script=bytes([
                        0x49,  # OP_DATA_73
                        0x30, 0x46, 0x02, 0x21, 0x00, 0xbb, 0x1a, 0xd2,
                        0x6d, 0xf9, 0x30, 0xa5, 0x1c, 0xce, 0x11, 0x0c,
                        0xf4, 0x4f, 0x7a, 0x48, 0xc3, 0xc5, 0x61, 0xfd,
                        0x97, 0x75, 0x00, 0xb1, 0xae, 0x5d, 0x6b, 0x6f,
                        0xd1, 0x3d, 0x0b, 0x3f, 0x4a, 0x02, 0x21, 0x00,
                        0xc5, 0xb4, 0x29, 0x51, 0xac, 0xed, 0xff, 0x14,
                        0xab, 0xba, 0x27, 0x36, 0xfd, 0x57, 0x4b, 0xdb,
                        0x46, 0x5f, 0x3e, 0x6f, 0x8d, 0xa1, 0x2e, 0x2c,
                        0x53, 0x03, 0x95, 0x4a, 0xca, 0x7f, 0x78, 0xf3,
                        0x01,  # 73-byte signature
                        0x41,  # OP_DATA_65
                        0x04, 0xa7, 0x13, 0x5b, 0xfe, 0x82, 0x4c, 0x97,
                        0xec, 0xc0, 0x1e, 0xc7, 0xd7, 0xe3, 0x36, 0x18,
                        0x5c, 0x81, 0xe2, 0xaa, 0x2c, 0x41, 0xab, 0x17,
                        0x54, 0x07, 0xc0, 0x94, 0x84, 0xce, 0x96, 0x94,
                        0xb4, 0x49, 0x53, 0xfc, 0xb7, 0x51, 0x20, 0x65,
                        0x64, 0xa9, 0xc2, 0x4d, 0xd0, 0x94, 0xd4, 0x2f,
                        0xdb, 0xfd, 0xd5, 0xaa, 0xd3, 0xe0, 0x63, 0xce,
                        0x6a, 0xf4, 0xcf, 0xaa, 0xea, 0x4e, 0xa1, 0x4f,
                        0xbb,  # 65-byte pubkey
                    ]),
                    sequence=0xffffffff
                )
            ],
            tx_outs=[
                wire.TxOut(
                    value=0xf4240,  # 1000000
                    pk_script=bytes([
                        0x76,  # OP_DUP
                        0xa9,  # OP_HASH160
                        0x14,  # OP_DATA_20
                        0x39, 0xaa, 0x3d, 0x56, 0x9e, 0x06, 0xa1, 0xd7,
                        0x92, 0x6d, 0xc4, 0xbe, 0x11, 0x93, 0xc9, 0x9b,
                        0xf2, 0xeb, 0x9e, 0xe0,
                        0x88,  # OP_EQUALVERIFY
                        0xac,  # OP_CHECKSIG
                    ])
                ),
            ],
            lock_time=0
        )

    ]
)
