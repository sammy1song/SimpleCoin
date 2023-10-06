import time
from wallet import Wallet
from constants import TIME_LOCK_PERIOD


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

    def update(self, asset, amount, signature1, signature2):
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