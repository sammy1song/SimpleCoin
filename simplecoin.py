import hashlib
import time
import random
import time
import smtplib
from email.message import EmailMessage
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
     def __init__(self, sender, recipient, amount, signature, tx_type="transfer", contract_address=None, contract_method=None, contract_args=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature
        self.fee = fee
        self.tx_type = tx_type  # New attribute to define the type of transaction
        self.contract_address = contract_address
        self.contract_method = contract_method
        self.contract_args = contract_args


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

# Time lock period in seconds (e.g., 24 hours)
TIME_LOCK_PERIOD = 86400


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


class Channel:
    def __init__(self, party1, party2, deposit1, deposit2):
        self.party1 = party1
        self.party2 = party2
        self.balances1 = {}
        self.balances2 = {}
        self.balance1 = deposit1
        self.balance2 = deposit2
        self.open = True
        self.commitment_transactions = []
        self.close_requested = False
        self.close_request_time = None

    def update(self, amount, signature1, signature2):
        if not self.open:
            print("Channel is closed!")
            return
        # Verify signatures
        if not Wallet.verify_signature(self.party1, signature1, str(amount)) or not Wallet.verify_signature(self.party2, signature2, str(amount)):
            print("Invalid signatures!")
            return
        self.balance1 -= amount
        self.balance2 += amount
        # Store the commitment transaction
        self.commitment_transactions.append((amount, signature1, signature2))
        self.balances1[asset] -= amount
        self.balances2[asset] += amount

    def close(self, transaction_index=None):
        self.open = False
        # If a specific transaction index is provided, close with that state
        if transaction_index and transaction_index < len(self.commitment_transactions):
            amount, _, _ = self.commitment_transactions[transaction_index]
            self.balance1 -= amount
            self.balance2 += amount
        # Logic to settle the final balances on the main chain can be added here

    def request_close(self, transaction_index=None):
        self.close_requested = True
        self.close_request_time = time.time()

    def finalize_close(self):
        if self.close_requested and (time.time() - self.close_request_time) > TIME_LOCK_PERIOD:
            self.close()  # This is the existing close method
        else:
            print("Close request time lock not yet expired.")

    def challenge_close(self, newer_transaction_index):
        if newer_transaction_index > self.last_transaction_index:
            self.last_transaction_index = newer_transaction_index
            self.close_request_time = time.time()  # Reset the timer


class SmartContract:
    def __init__(self, address):
        self.address = address
        self.state = {}

    def call(self, method, args):
        if hasattr(self, method):
            getattr(self, method)(*args)
        else:
            print(f"Method {method} not found in contract.")

    # Example methods
    def set_value(self, key, value):
        self.state[key] = value

    def get_value(self, key):
        return self.state.get(key)

class Watchtower:
    def __init__(self):
        self.monitored_channels = {}  # Key: channel_id, Value: channel_record

    def monitor_channel(self, channel, latest_transaction, signatures):
        self.monitored_channels[channel.id] = {
            'channel': channel,
            'latest_transaction': latest_transaction,
            'signatures': signatures
        }

    def check_channels(self):
        current_time = time.time()
        for channel_id, record in self.monitored_channels.items():
            channel = record['channel']
            if channel.close_requested:
                time_since_request = current_time - channel.close_request_time
                if time_since_request < TIME_LOCK_PERIOD:
                    if record['latest_transaction'].index > channel.last_transaction_index:
                        self.challenge_close(channel, record['latest_transaction'], record['signatures'])
                else:
                    self.notify_user_of_close(channel)

    def challenge_close(self, channel, latest_transaction, signatures):
        # In a real-world scenario, this would involve submitting the challenge to the blockchain
        # Here, we'll just update the channel directly and print a message
        channel.challenge_close(latest_transaction.index)
        print(f"Challenged close for channel {channel.id} with transaction {latest_transaction.index}")

    def notify_user_of_close(self, channel):
        # Send an email notification to the user
        self.send_email_notification(f"Channel {channel.id} Closed", f"Channel {channel.id} has been closed.")

    def send_email_notification(self, subject, body):
        # This is a basic implementation using smtplib; you'd need to set up your SMTP server details
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = 'watchtower@example.com'
        msg['To'] = 'user@example.com'  # This should be the user's email address

        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.login('watchtower@example.com', 'password')  # Use your SMTP server credentials
            server.send_message(msg)

