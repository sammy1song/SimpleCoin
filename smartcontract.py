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