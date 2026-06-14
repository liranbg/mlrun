# Copyright 2023 Iguazio
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

# ML-12736: server-side native pydantic 2 mirror of mlrun.common.schemas.object.
# The client/SDK keeps the pydantic.v1 version in mlrun/common/schemas/.

from datetime import datetime

from pydantic import BaseModel, ConfigDict

import mlrun.common.types


class ObjectMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    project: str | None = None
    tag: str | None = None
    labels: dict | None = {}
    updated: datetime | None = None
    created: datetime | None = None
    uid: str | None = None


class ObjectStatus(BaseModel):
    model_config = ConfigDict(extra="allow")

    state: str | None = None


class ObjectSpec(BaseModel):
    model_config = ConfigDict(extra="allow")


class LabelRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    value: str


class ObjectRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    project: str
    uid: str
    updated: datetime | None = None
    labels: list[LabelRecord]
    # state is extracted from the full status dict to enable queries
    state: str | None = None
    full_object: dict | None = None


class ObjectKind(mlrun.common.types.StrEnum):
    project = "project"
    feature_set = "FeatureSet"
    background_task = "BackgroundTask"
    feature_vector = "FeatureVector"
    model_endpoint = "model-endpoint"
    hub_source = "HubSource"
    hub_item = "HubItem"
    hub_catalog = "HubCatalog"


class ObjectStatusState(mlrun.common.types.StrEnum):
    CREATED = "created"
