"""
Unit tests for the data_quality_anomaly functions.
"""

import sys
import os
import pytest
import pandas as pd
from pytest_mock import MockerFixture

# Add scripts folder to sys.path
scripts_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts"))
sys.path.append(scripts_folder)


# pylint: disable=redefined-outer-name
# pylint: disable=import-outside-toplevel
@pytest.fixture
def setup_paths(tmp_path):
    """Fixture to create temporary paths for testing."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    csv_path = tmp_path / "cleaned_data.csv"
    pd.DataFrame(
        {
            "thread_id": ["thread1", "thread1", "thread2"],
            "email_type": ["original", "reply", "forward"],
        }
    ).to_csv(csv_path, index=False)
    return {
        "csv_path": str(csv_path),
        "log_path": str(log_dir / "data_quality_log.log"),
        "logger_name": "test_data_quality_logger",
    }


@pytest.fixture
def oauth_config():
    """Fixture for OAuth configuration."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "refresh_token": "test_refresh_token",
        "sender_email": "test@gmail.com",
    }


@pytest.fixture
def mock_logger(mocker):
    """Fixture for a mock logger."""
    return mocker.MagicMock()


def test_send_email_notification_success_already_valid(
    mocker: MockerFixture, oauth_config, mock_logger
):
    """Test successful email sending with an already valid token."""
    mock_credentials = mocker.MagicMock()
    mock_service = mocker.MagicMock()
    mocker.patch(
        "data_quality_anomaly.Credentials",
        return_value=mock_credentials,
    )
    mocker.patch(
        "data_quality_anomaly.build",
        return_value=mock_service,
    )
    mock_credentials.valid = True
    mock_credentials.token = "valid_token"
    mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = (
        None
    )

    from data_quality_anomaly import send_email_notification

    result = send_email_notification(
        subject="Test Subject",
        body="Test Body",
        to_email="recipient@example.com",
        oauth_config=oauth_config,
        logger=mock_logger,
    )

    assert result is True
    mock_service.users.return_value.messages.return_value.send.assert_called_once()
    mock_logger.info.assert_any_call(
        "Email notification sent successfully to %s", "recipient@example.com"
    )
    mock_logger.error.assert_not_called()


def test_send_email_notification_http_failure(
    mocker: MockerFixture, oauth_config, mock_logger
):
    """Test failure during Gmail API interaction."""
    mock_credentials = mocker.MagicMock()
    mock_service = mocker.MagicMock()
    mocker.patch(
        "data_quality_anomaly.Credentials",
        return_value=mock_credentials,
    )
    mocker.patch(
        "data_quality_anomaly.build",
        return_value=mock_service,
    )
    mock_credentials.valid = True
    mock_credentials.token = "valid_token"
    mock_service.users.return_value.messages.return_value.send.side_effect = Exception(
        "API error"
    )

    from data_quality_anomaly import send_email_notification

    result = send_email_notification(
        subject="Test Subject",
        body="Test Body",
        to_email="recipient@example.com",
        oauth_config=oauth_config,
        logger=mock_logger,
    )

    assert result is False


def test_handle_anomalies_with_anomalies(mocker: MockerFixture, setup_paths):
    """Test handling anomalies with detected issues."""
    mock_logger = mocker.MagicMock()
    mock_ti = mocker.MagicMock()
    mocker.patch(
        "data_quality_anomaly.create_logger",
        return_value=mock_logger,
    )
    mocker.patch(
        "data_quality_anomaly.send_email_notification",
        return_value=True,
    )
    mocker.patch(
        "data_quality_anomaly.os.getenv",
        side_effect=lambda x: (
            "recipient@example.com" if x == "receiver_email" else "test_value"
        ),
    )
    mocker.patch(
        "data_quality_anomaly.pd.read_csv",
        return_value=pd.DataFrame(
            {
                "thread_id": ["thread1", "thread1", "thread2"],
                "email_type": ["original", "reply", "forward"],
            }
        ),
    )

    validation_results = {
        "results": [
            {
                "success": False,
                "expectation_config": {
                    "type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "Body"},
                },
                "result": {
                    "unexpected_count": 5,
                    "unexpected_percent": 10.0,
                    "partial_unexpected_index_list": [1, 2, 3],
                },
            }
        ]
    }
    mock_ti.xcom_pull.side_effect = [validation_results, setup_paths["csv_path"]]

    from data_quality_anomaly import handle_anomalies

    handle_anomalies(
        log_path=setup_paths["log_path"],
        logger_name=setup_paths["logger_name"],
        ti=mock_ti,
    )

    mock_logger.warning.assert_any_call("Anomalies detected:")
    mock_logger.info.assert_any_call(
        "Column: Body, Expectation: expect_column_values_to_not_be_null, "
        "Unexpected Count: 5, Unexpected Percent: 10.0, Partial Indexes: [1, 2, 3]"
    )
    mock_logger.info.assert_any_call("📬 Email notification sent.")
    mock_logger.error.assert_not_called()


def test_handle_anomalies_no_anomalies(mocker: MockerFixture, setup_paths):
    """Test handling when no anomalies are detected."""
    mock_logger = mocker.MagicMock()
    mock_ti = mocker.MagicMock()
    mocker.patch(
        "data_quality_anomaly.create_logger",
        return_value=mock_logger,
    )
    mocker.patch(
        "data_quality_anomaly.send_email_notification",
        return_value=True,
    )
    mocker.patch(
        "data_quality_anomaly.os.getenv",
        side_effect=lambda x: (
            "recipient@example.com" if x == "receiver_email" else "test_value"
        ),
    )
    mocker.patch(
        "data_quality_anomaly.pd.read_csv",
        return_value=pd.DataFrame(
            {
                "thread_id": ["thread1", "thread1", "thread2"],
                "email_type": ["original", "reply", "forward"],
            }
        ),
    )

    validation_results = {
        "results": [
            {
                "success": True,
                "expectation_config": {
                    "type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": "Body"},
                },
                "result": {},
            }
        ]
    }
    mock_ti.xcom_pull.side_effect = [validation_results, setup_paths["csv_path"]]

    from data_quality_anomaly import handle_anomalies

    handle_anomalies(
        log_path=setup_paths["log_path"],
        logger_name=setup_paths["logger_name"],
        ti=mock_ti,
    )

    mock_logger.info.assert_any_call("✅ No actionable anomalies detected.")
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()


if __name__ == "__main__":
    pytest.main(["-v"])
