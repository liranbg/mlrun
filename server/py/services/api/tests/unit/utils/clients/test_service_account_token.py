# Copyright 2026 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest import mock

import pytest

import mlrun.common.schemas

import framework.utils.clients.service_account_token as service_account_token

TEST_TOKEN = "test-token"
TEST_NEW_TOKEN = "new-token"
TEST_TOKEN_EXPIRATION_SECONDS = 3600
TEST_TOKEN_EXPIRATION_BUFFER_SECONDS = TEST_TOKEN_EXPIRATION_SECONDS * 0.1


@pytest.fixture
def token_path(tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text(TEST_TOKEN)
    return str(token_file)


@pytest.fixture
def patch_config(token_path):
    service_account_token_client = service_account_token.Client()
    with (
        mock.patch.object(
            service_account_token_client,
            "_TOKEN_PATH",
            token_path,
        ),
        mock.patch.object(
            service_account_token_client,
            "_TOKEN_EXPIRATION_SECONDS",
            TEST_TOKEN_EXPIRATION_SECONDS,
        ),
        mock.patch.object(
            service_account_token_client,
            "_TOKEN_EXPIRATION_BUFFER_SECONDS",
            TEST_TOKEN_EXPIRATION_BUFFER_SECONDS,
        ),
    ):
        yield


@pytest.fixture
def patch_is_token_expired():
    with mock.patch("mlrun.auth.utils.is_token_expired") as is_token_expired_mock:
        yield is_token_expired_mock


def test_token_read_and_cache(patch_config, patch_is_token_expired):
    patch_is_token_expired.return_value = False
    client = service_account_token.Client()
    # First call should read from file and won't check expiration
    token1 = client.token
    assert token1 == TEST_TOKEN
    # Second call should use cache and check expiration
    token2 = client.token
    assert token2 == TEST_TOKEN
    # is_token_expired should be called only once
    assert patch_is_token_expired.call_count == 1


def test_token_expired_forces_reload(patch_config, patch_is_token_expired):
    patch_is_token_expired.side_effect = [True, False]
    client = service_account_token.Client()
    with mock.patch("builtins.open", mock.mock_open(read_data=TEST_NEW_TOKEN)) as m:
        token = client.token
        assert token == TEST_NEW_TOKEN
        m.assert_called_once_with(client._TOKEN_PATH)


def test_auth_headers(patch_config, patch_is_token_expired):
    patch_is_token_expired.return_value = False
    client = service_account_token.Client()
    expected = {
        mlrun.common.schemas.HeaderNames.igz_authenticator_kind: "sa",
        "Authorization": f"Bearer {TEST_TOKEN}",
    }
    assert client.auth_headers == expected


def test_escalate_request_headers(patch_config, patch_is_token_expired):
    patch_is_token_expired.return_value = False
    client = service_account_token.Client()
    original = {"foo": "bar"}
    result = client.escalate_request_headers(original)
    assert result["foo"] == "bar"
    assert result[mlrun.common.schemas.HeaderNames.igz_authenticator_kind] == "sa"
    assert result["Authorization"] == f"Bearer {TEST_TOKEN}"


def test_token_file_missing(patch_config, patch_is_token_expired):
    patch_is_token_expired.return_value = True
    client = service_account_token.Client()
    with mock.patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            _ = client.token


def test_token_strip_whitespace(patch_config, patch_is_token_expired):
    patch_is_token_expired.return_value = True
    client = service_account_token.Client()
    with mock.patch(
        "builtins.open", mock.mock_open(read_data="  token-with-space  \n")
    ):
        token = client.token
        assert token == "token-with-space"


def test_singleton_behavior(patch_config, patch_is_token_expired):
    patch_is_token_expired.return_value = False
    client1 = service_account_token.Client()
    client2 = service_account_token.Client()
    assert client1 is client2


def test_build_sa_auth_info_preserves_user_identity(
    patch_config, patch_is_token_expired
):
    """IG4-2615: build_sa_auth_info swaps creds to SA but keeps audit identity."""
    patch_is_token_expired.return_value = False
    client = service_account_token.Client()
    original = mlrun.common.schemas.AuthInfo(
        request_headers={"foo": "bar", "Authorization": "Bearer user-jwt"},
        username="alice",
        user_id="user-123",
        user_group_ids=["grp-a", "grp-b"],
        token="user-jwt",
        session="user-session-cookie",
        data_session="user-data-session",
        access_key="user-access-key",
        password="user-password",
        projects_role=mlrun.common.schemas.ProjectsRole.mlrun,
        planes=["control"],
        kind=mlrun.common.schemas.AuthInfoKind.user,
    )

    sa_auth_info = client.build_sa_auth_info(original)

    # Audit identity is preserved
    assert sa_auth_info.username == "alice"
    assert sa_auth_info.user_id == "user-123"
    assert sa_auth_info.user_group_ids == ["grp-a", "grp-b"]
    assert sa_auth_info.projects_role == mlrun.common.schemas.ProjectsRole.mlrun
    assert sa_auth_info.planes == ["control"]

    # Kind flips to service_account
    assert sa_auth_info.kind == mlrun.common.schemas.AuthInfoKind.service_account
    assert sa_auth_info.is_service_account()

    # User-bearing secrets are explicitly cleared
    assert sa_auth_info.token is None
    assert sa_auth_info.session is None
    assert sa_auth_info.data_session is None
    assert sa_auth_info.access_key is None
    assert sa_auth_info.password is None

    # Headers carry SA bearer + sa authenticator kind, original headers preserved
    assert sa_auth_info.request_headers["foo"] == "bar"
    assert (
        sa_auth_info.request_headers[
            mlrun.common.schemas.HeaderNames.igz_authenticator_kind
        ]
        == "sa"
    )
    assert sa_auth_info.request_headers["Authorization"] == f"Bearer {TEST_TOKEN}"

    # Original AuthInfo is not mutated
    assert original.kind == mlrun.common.schemas.AuthInfoKind.user
    assert original.token == "user-jwt"
    assert original.request_headers["Authorization"] == "Bearer user-jwt"


def test_build_sa_auth_info_handles_empty_headers(patch_config, patch_is_token_expired):
    """build_sa_auth_info must tolerate AuthInfo with None request_headers."""
    patch_is_token_expired.return_value = False
    client = service_account_token.Client()
    original = mlrun.common.schemas.AuthInfo(username="bob", request_headers=None)

    sa_auth_info = client.build_sa_auth_info(original)

    assert sa_auth_info.username == "bob"
    assert sa_auth_info.kind == mlrun.common.schemas.AuthInfoKind.service_account
    assert (
        sa_auth_info.request_headers[
            mlrun.common.schemas.HeaderNames.igz_authenticator_kind
        ]
        == "sa"
    )
    assert sa_auth_info.request_headers["Authorization"] == f"Bearer {TEST_TOKEN}"
