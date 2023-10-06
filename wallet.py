import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes

class Wallet:
    def __init__(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()

    def sign_transaction(sEmailMessage
        return self.private_key.sign(transaction.encode(), ec.ECDSA(hashes.SHA256()))

    @staticmethod
    def verify_signature(public_key, signature, transaction):
        return public_key.verify(signature, transaction.encode(), ec.ECDSA(hashes.SHA256()))
