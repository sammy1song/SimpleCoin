import time
import random
from transaction import Transaction
from block import Block
from channel import Channel
from smartcontract import SmartContract
from constants import DIFFICULTY, MAX_TRANSACTIONS_PER_BLOCK, MINING_REWARD, TIME_LOCK_PERIOD
from wallet import Wallet  # For the verify_signature method

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.transaction_pool = []
        self.stakers = {} # New dictionary to keep track of staked coins
        self.channels = [] # List to store active channels
        self.contracts = {} # Dictionary to store deployed contracts
        self.registered_assets = [] # List to store registered assets
        self.registered_watchtowers = [] # List to store registered watchtowers

    def register_asset(self, asset_name):
        if asset_name not in self.registered_assets:
            self.registered_assets.append(asset_name)

    def register_watchtower(self, watchtower):
        self.registered_watchtowers.append(watchtower)

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

    def challenge_close(self, party1, party2, transaction_index):
        channel = self.find_channel(party1, party2)
        if not channel or channel.open:
            print("Channel not found or still open!")
            return
        # Check if the provided transaction index is more recent
        if transaction_index > len(channel.commitment_transactions) - 1:
            print("Invalid transaction index!")
            return
        channel.close(transaction_index)


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

        # Process each transaction in the pool (including smart contract calls)
        for tx in self.transaction_pool:
            self.process_transaction(tx)

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
    
    def open_channel(self, party1, party2, deposit1, deposit2):
        # Check if both parties have enough balance
        if self.get_balance(party1) < deposit1 or self.get_balance(party2) < deposit2:
            print("Insufficient funds to open channel!")
            return
        new_channel = Channel(party1, party2, deposit1, deposit2)
        self.channels.append(new_channel)

    def find_channel(self, party1, party2):
        for channel in self.channels:
            if (channel.party1 == party1 and channel.party2 == party2) or (channel.party1 == party2 and channel.party2 == party1):
                return channel
        return None

    def update_channel(self, party1, party2, amount, signature1, signature2):
        channel = self.find_channel(party1, party2)
        if not channel:
            print("Channel not found!")
            return
        channel.update(amount, signature1, signature2)

    def close_channel(self, party1, party2):
        channel = self.find_channel(party1, party2)
        if not channel:
            print("Channel not found!")
            return
        channel.close()
        # Logic to settle the final balances on the main chain can be added here

    def process_transaction(self, transaction):
        # Handle regular transfers
        if transaction.tx_type == "transfer":
            sender_balance = self.get_balance(transaction.sender)
            if sender_balance < transaction.amount:
                print("Insufficient funds!")
                return False
            # Update balances (this is a simplified version)
            # In a real-world scenario, you'd add the transaction to a block and then update balances
            self.update_balance(transaction.sender, -transaction.amount)
            self.update_balance(transaction.recipient, transaction.amount)
            return True
        
        # Handle contract calls
        elif transaction.tx_type == "contract" and transaction.contract_address and transaction.contract_method:
            contract = self.contracts.get(transaction.contract_address)
            if contract:
                contract.call(transaction.contract_method, transaction.contract_args)
                return True
            else:
                print("Contract not found!")
                return False

        return False
    
    def deploy_contract(self, contract):
        if contract.address not in self.contracts:
            self.contracts[contract.address] = contract
            print(f"Contract deployed at address {contract.address}")
        else:
            print("Contract address already in use!")

    def request_channel_close(self, party1, party2):
        channel = self.find_channel(party1, party2)
        if channel:
            channel.request_close()

    def finalize_channel_close(self, party1, party2):
        channel = self.find_channel(party1, party2)
        if channel:
            channel.finalize_close()

