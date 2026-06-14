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

from enum import Enum

from mlrun.common.types import StrEnum

import schemas

# Minimum client version that supports model monitoring,
# Will be fixed when MM will be defined as BC supported feature
MINIMUM_CLIENT_VERSION_FOR_MM = (
    "1.7.0-rc43"  # can be changed to 1.7.0 before 1.7.0 release
)

internal_abort_task_id = "internal-abort"
SYSTEM_ID_KEY = "system_id"


class LogSources(Enum):
    AUTO = "auto"
    PERSISTENCY = "persistency"
    K8S = "k8s"


class MaskOperations(StrEnum):
    CONCEAL = "conceal"
    REDACT = "redact"


# These are alert templates that come built-in with the system and pre-populated on system start
# If we define new system templates, those should be added here

pre_defined_templates = [
    schemas.AlertTemplate(
        template_name="JobFailed",
        template_description="Generic template for job failure alerts",
        system_generated=True,
        summary="A job has failed",
        severity=schemas.alert.AlertSeverity.MEDIUM,
        trigger={"events": [schemas.alert.EventKind.FAILED]},
        reset_policy=schemas.alert.ResetPolicy.AUTO,
    ),
    schemas.AlertTemplate(
        template_name="DataDriftDetected",
        template_description="Generic template for data drift detected alerts",
        system_generated=True,
        summary="Model data drift has been detected",
        severity=schemas.alert.AlertSeverity.HIGH,
        trigger={"events": [schemas.alert.EventKind.DATA_DRIFT_DETECTED]},
        reset_policy=schemas.alert.ResetPolicy.AUTO,
    ),
    schemas.AlertTemplate(
        template_name="DataDriftSuspected",
        template_description="Generic template for data drift suspected alerts",
        system_generated=True,
        summary="Model data drift is suspected",
        severity=schemas.alert.AlertSeverity.MEDIUM,
        trigger={"events": [schemas.alert.EventKind.DATA_DRIFT_SUSPECTED]},
        reset_policy=schemas.alert.ResetPolicy.AUTO,
    ),
]
