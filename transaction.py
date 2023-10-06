class Transaction:
    def __init__(self, sender, recipient, amount, signature, fee, tx_type="transfer", contract_address=None, contract_method=None, contract_args=None):
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
