import hashlib
import time
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes

class Wallet:
    def __init__(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()

    def sign_transaction(self, transaction):
        return self.private_key.sign(transaction.encode(), ec.ECDSA(hashes.SHA256()))

    @staticmethod
    def verify_signature(public_key, signature, transaction):
        return public_key.verify(signature, transaction.encode(), ec.ECDSA(hashes.SHA256()))

class Transaction:
    def __init__(self, sender, recipient, amount, signature):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature

class Block:
    def __init__(self, previous_hash, transactions):
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = "{}{}{}".format(self.timestamp, self.previous_hash, self.transactions).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.transaction_pool = []

    def create_genesis_block(self):
        return Block("0", [])

    def add_transaction_to_pool(self, transaction, sender_public_key, signature):
        if Wallet.verify_signature(sender_public_key, signature, str(transaction)):
            self.transaction_pool.append(transaction)

    def mine_block(self, miner_address):
        if not self.transaction_pool:
            return False

        # Take transactions from the pool to add to the new block (e.g., up to 10 transactions)
        transactions_to_add = self.transaction_pool[:10]
        new_block = Block(self.chain[-1].hash, transactions_to_add)
        self.chain.append(new_block)

        # Clear the added transactions from the pool
        self.transaction_pool = self.transaction_pool[10:]

        # Reward the miner
        self.transaction_pool.append(Transaction("Network", miner_address, 1, None))
        return True

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True
