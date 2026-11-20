class FlipkartError(Exception):
    """Base exception for all Flipkart provider errors."""
    pass

class FlipkartAPIError(FlipkartError):
    """Raised when the Flipkart API returns a non-2xx response."""
    def __init__(self, message: str, status_code: int, response_body: str):
        super().__init__(f"Flipkart API Error {status_code}: {message}")
        self.status_code = status_code
        self.response_body = response_body

class FlipkartAuthenticationError(FlipkartAPIError):
    """Raised when authentication fails (e.g., 401 Unauthorized)."""
    pass

class FlipkartRateLimitError(FlipkartAPIError):
    """Raised when the API rate limit is exceeded (e.g., 429 Too Many Requests)."""
    pass

class FlipkartConfigurationError(FlipkartError):
    """Raised when the provider is misconfigured (e.g., missing API keys)."""
    pass

class FlipkartNormalizationError(FlipkartError):
    """Raised when the API response cannot be mapped to the internal ProductData model."""
    pass
