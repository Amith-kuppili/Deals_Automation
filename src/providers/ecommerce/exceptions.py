class ECommerceAPIError(Exception):
    """Base exception for E-Commerce API errors"""
    pass

class ECommerceAuthenticationError(ECommerceAPIError):
    """Raised when authentication fails (401, 403)"""
    pass

class ECommerceRateLimitError(ECommerceAPIError):
    """Raised when rate limit is exceeded (429)"""
    pass

class ECommerceCreditLimitError(ECommerceAPIError):
    """Raised when API credits are insufficient"""
    pass

class ECommerceTimeoutError(ECommerceAPIError):
    """Raised when API request times out"""
    pass

class ECommerceInvalidResponseError(ECommerceAPIError):
    """Raised when API response is malformed or missing expected fields"""
    pass
