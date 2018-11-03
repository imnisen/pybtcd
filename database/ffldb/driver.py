import wire
from .db import *
import database

dbType = "ffldb"


def parse_args(func_name: str, *args):
    if len(args) != 2:
        msg = "invalid arguments to %s.%s -- expected database path and block network" % (dbType, func_name)
        raise Exception(msg)

    db_path = str(args[0])

    network = wire.BitcoinNet.from_string(args[1])  # TOCHECK

    return db_path, network


def open_db_driver(*args):
    db_path, network = parse_args("Open", *args)
    return open_db(db_path, network, False)


def create_db_driver(*args):
    db_path, network = parse_args("Create", *args)
    return open_db(db_path, network, True)


def use_logger(logger):
    pass  # TOADD


def driver_init():
    driver = database.Driver(
        db_type=dbType,
    )
    driver.create = create_db_driver
    driver.open = open_db_driver
    driver.use_logger = use_logger
    database.register_driver(driver)
