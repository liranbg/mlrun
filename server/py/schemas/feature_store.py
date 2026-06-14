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


import typing

import pydantic

from .auth import AuthorizationResourceTypes, Credentials
from .object import (
    LabelRecord,
    ObjectKind,
    ObjectMetadata,
    ObjectRecord,
    ObjectSpec,
    ObjectStatus,
)


class FeatureStoreBaseModel(pydantic.BaseModel):
    """
    Intermediate base class, in order to override pydantic's configuration, as per
    https://docs.pydantic.dev/1.10/usage/model_config/#change-behaviour-globally
    """

    model_config = pydantic.ConfigDict(copy_on_model_validation="none")


class Feature(FeatureStoreBaseModel):
    model_config = pydantic.ConfigDict(extra="allow")

    name: str
    value_type: str
    labels: dict | None = {}


class Entity(FeatureStoreBaseModel):
    model_config = pydantic.ConfigDict(extra="allow")

    name: str
    value_type: str
    labels: dict | None = {}


class FeatureSetSpec(ObjectSpec):
    entities: list[Entity] = []
    features: list[Feature] = []
    engine: str | None = pydantic.Field(default="storey")


class FeatureSet(FeatureStoreBaseModel):
    kind: typing.Literal[ObjectKind.feature_set] = pydantic.Field(
        ObjectKind.feature_set
    )
    metadata: ObjectMetadata
    spec: FeatureSetSpec
    status: ObjectStatus

    @staticmethod
    def get_authorization_resource_type():
        return AuthorizationResourceTypes.feature_set


class EntityRecord(FeatureStoreBaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    name: str
    value_type: str
    labels: list[LabelRecord]


class FeatureRecord(FeatureStoreBaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    name: str
    value_type: str
    labels: list[LabelRecord]


class FeatureSetRecord(ObjectRecord):
    model_config = pydantic.ConfigDict(from_attributes=True)

    entities: list[EntityRecord]
    features: list[FeatureRecord]


class FeatureSetsOutput(FeatureStoreBaseModel):
    feature_sets: list[FeatureSet]


class FeatureSetsTagsOutput(FeatureStoreBaseModel):
    tags: list[str] = []


class FeatureSetDigestSpec(FeatureStoreBaseModel):
    entities: list[Entity]
    features: list[Feature]


class FeatureSetDigestOutput(FeatureStoreBaseModel):
    metadata: ObjectMetadata
    spec: FeatureSetDigestSpec


class FeatureSetDigestSpecV2(FeatureStoreBaseModel):
    entities: list[Entity]


class FeatureSetDigestOutputV2(FeatureStoreBaseModel):
    feature_set_index: int
    metadata: ObjectMetadata
    spec: FeatureSetDigestSpecV2


class FeatureListOutput(FeatureStoreBaseModel):
    feature: Feature
    feature_set_digest: FeatureSetDigestOutput


class FeaturesOutput(FeatureStoreBaseModel):
    features: list[FeatureListOutput]


class FeaturesOutputV2(FeatureStoreBaseModel):
    features: list[Feature]
    feature_set_digests: list[FeatureSetDigestOutputV2]


class EntityListOutput(FeatureStoreBaseModel):
    entity: Entity
    feature_set_digest: FeatureSetDigestOutput


class EntitiesOutputV2(FeatureStoreBaseModel):
    entities: list[Entity]
    feature_set_digests: list[FeatureSetDigestOutputV2]


class EntitiesOutput(FeatureStoreBaseModel):
    entities: list[EntityListOutput]


class FeatureVector(FeatureStoreBaseModel):
    kind: typing.Literal[ObjectKind.feature_vector] = pydantic.Field(
        ObjectKind.feature_vector
    )
    metadata: ObjectMetadata
    spec: ObjectSpec
    status: ObjectStatus

    @staticmethod
    def get_authorization_resource_type():
        return AuthorizationResourceTypes.feature_vector


class FeatureVectorRecord(ObjectRecord):
    pass


class FeatureVectorsOutput(FeatureStoreBaseModel):
    feature_vectors: list[FeatureVector]


class FeatureVectorsTagsOutput(FeatureStoreBaseModel):
    tags: list[str] = []


class DataSource(FeatureStoreBaseModel):
    model_config = pydantic.ConfigDict(extra="allow")

    kind: str
    name: str
    path: str


class DataTarget(FeatureStoreBaseModel):
    model_config = pydantic.ConfigDict(extra="allow")

    kind: str
    name: str
    path: str | None = None


class FeatureSetIngestInput(FeatureStoreBaseModel):
    source: DataSource | None = None
    targets: list[DataTarget] | None = None
    infer_options: int | None = None
    credentials: Credentials = Credentials()


class FeatureSetIngestOutput(FeatureStoreBaseModel):
    feature_set: FeatureSet
    run_object: dict
