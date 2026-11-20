class ReefAPIError(Exception):
    """Base exception for ReefAPI errors"""
    pass

class ReefAPIAuthenticationError(ReefAPIError):
    """Raised when authentication fails"""
    pass

class ReefAPIRateLimitError(ReefAPIError):
    """Raised when rate limit is exceeded"""
    pass

class ReefAPIQuotaError(ReefAPIError):
    """Raised when quota is exhausted"""
    pass

class ReefAPITimeoutError(ReefAPIError):
    """Raised when request times out"""
    pass

class ReefAPIInvalidResponseError(ReefAPIError):
    """Raised when response is malformed"""
    pass
