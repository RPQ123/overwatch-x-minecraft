"""MC account boundary. No login, credential reads, token storage or network."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
from typing import Protocol

from .config import PackPaths


@dataclass(frozen=True)
class AuthenticatedSession:
    username: str
    uuid: str
    access_token: str = field(repr=False)
    expires_at: float = 0
    ownership_verified: bool = False

    def options(self) -> dict:
        if (not self.username or not self.uuid or not self.access_token
                or self.expires_at <= time.time() or not self.ownership_verified):
            raise ValueError('MC 账号会话未验证、已过期或未确认游戏所有权。')
        return dict(username=self.username, uuid=self.uuid, token=self.access_token, userType='msa')


class AccountProvider(Protocol):
    """Future account-enabled launcher adapter; return an in-memory session only."""
    def session(self) -> AuthenticatedSession: ...


def launch_options(paths: PackPaths, provider: AccountProvider | None = None) -> tuple[dict, bool]:
    if paths.account_mode() == 'external':
        if provider is None:
            raise ValueError('尚未接入 MC 账号提供方；请使用合法账号启动器提供会话。未读取或保存登录凭据。')
        return provider.session().options(), False
    if provider is not None:
        raise ValueError('离线开发模式不能接收账号凭据。')
    # Preserve the existing development identity and localhost-only lab options.
    # This is not a Microsoft login or an ownership assertion.
    from minecraft_launcher_lib.utils import generate_test_options
    identity_file = paths.get('minecraft') / 'development-identity.json'
    if identity_file.is_file():
        identity = json.loads(identity_file.read_text(encoding='utf-8'))
    else:
        identity = generate_test_options()
        identity['username'] = 'OverwatchDev'
        identity_file.write_text(json.dumps(identity, indent=2), encoding='utf-8')
    return {**identity, 'token': ''}, True
