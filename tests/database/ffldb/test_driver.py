import unittest
import database
import database.ffldb as ffldb
from database.ffldb import *
from tests.database.ffldb.test_interface import *
import tempfile
import chaincfg
import shutil

dbType = "ffldb"


class TestDriver(unittest.TestCase):
    # TestCreateOpenFail ensures that errors related to creating and opening a
    # database are handled properly.
    def test_create_open_fail(self):
        # TOADD parapllel

        # Ensure that attempting to open a database that doesn't exist returns
        # the expected error.
        want_err_code = database.ErrorCode.ErrDbDoesNotExist

        with self.assertRaises(database.DBError) as cm:
            database.open(dbType, "noexist", blockDataNet)
        self.assertEqual(cm.exception.c, want_err_code)

        # Ensure that attempting to open a database with the wrong number of
        # parameters returns the expected error.
        with self.assertRaises(InvalidArgNumErr):
            database.open(dbType, 1, 2, 3)

        # Ensure that attempting to open a database with an invalid type for
        # the first parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.open(dbType, 1, blockDataNet)

        # Ensure that attempting to open a database with an invalid type for
        # the second parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.open(dbType, "noexist", "invalid")

        # Ensure that attempting to create a database with the wrong number of
        # parameters returns the expected error.
        with self.assertRaises(InvalidArgNumErr):
            database.create(dbType, 1, 2, 3)

        # Ensure that attempting to create a database with an invalid type for
        # the first parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.create(dbType, 1, blockDataNet)

        # Ensure that attempting to create a database with an invalid type for
        # the second parameter returns the expected error.
        with self.assertRaises(AssertionError):
            database.create(dbType, "noexist", "invalid")

        # Ensure operations against a closed database return the expected
        # error.
        tmp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(tmp_dir.name, "ffldb-createfail")
        tmp_dir.cleanup()
        db = database.create(dbType, db_path, blockDataNet)
        db.close()

        try:
            want_err_code = database.ErrorCode.ErrDbNotOpen
            with self.assertRaises(database.DBError) as cm:
                db.view(lambda tx: None)
            self.assertEqual(cm.exception.c, want_err_code)

            want_err_code = database.ErrorCode.ErrDbNotOpen
            with self.assertRaises(database.DBError) as cm:
                db.update(lambda tx: None)
            self.assertEqual(cm.exception.c, want_err_code)

            want_err_code = database.ErrorCode.ErrDbNotOpen
            with self.assertRaises(database.DBError) as cm:
                db.begin(False)
            self.assertEqual(cm.exception.c, want_err_code)

            want_err_code = database.ErrorCode.ErrDbNotOpen
            with self.assertRaises(database.DBError) as cm:
                db.begin(True)
            self.assertEqual(cm.exception.c, want_err_code)

            want_err_code = database.ErrorCode.ErrDbNotOpen
            with self.assertRaises(database.DBError) as cm:
                db.close()
            self.assertEqual(cm.exception.c, want_err_code)
        finally:
            shutil.rmtree(tmp_dir.name)

    # TestPersistence ensures that values stored are still valid after closing and
    # reopening the database.
    def test_persistence(self):
        # TOADD parallel

        tmp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(tmp_dir.name, "ffldb-persistencetest")
        tmp_dir.cleanup()
        db = database.create(dbType, db_path, blockDataNet)

        try:
            # Create a bucket, put some values into it, and store a block so they
            # can be tested for existence on re-open.
            bucket1_key = b"bucket1"
            store_values = {
                "b1key1": "foo1",
                "b1key2": "foo2",
                "b1key3": "foo3",
            }
            genesis_block = btcutil.Block(chaincfg.MainNetParams.genesis_block)
            genesis_hash = chaincfg.MainNetParams.genesis_hash

            def _test_put_vals(tx: database.Tx):
                metadata_bucket = tx.metadata()
                self.assertIsNotNone(metadata_bucket)

                bucket1 = metadata_bucket.create_bucket(bucket1_key)

                for k, v in store_values.items():
                    bucket1.put(k.encode(), v.encode())

                tx.store_block(genesis_block)

                return

            db.update(_test_put_vals)

            # Close and reopen the database to ensure the values persist.
            db.close()

            db = database.open(dbType, db_path, blockDataNet)

            def _test_get_vals(tx: database.Tx):
                metadata_bucket = tx.metadata()
                self.assertIsNotNone(metadata_bucket)

                bucket1 = metadata_bucket.bucket(bucket1_key)
                self.assertIsNotNone(bucket1)

                for k, v in store_values.items():
                    got_val = bucket1.get(k.encode())
                    self.assertEqual(got_val, v.encode())

                genesis_block_bytes = genesis_block.bytes()
                got_bytes = tx.fetch_block(genesis_hash)
                self.assertEqual(got_bytes, genesis_block_bytes)

                return

            db.view(_test_get_vals)

            return
        finally:
            db.close()
            shutil.rmtree(tmp_dir.name)

    # TestInterface performs all interfaces tests for this database driver.
    def test_interface(self):
        # TOADD parallel
        tmp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(tmp_dir.name, "ffldb-persistencetest")
        tmp_dir.cleanup()
        db = database.create(dbType, db_path, blockDataNet)
        try:
            self.assertEqual(db.type(), dbType)

            def f():
                TestInterface()._test_interface(db)

            test_run_with_max_block_file_size(db, 2048, f)
        except Exception as e:
            pass

        finally:
            db.close()
            shutil.rmtree(tmp_dir.name)


def test_run_with_max_block_file_size(idb, size: int, fn):
    origin_size = idb.store.max_block_file_size

    idb.store.max_block_file_size = size
    fn()
    idb.store.max_block_file_size = origin_size
