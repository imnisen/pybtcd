import unittest
import wire
import os
import bz2
import btcutil
import chaincfg
import database
import copy


# some constant

# blockDataNet is the expected network in the test block data.
blockDataNet = wire.BitcoinNet.MainNet

# blockDataFile is the path to a file containing the first 256 blocks
# of the block chain.
dataDirPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
blockDataFile = os.path.join(dataDirPath, "testdata", "blocks1-256.bz2")


# print("blockDataFile", blockDataFile)


class TestContext:
    def __init__(self, db, bucket_depth=None, is_writeable=None, blocks=None):
        """

        :param database.DB db:
        :param int bucket_depth:
        :param bool is_writeable:
        :param [btcutil.Block] blocks:
        """

        self.db = db
        self.bucket_depth = bucket_depth or 0
        self.is_writeable = is_writeable or False
        self.blocks = blocks or []


class KeyPair:
    def __init__(self, key, value):
        """

        :param bytes key:
        :param bytes or None value:
        """
        self.key = key
        self.value = value


class TestInterface(unittest.TestCase):
    # ***
    # Some helper method
    # ***

    # loadBlocks loads the blocks contained in the testdata directory and returns
    # a slice of them.
    def _load_blocks(self, data_file: str, network: wire.BitcoinNet):
        with bz2.open(data_file, 'rb') as f:
            blocks = []  # for return blocks

            # set the first block as genesis block
            genesis = btcutil.Block(chaincfg.MainNetParams.genesis_block)
            blocks.append(genesis)

            while True:
                # check EOF (not full correct check)
                b = f.read(4)
                if len(b) < 4:
                    break

                # Load the remaining blocks
                net = wire.BitcoinNet.from_int(int.from_bytes(b, byteorder="little"))

                self.assertEqual(net, network)

                # read blockLen(uint32)
                block_len = wire.read_element(f, "uint32")

                # read block bytes
                block_bytes = f.read(block_len)

                block = btcutil.Block.from_bytes(block_bytes)

                blocks.append(block)

            return blocks

    # testGetValues checks that all of the provided key/value pairs can be
    # retrieved from the database and the retrieved values match the provided
    # values.
    def _test_get_values(self, tc, bucket, values):
        for item in values:
            got_value = bucket.get(item.key)
            self.assertEqual(got_value, item.value)
        return

    # testPutValues stores all of the provided key/value pairs in the provided
    # bucket while checking for errors.
    def _test_put_values(self, tc, bucket, values):
        for item in values:
            bucket.put(item.key, item.value)
        return

    def _test_delete_values(self, tc, bucket, values):
        for item in values:
            bucket.delete(item.key, item.value)
        return

    # toGetValues returns a copy of the provided keypairs with all of the nil
    # values set to an empty byte slice.  This is used to ensure that keys set to
    # nil values result in empty byte slices when retrieved instead of nil.
    def _to_get_values(self, values):
        values = copy.deepcopy(values)
        for item in values:
            if item.value is None:
                item.value = bytes()
        return values

    def _roll_back_values(self,  values):
        values = copy.deepcopy(values)
        for item in values:
            item.value = None
        return values

    # testCursorKeyPair checks that the provide key and value match the expected
    # keypair at the provided index.  It also ensures the index is in range for the
    # provided slice of expected keypairs.
    def _test_cursor_key_pair(self, tc, k, v, index, values):
        self.assertTrue(index > 0)
        self.assertTrue(index < len(values))

        pair = values[index]
        self.assertEqual(k, pair.key)
        self.assertEqual(v, pair.value)
        return

    # lookupKey is a convenience method to lookup the requested key from the
    # provided keypair slice along with whether or not the key was found.
    def _lookup_key(self, key, values):
        for item in values:
            if key == item.key:
                return item.value , True
        return None, False

    # testNestedBucket reruns the testBucketInterface against a nested bucket along
    # with a counter to only test a couple of level deep.
    def _test_nested_bucket(self, tc, test_bucket):
        # Don't go more than 2 nested levels deep.
        if tc.bucket_depth > 1:
            return True

        tc.bucket_depth += 1
        try:
            return self.test_bucket_inteface(tc, test_bucket)
        finally:
            tc.bucket_depth -= 1


        

    # ***
    # Here comes the test
    # ***

    # testCursorInterface ensures the cursor itnerface is working properly by
    # exercising all of its functions on the passed bucket.
    def test_cursor_interface(self, tc: TestContext, bucket: database.Bucket):
        # Ensure a cursor can be obtained for the bucket.
        cursor = bucket.cursor()

        # Ensure the cursor returns the same bucket it was created for.
        self.assertEqual(cursor.bucket(), bucket)

        if tc.is_writeable:
            unsorted_values = [
                KeyPair(b"cursor", b"val1"),
                KeyPair(b"abcd", b"val2"),
                KeyPair(b"bcd", b"val3"),
                KeyPair(b"defg", None),
            ]

            sorted_values = [
                KeyPair(b"abcd", b"val2"),
                KeyPair(b"bcd", b"val3"),
                KeyPair(b"cursor", b"val1"),
                KeyPair(b"defg", None),
            ]

            # Store the values to be used in the cursor tests in unsorted
            # order and ensure they were actually stored.
            self._test_put_values(tc, bucket, unsorted_values)
            self._test_get_values(tc, bucket, self._to_get_values(unsorted_values))

            # Ensure the cursor returns all items in byte-sorted order when
            # iterating forward.
            cur_idx = 0
            ok = cursor.first()
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx += 1
                ok = cursor.next()

            self.assertEqual(cur_idx, len(unsorted_values))

            # Ensure the cursor returns all items in reverse byte-sorted
            # order when iterating in reverse.
            cur_idx = len(unsorted_values) - 1
            ok = cursor.last()
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx -= 1
                ok = cursor.prev()

            self.assertEqual(cur_idx, -1)

            # Ensure forward iteration works as expected after seeking.
            middle_idx = (len(sorted_values) - 1) // 2
            seek_key = sorted_values[middle_idx].key

            cur_idx = middle_idx
            ok = cursor.seek(seek_key)
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx += 1
                ok = cursor.next()

            self.assertEqual(cur_idx, len(unsorted_values))

            # Ensure reverse iteration works as expected after seeking.
            cur_idx = middle_idx
            ok = cursor.seek(seek_key)
            while ok:
                k, v = cursor.key(), cursor.value()
                self._test_cursor_key_pair(tc, k, v, cur_idx, sorted_values)
                cur_idx -= 1
                ok = cursor.prev()

            self.assertEqual(cur_idx, -1)

            # Ensure the cursor deletes items properly.
            self.assertTrue(cursor.first())

            k = cursor.key()
            cursor.delete()
            self.assertIsNone(bucket.get(k))

        return

    # testBucketInterface ensures the bucket interface is working properly by
    # exercising all of its functions.  This includes the cursor interface for the
    # cursor returned from the bucket.
    def test_bucket_inteface(self, tc: TestContext, bucket: database.Bucket):
        self.assertEqual(bucket.writable(), tc.is_writeable)

        if tc.is_writeable:
            key_values = [
                KeyPair(b"bucketkey1", b"foo1"),
                KeyPair(b"bucketkey2", b"foo2"),
                KeyPair(b"bucketkey3", b"foo3"),
                KeyPair(b"bucketkey4", None),
            ]
            expected_key_values = self._to_get_values(key_values)
            self._test_put_values(tc, bucket, key_values)
            self._test_get_values(tc, bucket, self._to_get_values(expected_key_values))

            # Iterate all of the keys using ForEach while making sure the
            # stored values are the expected values.
            keys_found = []

            for k, v in bucket.for_each2():
                want_v, found = self._lookup_key(k,  expected_key_values)
                self.assertTrue(found)

                self.assertEqual(v, want_v)

                keys_found.append(k)

            # Ensure all keys were iterated.
            for item in key_values:
                self.assertTrue(item.key in keys_found)

            # Delete the keys and ensure they were deleted.
            self._test_delete_values(tc, bucket, key_values)
            self._test_get_values(tc, bucket, self._roll_back_values(key_values))

            # Ensure creating a new bucket works as expected.
            test_bucket_name = b"testbucket"
            test_bucket = bucket.create_bucket(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure creating a bucket that already exists fails with the
            # expected error.
            with self.assertRaises(database.DBError) as cm:
                bucket.create_bucket(test_bucket_name)
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrBucketExists)

            # Ensure CreateBucketIfNotExists returns an existing bucket.
            test_bucket = bucket.create_bucket_if_not_exists(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure retrieving an existing bucket works as expected.
            test_bucket = bucket.bucket(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure deleting a bucket works as intended.
            bucket.delete_bucket(test_bucket_name)
            self.assertIsNone(bucket.bucket(test_bucket_name))

            # Ensure deleting a bucket that doesn't exist returns the
            #  expected error.
            with self.assertRaises(database.DBError) as cm:
                bucket.delete_bucket(test_bucket_name)
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrBucketNotFound)

            # Ensure CreateBucketIfNotExists creates a new bucket when
            # it doesn't already exist.
            test_bucket = bucket.create_bucket_if_not_exists(test_bucket_name)
            self._test_nested_bucket(tc, test_bucket)

            # Ensure the cursor interface works as expected.
            self.test_cursor_interface(tc, test_bucket)

            # Delete the test bucket to avoid leaving it around for future
            # calls.
            bucket.delete_bucket(test_bucket_name)
            self.assertIsNone(bucket.bucket(test_bucket_name))
        else:
            # Put should fail with bucket that is not writable.
            fail_bytes = b"fail"
            with self.assertRaises(database.DBError) as cm:
                bucket.put(fail_bytes, fail_bytes)
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.delete(fail_bytes)
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.create_bucket(fail_bytes)
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.create_bucket_if_not_exists(fail_bytes)
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            with self.assertRaises(database.DBError) as cm:
                bucket.delete_bucket(fail_bytes)
                self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)

            # Ensure the cursor interface works as expected with read-only
            # buckets.
            self.test_cursor_interface(tc, bucket)

        return

    # testManagedTxPanics ensures calling Rollback of Commit inside a managed
    # transaction panics.
    def test_managed_tx_panics(self, tc):
        # Ensure calling Commit on a managed read-only transaction panics.
        with self.assertRaises(Exception):
            tc.db.view(lambda tx: tx.commit())

        # Ensure calling Rollback on a managed read-only transaction panics.
        with self.assertRaises(Exception):
            tc.db.view(lambda tx: tx.rollback())

        # Ensure calling Commit on a managed read-write transaction panics.
        with self.assertRaises(Exception):
            tc.db.update(lambda tx: tx.commit())

        # Ensure calling Rollback on a managed read-write transaction panics.
        with self.assertRaises(Exception):
            tc.db.update(lambda tx: tx.rollback())

        return

    # testMetadataManualTxInterface ensures that the manual transactions metadata
    # interface works as expected.
    def test_metadata_manual_tx_interface(self, tc):
        # populateValues tests that populating values works as expected.
        #
        # When the writable flag is false, a read-only tranasction is created,
        # standard bucket tests for read-only transactions are performed, and
        # the Commit function is checked to ensure it fails as expected.
        #
        # Otherwise, a read-write transaction is created, the values are
        # written, standard bucket tests for read-write transactions are
        # performed, and then the transaction is either committed or rolled
        # back depending on the flag.
        bucket1_name = b"bucket1"
        def populate_values(writable: bool, rollback: bool, put_values: [KeyPair]) -> bool:
            tx = tc.db.begin(writable)

            # TODO rollback on panic

            metadata_bucket = tx.meta_data()
            print("metadata bucket", metadata_bucket)
            self.assertIsNotNone(metadata_bucket)

            bucket1 = metadata_bucket.bucket(bucket1_name)
            self.assertIsNotNone(bucket1)

            tc.is_writeable = writable

            self.test_bucket_inteface(tc, bucket1)

            if not writable:
                # The transaction is not writable, so it should fail
                # the commit.

                # test_name = "unwritable tx commit"
                with self.assertRaises(database.DB) as cm:
                    tx.commit()  # TOCHANGE TODO commit and rollback raise a exception that not catch here
                    self.assertEqual(cm.exception.c, database.ErrorCode.ErrTxNotWritable)
            else:
                self.assertTrue(self._test_put_values(tc, bucket1, put_values))
                if rollback:
                    tx.rollback()
                else:
                    tx.commit()
            
            return



        # checkValues starts a read-only transaction and checks that all of
        # the key/value pairs specified in the expectedValues parameter match
        # what's in the database.
        def check_values(expected_values: [KeyPair]) -> bool:
            pass

        # deleteValues starts a read-write transaction and deletes the keys
        # in the passed key/value pairs.
        def delete_values(values: [KeyPair]) -> bool:
            pass

        # keyValues holds the keys and values to use when putting values into a
        # bucket.
        key_values = [
            KeyPair(b"umtxkey1", b"foo1"),
            KeyPair(b"umtxkey2", b"foo2"),
            KeyPair(b"umtxkey3", b"foo3"),
            KeyPair(b"umtxkey4", None),
        ]

        # Ensure that attempting populating the values using a read-only
        # transaction fails as expected.
        self.assertTrue(populate_values(False, True, key_values))
        self.assertTrue(check_values(self._roll_back_values(key_values)))

        # Ensure that attempting populating the values using a read-write
        # transaction and then rolling it back yields the expected values.
        self.assertTrue(populate_values(True, True, key_values))
        self.assertTrue(check_values(self._roll_back_values(key_values)))

        # Ensure that attempting populating the values using a read-write
        # transaction and then committing it stores the expected values.
        self.assertTrue(populate_values(True, False, key_values))
        self.assertTrue(check_values(self._roll_back_values(key_values)))

        # Clean up the keys.
        self.assertTrue(delete_values(key_values))

        return



    # testMetadataTxInterface tests all facets of the managed read/write and
    # manual transaction metadata interfaces as well as the bucket interfaces under
    # them.
    def test_metadata_tx_interface(self, tc):
        self.test_managed_tx_panics(tc)

        bucket1_name = b"bucket1"
        tc.db.update(lambda tx: tx.metadata().create_bucket(bucket1_name))

        self.test_metadata_manual_tx_interface(tc)


    # testInterface tests performs tests for the various interfaces of the database
    # package which require state in the database for the given database type.
    def test_interface(self, db: database.DB):
        # Create a test context to pass around.
        context = TestContext(db=db)

        # Load the test blocks and store in the test context for use throughout
        # the tests.
        blocks = self._load_blocks(blockDataFile, blockDataNet)
        context.blocks = blocks

        # Test the transaction metadata interface including managed and manual
        # transactions as well as buckets.
        self.test_metadata_tx_interface(context)




















