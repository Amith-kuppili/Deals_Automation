class AmazonProviderError(Exception):
    """Base exception for Amazon provider errors"""
    pass

class AmazonAuthenticationError(AmazonProviderError):
    """Raised when authentication fails"""
    pass

class AmazonRateLimitError(AmazonProviderError):
    """Raised when rate limit is exceeded"""
    pass

class AmazonQuotaExceededError(AmazonProviderError):
    """Raised when monthly quota is exhausted"""
    pass

class AmazonTimeoutError(AmazonProviderError):
    """Raised when request times out"""
    pass

class AmazonInvalidResponseError(AmazonProviderError):
    """Raised when response is malformed"""
    pass

class AmazonUnavailableError(AmazonProviderError):
    """Raised when provider is unavailable"""
    pass
