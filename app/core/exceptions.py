class BetControlException(Exception):
    """Excepción base para el sistema"""
    pass


class InsufficientFundsError(BetControlException):
    """Error cuando no hay fondos suficientes"""
    pass


class InvalidBetAmountError(ValueError):
    """Raised when bet amount is invalid (too high/low)"""
    pass


class UserNotFoundError(BetControlException):
    """Error cuando el usuario no existe"""
    pass


class BetNotFoundError(BetControlException):
    """Error cuando la apuesta no existe"""
    pass


class InvalidBetStatusError(BetControlException):
    """Error cuando el estado de la apuesta es inválido"""
    pass


class DuplicateBetError(BetControlException):
    """Error cuando se intenta crear una apuesta duplicada"""
    pass