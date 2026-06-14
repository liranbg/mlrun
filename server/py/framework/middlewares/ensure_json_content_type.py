# Copyright 2024 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from starlette.datastructures import MutableHeaders

# ML-12736: pydantic-v1 mlrun clients send request bodies via ``requests data=<json>`` without a
# Content-Type header. FastAPI <= 0.125 parsed such bodies as JSON regardless; FastAPI >= 0.128
# only parses a body as JSON when Content-Type is application/json — otherwise the raw body
# reaches pydantic as a string and validation fails with 422. Default the missing Content-Type
# to application/json for body-bearing requests so existing (unchanged) v1 clients keep working.
# Requests that set an explicit Content-Type (application/yaml, application/zip, multipart/*,
# form-urlencoded, octet-stream, ...) are left untouched.
_BODY_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class EnsureJSONContentTypeMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http" and scope.get("method") in _BODY_METHODS:
            headers = MutableHeaders(scope=scope)
            if not headers.get("content-type"):
                content_length = headers.get("content-length")
                has_body = (
                    content_length not in (None, "", "0")
                    or "transfer-encoding" in headers
                )
                if has_body:
                    headers["content-type"] = "application/json"
        return await self.app(scope, receive, send)
