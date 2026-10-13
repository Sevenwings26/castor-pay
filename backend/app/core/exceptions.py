class PaymentGatewayException(Exception):
    """Base exception for all CastorPay platform errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class LedgerImbalanceError(PaymentGatewayException):
    """Raised when sum(debits) != sum(credits) in a journal entry."""

    def __init__(self, total_debit: int, total_credit: int, currency: str):
        diff = total_debit - total_credit
        message = (
            f"Ledger entry violates fundamental accounting equation: "
            f"Debits ({total_debit}) != Credits ({total_credit}) "
            f"[Diff: {diff} {currency}]"
        )
        super().__init__(message, code="LEDGER_IMBALANCE", status_code=422)
        self.total_debit = total_debit
        self.total_credit = total_credit
        self.currency = currency


class InsufficientFundsError(PaymentGatewayException):
    """Raised when an account does not have sufficient liquidity for a withdrawal/transfer."""

    def __init__(self, account_id: str, available_balance: int, requested_amount: int, currency: str):
        message = (
            f"Insufficient funds in account {account_id}: "
            f"Available: {available_balance} {currency}, Requested: {requested_amount} {currency}"
        )
        super().__init__(message, code="INSUFFICIENT_FUNDS", status_code=400)
        self.account_id = account_id
        self.available_balance = available_balance
        self.requested_amount = requested_amount
        self.currency = currency


class IdempotencyConflictError(PaymentGatewayException):
    """Raised when an identical idempotent request is currently being processed concurrently."""

    def __init__(self, idempotency_key: str):
        message = (
            f"A request with Idempotency-Key '{idempotency_key}' is currently processing. "
            "Please retry in a few moments."
        )
        super().__init__(message, code="IDEMPOTENCY_IN_FLIGHT", status_code=409)
        self.idempotency_key = idempotency_key


class QuoteExpiredError(PaymentGatewayException):
    """Raised when a 60-second guaranteed FX quote has expired before execution."""

    def __init__(self, quote_id: str, expired_at: str):
        message = f"FX Quote '{quote_id}' expired at {expired_at}. Please request a fresh quote."
        super().__init__(message, code="FX_QUOTE_EXPIRED", status_code=400)
        self.quote_id = quote_id
        self.expired_at = expired_at


class ProviderUnavailableError(PaymentGatewayException):
    """Raised when an external bank or payment provider is unreachable or rejects processing."""

    def __init__(self, provider_name: str, reason: str = "Service unavailable"):
        message = f"Payment rail '{provider_name}' failed to process transaction: {reason}"
        super().__init__(message, code="PROVIDER_UNAVAILABLE", status_code=502)
        self.provider_name = provider_name
        self.reason = reason


class AccountNotFoundError(PaymentGatewayException):
    """Raised when a requested ledger account does not exist."""

    def __init__(self, account_id: str):
        message = f"Ledger account '{account_id}' not found."
        super().__init__(message, code="ACCOUNT_NOT_FOUND", status_code=404)
        self.account_id = account_id


class EscrowTransitionError(PaymentGatewayException):
    """Raised when an invalid state transition is attempted on an escrow contract."""

    def __init__(self, current_status: str, requested_action: str):
        message = f"Cannot perform action '{requested_action}' on escrow in '{current_status}' status."
        super().__init__(message, code="INVALID_ESCROW_TRANSITION", status_code=400)


class SignatureVerificationError(PaymentGatewayException):
    """Raised when inbound webhook HMAC signature is missing or fails verification."""

    def __init__(self, provider: str):
        message = f"HMAC-SHA256 signature verification failed for webhook from '{provider}'."
        super().__init__(message, code="INVALID_WEBHOOK_SIGNATURE", status_code=401)
