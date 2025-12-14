class InsufficientFundsError(Exception):
    def __init__(self, balance, amount):
        super().__init__(f"Insufficient funds: balance={balance}, amount={amount}")
        self.balance = balance
        self.amount = amount
