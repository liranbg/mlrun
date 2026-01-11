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

import tempfile

import git
import pytest

import mlrun.common.runtimes.constants
import mlrun.runtimes.utils


@pytest.fixture
def repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = git.Repo.init(tmpdir)
        repo.create_remote("origin", "git@github.com:somewhere/else.git")

        # first commit
        tempfilename = "tempfile"
        open(f"{repo.working_dir}/{tempfilename}", "wb").close()
        repo.index.add([tempfilename])
        repo.index.commit("initialcommit")

        yield repo


def test_add_code_metadata_sanity(repo):
    code_metadata = mlrun.runtimes.utils.add_code_metadata(repo.working_dir)
    assert (
        repo.remote("origin").url in code_metadata
    ), "code metadata should contain git info"
    assert (
        repo.head.commit.hexsha in code_metadata
    ), "commit hash should be in code metadata"


def test_add_code_metadata_stale_remote(repo):
    # simulating a malformed / stale remote that has no url attribute
    with open(f"{repo.git_dir}/config", "a") as f:
        f.write('[remote "stale"]\n')

    # origin is still there and valid, use that
    code_metadata = mlrun.runtimes.utils.add_code_metadata(repo.working_dir)
    assert (
        repo.remote("origin").url in code_metadata
    ), "code metadata should contain git info"
    assert (
        repo.head.commit.hexsha in code_metadata
    ), "commit hash should be in code metadata"

    repo.delete_remote(repo.remote("origin"))

    code_metadata = mlrun.runtimes.utils.add_code_metadata(repo.working_dir)
    assert code_metadata is None, "code metadata should be None as there is no remote"


def test_results_to_iter_status_resolution(rundb_mock):
    """
    Test that results_to_iter correctly updates the execution state based on the results provided.
    Results objects contains result of each iteration, including their parameters and status.

    The test first simulates a scenario where one of the iteration fails and is pending a retry,
    then it simulates all iterations being successful.
    """
    results = [
        {
            "spec": {"parameters": {"p1": 2, "p2": 0}},
            "status": {
                "state": "pendingRetry",
                "error": "division by zero",
                "retry_count": None,
            },
        },
        {
            "spec": {"parameters": {"p1": 2, "p2": 1}},
            "status": {"state": "completed", "results": {"multiplier": 2.0}},
        },
        {
            "spec": {"parameters": {"p1": 2, "p2": 2}},
            "status": {"state": "completed", "results": {"multiplier": 1.0}},
        },
    ]
    run = {
        "kind": "run",
        "spec": {
            "log_level": "info",
            "parameters": {"p1": 2, "p2": 0},
            "handler": "my_function",
            "outputs": [],
            "output_path": "artifacts",
            "inputs": {},
            "notifications": [],
            "retry": {"count": 2, "backoff": {"base_delay": "30 sec"}},
            "data_stores": [],
        },
    }
    run = mlrun.run.RunObject.from_dict(run)

    execution = mlrun.execution.MLClientCtx.from_dict(
        run.to_dict(),
        rundb_mock,
        autocommit=False,
        is_api=True,
        store_run=False,
    )
    # Replace execution.commit with a no-op to avoid persisting changes during test
    execution.commit = lambda: None

    mlrun.runtimes.utils.results_to_iter(results, run, execution)
    assert execution.state == mlrun.common.runtimes.constants.RunStates.pending_retry

    # delete the failed result to simulate all iterations being successful
    results = results[1:]
    mlrun.runtimes.utils.results_to_iter(results, run, execution)
    assert execution.state == mlrun.common.runtimes.constants.RunStates.completed
