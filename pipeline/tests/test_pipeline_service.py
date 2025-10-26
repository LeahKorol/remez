"""
Unit tests for pipeline_service functions
"""

import json
from datetime import datetime
from pathlib import Path

import pytest
from constants import RorFields, TaskStatus
from errors import DataFilesNotFoundError
from models.models import TaskResults
from models.schemas import PipelineRequest
from services.pipeline_service import (
    cleanup,
    get_available_data,
    mark_data,
    save_results_to_db,
    verify_data_files_exist,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_task():
    return TaskResults(
        id=1,
        external_id="test_ext_001",
        status=TaskStatus.RUNNING,
        created_at=datetime.now(),
    )


@pytest.fixture
def results_file_with_data(tmp_path):
    results_data = {
        "ror_values": [1.5, 2.0, 1.8],
        "ror_lower": [1.2, 1.7, 1.5],
        "ror_upper": [1.8, 2.3, 2.1],
    }

    results_file = tmp_path / "results.json"
    with open(results_file, "w") as f:
        json.dump(results_data, f)

    return results_file


@pytest.fixture
def results_file_empty(tmp_path):
    results_data = {"ror_values": [], "ror_lower": [], "ror_upper": []}

    results_file = tmp_path / "results.json"
    with open(results_file, "w") as f:
        json.dump(results_data, f)

    return results_file


@pytest.fixture
def external_data_dir(tmp_path):
    external_dir = tmp_path / "external_data"
    external_dir.mkdir()
    return external_dir


@pytest.fixture
def pipeline_request():
    return PipelineRequest(
        year_start=2023,
        quarter_start=1,
        year_end=2023,
        quarter_end=3,
        drugs=["aspirin", "ibuprofen"],
        reactions=["headache", "nausea"],
        control=["placebo"],
        external_id="test_request_001",
    )


@pytest.fixture
def create_faers_files():
    def _create_files(directory: Path, quarters: list, file_types: list = None):
        if file_types is None:
            file_types = ["demo", "drug", "outc", "reac"]

        created_files = []
        for quarter in quarters:
            for file_type in file_types:
                file_path = directory / f"{file_type}{quarter}.csv.zip"
                file_path.touch()
                created_files.append(file_path)

        return created_files

    return _create_files


@pytest.fixture
def calculation_directory(tmp_path):
    calc_dir = tmp_path / "calculations"
    calc_dir.mkdir()

    (calc_dir / "subdir1").mkdir()
    (calc_dir / "subdir2").mkdir()
    (calc_dir / "file1.txt").touch()
    (calc_dir / "subdir1" / "file2.txt").touch()
    (calc_dir / "subdir2" / "file3.txt").touch()

    return calc_dir


@pytest.fixture
def mark_data_params(tmp_path):
    return {
        "year_q_from": "2023q1",
        "year_q_to": "2023q2",
        "dir_external": tmp_path / "external",
        "config_dict": {
            "drug": ["aspirin"],
            "reaction": ["headache"],
            "control": ["placebo"],
        },
        "marked_data_dir": tmp_path / "marked_data",
    }


# ============================================================================
# TESTS FOR save_results_to_db
# ============================================================================


def test_save_results_to_db_with_valid_data(
    sample_task, results_file_with_data, mocker
):
    mock_task_repository = mocker.patch(
        "services.pipeline_service.TaskRepository.save_task_results"
    )
    mock_get_ror_fields = mocker.patch("services.pipeline_service.get_ror_fields")
    mock_get_ror_fields.return_value = {
        RorFields.ROR_VALUES: [1.5, 2.0, 1.8],
        RorFields.ROR_LOWER: [1.2, 1.7, 1.5],
        RorFields.ROR_UPPER: [1.8, 2.3, 2.1],
    }

    save_results_to_db(sample_task, results_file_with_data)

    assert sample_task.status == TaskStatus.COMPLETED
    assert sample_task.completed_at is not None
    assert isinstance(sample_task.completed_at, datetime)
    assert sample_task.ror_values == [1.5, 2.0, 1.8]
    assert sample_task.ror_lower == [1.2, 1.7, 1.5]
    assert sample_task.ror_upper == [1.8, 2.3, 2.1]

    mock_task_repository.assert_called_once_with(sample_task)
    mock_get_ror_fields.assert_called_once_with(results_file_with_data)


def test_save_results_to_db_with_empty_data(sample_task, results_file_empty, mocker):
    mock_task_repository = mocker.patch(
        "services.pipeline_service.TaskRepository.save_task_results"
    )
    mock_get_ror_fields = mocker.patch("services.pipeline_service.get_ror_fields")
    mock_get_ror_fields.return_value = {
        RorFields.ROR_VALUES: [],
        RorFields.ROR_LOWER: [],
        RorFields.ROR_UPPER: [],
    }

    save_results_to_db(sample_task, results_file_empty)

    assert sample_task.status == TaskStatus.COMPLETED
    assert sample_task.completed_at is not None
    assert sample_task.ror_values == []
    assert sample_task.ror_lower == []
    assert sample_task.ror_upper == []

    mock_task_repository.assert_called_once_with(sample_task)


# ============================================================================
# TESTS FOR cleanup
# ============================================================================


def test_cleanup_removes_directory_when_enabled(calculation_directory, mocker):
    mock_settings = mocker.patch("services.pipeline_service.settings")
    mock_settings.PIPELINE_CLEAN_INTERNAL_DIRS = True

    assert calculation_directory.exists()
    assert len(list(calculation_directory.iterdir())) > 0

    cleanup(calculation_directory)

    assert not calculation_directory.exists()


def test_cleanup_preserves_directory_when_disabled(calculation_directory, mocker):
    mock_settings = mocker.patch("services.pipeline_service.settings")
    mock_settings.PIPELINE_CLEAN_INTERNAL_DIRS = False

    assert calculation_directory.exists()
    original_files = list(calculation_directory.rglob("*"))

    cleanup(calculation_directory)

    assert calculation_directory.exists()
    remaining_files = list(calculation_directory.rglob("*"))
    assert len(remaining_files) == len(original_files)


# ============================================================================
# TESTS FOR verify_data_files_exist
# ============================================================================


def test_verify_data_files_exist_all_quarters_complete(
    external_data_dir, pipeline_request, create_faers_files, mocker
):
    mocker.patch("services.pipeline_service.task_logger")

    create_faers_files(external_data_dir, ["2023q1", "2023q2"])

    available_quarters = verify_data_files_exist(pipeline_request, external_data_dir)

    assert len(available_quarters) == 2
    assert set(available_quarters) == {"2023q1", "2023q2"}


def test_verify_data_files_exist_missing_quarters_raises_error(
    external_data_dir, pipeline_request, create_faers_files, mocker
):
    mocker.patch("services.pipeline_service.task_logger")

    create_faers_files(external_data_dir, ["2023q1"])
    create_faers_files(external_data_dir, ["2023q2"], file_types=["demo", "drug"])

    with pytest.raises(DataFilesNotFoundError) as exc_info:
        verify_data_files_exist(pipeline_request, external_data_dir)

    error = exc_info.value
    assert "2023q1" in error.requested_quarters
    assert "2023q2" in error.requested_quarters
    assert len(error.available_quarters) < len(error.requested_quarters)


# ============================================================================
# TESTS FOR mark_data
# ============================================================================


def test_mark_data_calls_mark_data_main_with_correct_parameters(
    mark_data_params, mocker
):
    mock_task_logger = mocker.patch("services.pipeline_service.task_logger")
    mock_settings = mocker.patch("services.pipeline_service.settings")
    mock_settings.PIPELINE_THREADS = 4
    mock_mark_data_main = mocker.patch("services.pipeline_service.mark_data_main")

    mark_data(**mark_data_params)

    mock_mark_data_main.assert_called_once_with(
        year_q_from=mark_data_params["year_q_from"],
        year_q_to=mark_data_params["year_q_to"],
        dir_in=str(mark_data_params["dir_external"]),
        config_dict=mark_data_params["config_dict"],
        dir_out=str(mark_data_params["marked_data_dir"]),
        threads=4,
        clean_on_failure=False,
        custom_logger=mock_task_logger,
    )


def test_mark_data_logs_start_and_completion_messages(mark_data_params, mocker):
    mock_task_logger = mocker.patch("services.pipeline_service.task_logger")
    mock_settings = mocker.patch("services.pipeline_service.settings")
    mock_settings.PIPELINE_THREADS = 2
    mocker.patch("services.pipeline_service.mark_data_main")

    mark_data(**mark_data_params)

    mock_task_logger.info.assert_any_call("Starting Step 1: Mark data")
    mock_task_logger.info.assert_called_with("Data marking step completed successfully")


# ============================================================================
# TESTS FOR get_available_data
# ============================================================================


def test_get_available_data_with_complete_quarters(
    external_data_dir, create_faers_files, mocker
):
    mock_settings = mocker.patch("services.pipeline_service.settings")
    mock_settings.get_external_data_path.return_value = external_data_dir

    create_faers_files(external_data_dir, ["2023q1", "2023q2", "2023q3"])

    result = get_available_data()

    assert len(result.complete_quarters) == 3
    assert set(result.complete_quarters) == {"2023q1", "2023q2", "2023q3"}
    assert len(result.incomplete_quarters) == 0
    assert len(result.file_details) == 3

    for quarter in ["2023q1", "2023q2", "2023q3"]:
        assert quarter in result.file_details
        assert result.file_details[quarter].complete is True
        assert len(result.file_details[quarter].files) == 4


def test_get_available_data_with_incomplete_quarters(
    external_data_dir, create_faers_files, mocker
):
    mock_settings = mocker.patch("services.pipeline_service.settings")
    mock_settings.get_external_data_path.return_value = external_data_dir

    create_faers_files(external_data_dir, ["2023q1"])
    create_faers_files(external_data_dir, ["2023q2"], file_types=["demo", "drug"])

    result = get_available_data()

    assert len(result.complete_quarters) == 1
    assert "2023q1" in result.complete_quarters
    assert len(result.incomplete_quarters) == 1
    assert "2023q2" in result.incomplete_quarters

    assert result.file_details["2023q1"].complete is True
    assert len(result.file_details["2023q1"].files) == 4
    assert result.file_details["2023q2"].complete is False
    assert len(result.file_details["2023q2"].files) == 2
