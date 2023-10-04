import unittest
from simplecoin import Blockchain, Wallet, Transaction

class TestSimpleCoin(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()
        self.wallet1 = Wallet()
        self.wallet2 = Wallet()

    def test_transaction_signature(self):
        transaction = Transaction(self.wallet1.public_key, self.wallet2.public_key, 10, None)
        signature = self.wallet1.sign_transaction(str(transaction))
        self.assertTrue(Wallet.verify_signature(self.wallet1.public_key, signature, str(transaction)))

    def test_add_transaction_to_pool(self):
        transaction = Transaction(self.wallet1.public_key, self.wallet2.public_key, 10, None)
        signature = self.wallet1.sign_transaction(str(transaction))
        self.blockchain.add_transaction_to_pool(transaction, self.wallet1.public_key, signature)
        self.assertIn(transaction, self.blockchain.transaction_pool)

    def test_mine_block(self):
        transaction = Transaction(self.wallet1.public_key, self.wallet2.public_key, 10, None)
        signature = self.wallet1.sign_transaction(str(transaction))
        self.blockchain.add_transaction_to_pool(transaction, self.wallet1.public_key, signature)
        self.blockchain.mine_block(self.wallet2.public_key)
        self.assertIn(transaction, self.blockchain.chain[-1].transactions)

if __name__ == "__main__":
    unittest.main()
