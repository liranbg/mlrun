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

import pathlib
import re
import typing

import alembic.config
import pytest
import pytest_alembic.plugin.fixtures
import sqlalchemy.engine
from pytest_alembic import MigrationContext
from pytest_alembic.tests import (  # noqa
    test_model_definitions_match_ddl,
    test_single_head_revision,
    test_up_down_consistency,
    test_upgrade,
)

pytest_plugins = [
    "tests.common_fixtures",
    "tests.conftest",
]


class Constants:
    ini_file_path = str(
        pathlib.Path(__file__).absolute().parent.parent.parent.parent / "alembic.ini"
    )
    baseline_revision = "c0e342d73bd0"


@pytest.fixture
def alembic_runner(
    alembic_engine: sqlalchemy.engine.Engine,
) -> typing.Generator[MigrationContext, None, None]:
    config = pytest_alembic.plugin.fixtures.Config(
        alembic_config=alembic.config.Config(
            file_=Constants.ini_file_path,
        ),
    )
    with pytest_alembic.runner(
        config=config,
        engine=alembic_engine,
    ) as runner:
        yield runner


@pytest.mark.alembic
def test_baseline_revision_is_new_root():
    """
    We only support schema upgrades from MLRun >= 1.6.0.
    Therefore, the Alembic migration graph is squashed so that the v1.6.0 head revision is the new base.
    """

    migrations_dir = pathlib.Path(__file__).absolute().parent.parent.parent
    versions_dir = migrations_dir / "versions"

    root_revisions: list[str] = []
    for path in versions_dir.glob("*.py"):
        content = path.read_text(encoding="utf-8")
        revision_match = re.search(
            r"^revision\s*=\s*['\"]([^'\"]+)['\"]\s*$",
            content,
            re.MULTILINE,
        )
        down_revision_match = re.search(
            r"^down_revision\s*=\s*(None|['\"]([^'\"]+)['\"])\s*$",
            content,
            re.MULTILINE,
        )
        if not revision_match or not down_revision_match:
            continue
        if down_revision_match.group(1) == "None":
            root_revisions.append(revision_match.group(1))

    assert sorted(root_revisions) == [Constants.baseline_revision]
