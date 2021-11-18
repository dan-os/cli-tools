import pytest

from codemagic.apple.resources import ProfileType


@pytest.mark.parametrize('profile_type, should_be_allowed', [
    (ProfileType.IOS_APP_ADHOC, True),
    (ProfileType.IOS_APP_DEVELOPMENT, True),
    (ProfileType.IOS_APP_INHOUSE, False),
    (ProfileType.IOS_APP_STORE, False),
    (ProfileType.MAC_APP_DEVELOPMENT, True),
    (ProfileType.MAC_APP_DIRECT, False),
    (ProfileType.MAC_APP_STORE, False),
    (ProfileType.MAC_CATALYST_APP_DEVELOPMENT, True),
    (ProfileType.MAC_CATALYST_APP_DIRECT, False),
    (ProfileType.MAC_CATALYST_APP_STORE, False),
    (ProfileType.TVOS_APP_ADHOC, True),
    (ProfileType.TVOS_APP_DEVELOPMENT, True),
    (ProfileType.TVOS_APP_INHOUSE, False),
    (ProfileType.TVOS_APP_STORE, False),
    (ProfileType.ANY_APP_STORE, False),
])
def test_devices_allowed(profile_type, should_be_allowed):
    assert profile_type.devices_allowed() is should_be_allowed
