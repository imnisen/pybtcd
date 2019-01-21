

# About pybtcd

This project is a python fork of [btcd](https://github.com/btcsuite/btcd) which is a full node golang bitcoin implementation.

Now this project is for self-education purpose, under active development.


# Project Status

-   wire: Done
-   chainhash: Done
-   chaincfg: Done
-   txscript: Almost(lacking checkmultisigverify)
-   database: Done(need more test case)
-   blockchain: Done(need more test case)
-   btcec: Finish needed
-   btcutil: Finish needed
-   mining: Doing(stuck, need easy python concurrent programming methods)
-   mempool: Todo
-   peer, netsync, connmgr, addrmgr: Todo
-   rpclient, cmd: Todo
-   btcjson: Todo


# Technical debts

-   Move const in test case out in one file
-   change: `read_variable_bytes` and `read_var_bytes` are too similar
-   The unittest seems very slow at some tests, figure out why
-   txscript/standard txscript/script very messy, Change the structure of whole txscript
-   Change the mix ecdsa cryptools thing in btcec to ecdsa methods
-   Change the ScriptNum to subclass int? and other same class can also do so
-   A much pythonic way to implenmetate treap structure
-   Finish test case for txscript
-   Reconsider of time struct of python, now is int, need a class?
-   Use subclass of Enum or Int  to refactor some class
-   Add helper decorator to database, to easy life
-   Add more test case for database packages. now let's just move on
-   Refactor `the_` field things
-   refactor `txscript_flag` to int
-   refacto BlockStatus to inherit bytes
-   Find unbuffer channel like mechanism to finish blockchain/upgrade `interrupt_requested`
-   Refactor whole logger things
-   Rethink when methods return [], return None instead? How to choose?
-   Refactor `blockchain/script_val` with aiochan
-   Finish and finish cpuminer.waitgroup


# Others


## Tags used

-   \#TOCHANGE
-   \#TOCHECK
-   \#TOCLEAN
-   \#TOADD
-   \#TOCONSIDER

