import hashlib
import time
import random
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes

DIFFICULTY = 4
MAX_TRANSACTIONS_PER_BLOCK = 10
MINING_REWARD = 50

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
    def __init__(self, sender, recipient, amount, signature, tx_type="transfer", fee=1):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature
        self.fee = fee
        self.tx_type = tx_type  # New attribute to define the type of transaction


    def __str__(self):
        return "{}{}{}{}".format(self.sender, self.recipient, self.amount, self.fee)

class Block:
    def __init__(self, previous_hash, transactions):
        self.timestamp = time.time()
        self.previous_hash = previous_hash
        self.nonce = 0 # Added for the Proof-of-Work mechanism
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

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.transaction_pool = []
        self.stakers = {} # New dictionary to keep track of staked coins

    def stake_coins(self, address, amount):
        # Check if the user has enough balance
        balance = self.get_balance(address)
        if balance < amount:
            print("Insufficient funds to stake!")
            return False
        # Add or update the staked amount
        if address in self.stakers:
            self.stakers[address] += amount
        else:
            self.stakers[address] = amount
        # Create a staking transaction
        staking_transaction = Transaction(address, "STAKE_ADDRESS", amount, None, tx_type="stake")
        self.transaction_pool.append(staking_transaction)
        return True

    def select_validator(self):
        # Select a validator based on the number of coins staked
        total_staked = sum(self.stakers.values())
        r = random.randint(1, total_staked)
        for address, stake in self.stakers.items():
            if r <= stake:
                return address
            r -= stake


    def add_transaction_to_pool(self, transaction, sender_public_key, signature):
        # Added validation for transaction amounts
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance < transaction.amount:
            print("Insufficient funds!")
            return False

        if Wallet.verify_signature(sender_public_key, signature, str(transaction)):
            # Replace-by-Fee mechanism: If a transaction with a higher fee comes in, replace the one in the pool
            for idx, old_transaction in enumerate(self.transaction_pool):
                if old_transaction.sender == transaction.sender and old_transaction.recipient == transaction.recipient:
                    if transaction.fee > old_transaction.fee:
                        self.transaction_pool[idx] = transaction
                        return True
            self.transaction_pool.append(transaction)
            return True
        return False

    def create_genesis_block(self):
        return Block("0", [])

    def mine_block(self, miner_address=None):
        if not self.transaction_pool:
            return False

        # Select transactions based on fees (higher fees first) and the set limit
        sorted_transactions = sorted(self.transaction_pool, key=lambda x: x.fee, reverse=True)
        transactions_to_add = sorted_transactions[:MAX_TRANSACTIONS_PER_BLOCK]
        new_block = Block(self.chain[-1].hash, transactions_to_add)
        new_block.mine()  # Proof-of-Work mining

        # PoS: Select a validator based on staked coins
        validator = self.select_validator()
        # Reward the validator
        reward_transaction = Transaction("Network", validator, MINING_REWARD, None, tx_type="reward")
        self.transaction_pool.append(reward_transaction)

        # Clear the added transactions from the pool
        self.transaction_pool = self.transaction_pool[MAX_TRANSACTIONS_PER_BLOCK:]

        # Adjusted reward mechanism
        global MINING_REWARD
        MINING_REWARD *= 0.9  # Reward reduction mechanism

        self.chain.append(new_block)
        return True

    
    def get_balance(self, address):
        # Calculate the balance of an address
        balance = 0
        for block in self.chain:
            for transaction in block.transactions:
                if transaction.sender == address:
                    balance -= transaction.amount
                if transaction.recipient == address:
                    balance += transaction.amount
        for transaction in self.transaction_pool:
            if transaction.sender == address:
                balance -= transaction.amount
            if transaction.recipient == address:
                balance += transaction.amount
        return balance

    def is_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True
