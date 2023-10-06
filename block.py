import time
import hashlib
from constants import DIFFICULTY


class Block:
    def __init__(self, previous_hash, transactions):
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.nonce = 0  # Added for the Proof-of-Work mechanism
        self.transactions = transactions
        self.hash = self.compute_hash()

    def compute_hash(self):
        block_string = "{}{}{}{}".format(self.timestamp, self.previous_hash, self.transactions, self.nonce).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine(self):
        # Proof-of-Work mechanism
        pattern = '0' * DIFFICULTY
        while not self.hash.startswith(pattern):
            self.nonce += 1
            self.hash = self.compute_hash()
