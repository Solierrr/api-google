import base64
import hashlib
import hmac
import time
from collections.abc import Callable

_DEFAULT_TTL_SECONDS = 600


class InvalidStateError(ValueError):
    pass


class CalendarStateSigner:
    def __init__(
        self, secret: str, *, ttl_seconds: int = _DEFAULT_TTL_SECONDS, clock: Callable[[], float] = time.time
    ) -> None:
        self._secret = secret.encode()
        self._ttl_seconds = ttl_seconds
        self._clock = clock

    def sign(self, technician_id: str) -> str:
        expires_at = int(self._clock()) + self._ttl_seconds
        payload = base64.urlsafe_b64encode(f"{technician_id}.{expires_at}".encode()).decode().rstrip("=")
        return f"{payload}.{self._mac(payload)}"

    def verify(self, state: str) -> str:
        payload, separator, signature = state.rpartition(".")
        if not separator or not hmac.compare_digest(self._mac(payload), signature):
            raise InvalidStateError("state inválido")
        try:
            decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode()
            technician_id, _, expires_at = decoded.rpartition(".")
            expired = int(expires_at) < self._clock()
        except ValueError as exc:
            raise InvalidStateError("state inválido") from exc
        if not technician_id or expired:
            raise InvalidStateError("state expirado" if technician_id else "state inválido")
        return technician_id

    def _mac(self, payload: str) -> str:
        digest = hmac.new(self._secret, payload.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")
