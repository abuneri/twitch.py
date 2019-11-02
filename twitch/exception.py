class TwitchException(Exception):
    pass


class HTTPException(TwitchException):
    def __init__(self, response, error, status=None):
        self.status = response.status if not status else status
        self.response = response
        self.message = None
        if isinstance(error, dict):
            self.message = error.get('message', 'Unknown')
            self.error = error.get('error', '')
        else:
            self.error = error

        reason = f' (reason: {self.message})' if self.message else ''
        e = f'{self.status} {self.error}{reason}'
        super().__init__(e)


class HTTPNotAuthorized(HTTPException):
    def __init__(self, response, error):
        super().__init__(response, error, 401)


class HTTPForbidden(HTTPException):
    def __init__(self, response, error):
        super().__init__(response, error, 403)


class HTTPNotFound(HTTPException):
    def __init__(self, response, error):
        super().__init__(response, error, 404)


class ClientException(TwitchException):
    pass


class WebSocketException(TwitchException):
    def __init__(self, original):
        super().__init__(str(original))


class WebSocketConnectionClosed(WebSocketException):
    pass


class WebSocketLoginFailure(WebSocketException):
    pass
