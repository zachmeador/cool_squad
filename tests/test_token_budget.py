"""
Tests for the token budget tracking system.
"""

import pytest
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from cool_squad.utils.token_budget import (
    ModelUsage,
    ProviderUsage,
    TokenBudget,
    TokenBudgetTracker,
    get_token_budget_tracker
)


def test_model_usage():
    """test that model usage tracking works correctly"""
    usage = ModelUsage()
    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0
    
    usage.add_usage(100, 50)
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 50
    assert usage.total_tokens == 150
    
    usage.add_usage(50, 25)
    assert usage.prompt_tokens == 150
    assert usage.completion_tokens == 75
    assert usage.total_tokens == 225


def test_provider_usage():
    """test that provider usage tracking works correctly"""
    provider = ProviderUsage()
    assert len(provider.models) == 0
    
    # get non-existent model should create it
    model = provider.get_model("gpt-4")
    assert "gpt-4" in provider.models
    assert model.prompt_tokens == 0
    
    # add usage to a model
    provider.add_usage("gpt-4", 100, 50)
    assert provider.models["gpt-4"].prompt_tokens == 100
    assert provider.models["gpt-4"].completion_tokens == 50
    
    # add usage to another model
    provider.add_usage("claude-3", 200, 100)
    assert "claude-3" in provider.models
    assert provider.models["claude-3"].prompt_tokens == 200
    
    # check total tokens
    assert provider.get_total_tokens() == 450


def test_token_budget():
    """test that token budget limits work correctly"""
    # no limits
    budget = TokenBudget()
    within_budget, _ = budget.is_within_budget(1000, 5000)
    assert within_budget is True
    
    # daily limit only
    budget = TokenBudget(daily_limit=500)
    within_budget, message = budget.is_within_budget(400, 5000)
    assert within_budget is True
    
    within_budget, message = budget.is_within_budget(600, 5000)
    assert within_budget is False
    assert "Daily limit" in message
    
    # monthly limit only
    budget = TokenBudget(monthly_limit=10000)
    within_budget, message = budget.is_within_budget(1000, 9000)
    assert within_budget is True
    
    within_budget, message = budget.is_within_budget(1000, 11000)
    assert within_budget is False
    assert "Monthly limit" in message
    
    # both limits
    budget = TokenBudget(daily_limit=500, monthly_limit=10000)
    within_budget, message = budget.is_within_budget(600, 5000)
    assert within_budget is False
    assert "Daily limit" in message


@pytest.fixture
def mock_data_dir(tmp_path):
    """create a temporary directory for test data"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return str(data_dir)


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_init(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker initializes correctly"""
    mock_get_data_dir.return_value = mock_data_dir
    
    tracker = TokenBudgetTracker()
    assert len(tracker.providers) == 0
    assert len(tracker.provider_budgets) == 0
    assert len(tracker.model_budgets) == 0
    assert isinstance(tracker.daily_reset_time, datetime)
    assert isinstance(tracker.monthly_reset_time, datetime)


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_add_usage(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker can add usage"""
    mock_get_data_dir.return_value = mock_data_dir
    
    tracker = TokenBudgetTracker()
    
    # add usage with no budget constraints
    within_budget, _ = tracker.add_usage("openai", "gpt-4", 100, 50)
    assert within_budget is True
    
    # check that usage was recorded
    assert "openai" in tracker.providers
    assert "gpt-4" in tracker.providers["openai"].models
    assert tracker.providers["openai"].models["gpt-4"].total_tokens == 150
    
    # check daily and monthly usage tracking
    assert tracker.daily_usage["openai"]["gpt-4"] == 150
    assert tracker.monthly_usage["openai"]["gpt-4"] == 150


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_budget_limits(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker enforces budget limits"""
    mock_get_data_dir.return_value = mock_data_dir
    
    tracker = TokenBudgetTracker()
    
    # set provider budget
    tracker.set_provider_budget("openai", daily_limit=500)
    
    # add usage within budget
    within_budget, _ = tracker.add_usage("openai", "gpt-4", 100, 50)
    assert within_budget is True
    
    # add usage that exceeds budget
    within_budget, message = tracker.add_usage("openai", "gpt-4", 300, 100)
    assert within_budget is False
    assert "Daily limit" in message
    
    # set model budget
    tracker.set_model_budget("anthropic", "claude-3", daily_limit=200)
    
    # add usage within budget
    within_budget, _ = tracker.add_usage("anthropic", "claude-3", 100, 50)
    assert within_budget is True
    
    # add usage that exceeds budget
    within_budget, message = tracker.add_usage("anthropic", "claude-3", 100, 50)
    assert within_budget is False
    assert "Model claude-3" in message


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_reset_periods(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker resets usage counters correctly"""
    mock_get_data_dir.return_value = mock_data_dir
    
    tracker = TokenBudgetTracker()
    
    # add some usage
    tracker.add_usage("openai", "gpt-4", 100, 50)
    assert tracker.daily_usage["openai"]["gpt-4"] == 150
    
    # simulate a day passing
    yesterday = datetime.now() - timedelta(days=1)
    tracker.daily_reset_time = yesterday
    
    # check reset
    tracker._check_reset_periods()
    assert "openai" not in tracker.daily_usage
    
    # add usage again
    tracker.add_usage("openai", "gpt-4", 100, 50)
    
    # simulate a month passing
    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    tracker.monthly_reset_time = last_month
    
    # check reset
    tracker._check_reset_periods()
    assert "openai" not in tracker.monthly_usage


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_save_load_state(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker can save and load state"""
    mock_get_data_dir.return_value = mock_data_dir
    
    # create a tracker and add some data
    tracker1 = TokenBudgetTracker()
    tracker1.add_usage("openai", "gpt-4", 100, 50)
    tracker1.set_provider_budget("openai", daily_limit=500)
    tracker1.set_model_budget("anthropic", "claude-3", monthly_limit=10000)
    
    # save state
    tracker1.save_state()
    
    # check that state file exists
    state_file = os.path.join(mock_data_dir, "token_budget_state.json")
    assert os.path.exists(state_file)
    
    # create a new tracker that should load the state
    # make sure the mock is still returning the same directory
    mock_get_data_dir.return_value = mock_data_dir
    tracker2 = TokenBudgetTracker()
    
    # check that budget settings were loaded correctly
    # note: provider usage data is not saved/loaded, only budget settings and usage counters
    assert "openai" in tracker2.provider_budgets
    assert tracker2.provider_budgets["openai"].daily_limit == 500
    assert "anthropic" in tracker2.model_budgets
    assert "claude-3" in tracker2.model_budgets["anthropic"]
    assert tracker2.model_budgets["anthropic"]["claude-3"].monthly_limit == 10000
    
    # check that usage counters were loaded
    assert "openai" in tracker2.daily_usage
    assert "gpt-4" in tracker2.daily_usage["openai"]
    assert tracker2.daily_usage["openai"]["gpt-4"] == 150
    assert "openai" in tracker2.monthly_usage
    assert "gpt-4" in tracker2.monthly_usage["openai"]
    assert tracker2.monthly_usage["openai"]["gpt-4"] == 150


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_save_state_error(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker handles save state errors gracefully"""
    mock_get_data_dir.return_value = mock_data_dir
    
    # create a tracker
    tracker = TokenBudgetTracker()
    
    # make the state file path point to a directory that doesn't exist
    with patch.object(tracker, "get_state_file_path") as mock_get_path:
        mock_get_path.return_value = os.path.join(mock_data_dir, "nonexistent_dir", "token_budget_state.json")
        
        # try to save state, which should fail
        with patch("cool_squad.utils.token_budget.logger") as mock_logger:
            tracker.save_state()
            
            # check that the error was logged
            mock_logger.error.assert_called_once()
            assert "Error saving token budget state" in mock_logger.error.call_args[0][0]


def test_get_token_budget_tracker():
    """test that get_token_budget_tracker returns a singleton instance"""
    # reset the singleton
    import cool_squad.utils.token_budget
    cool_squad.utils.token_budget._token_budget_tracker = None
    
    # get the tracker
    tracker1 = get_token_budget_tracker()
    assert isinstance(tracker1, TokenBudgetTracker)
    
    # get it again, should be the same instance
    tracker2 = get_token_budget_tracker()
    assert tracker1 is tracker2


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_get_usage_report(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker can generate a usage report"""
    mock_get_data_dir.return_value = mock_data_dir
    
    tracker = TokenBudgetTracker()
    
    # add some usage
    tracker.add_usage("openai", "gpt-4", 100, 50)
    tracker.add_usage("anthropic", "claude-3", 200, 100)
    
    # set some budgets
    tracker.set_provider_budget("openai", daily_limit=500)
    tracker.set_model_budget("anthropic", "claude-3", monthly_limit=10000)
    
    # get report
    report = tracker.get_usage_report()
    
    # check report structure
    assert "providers" in report
    assert "daily_usage" in report
    assert "monthly_usage" in report
    assert "budgets" in report
    
    # check provider data
    assert "openai" in report["providers"]
    assert report["providers"]["openai"]["total_tokens"] == 150
    assert "gpt-4" in report["providers"]["openai"]["models"]
    
    # check budget data
    assert report["budgets"]["providers"]["openai"]["daily"] == 500
    assert report["budgets"]["models"]["anthropic"]["claude-3"]["monthly"] == 10000


@patch("cool_squad.utils.token_budget.get_data_dir")
def test_token_budget_tracker_load_state_error(mock_get_data_dir, mock_data_dir):
    """test that token budget tracker handles load state errors gracefully"""
    mock_get_data_dir.return_value = mock_data_dir
    
    # create a state file with invalid json
    state_file = os.path.join(mock_data_dir, "token_budget_state.json")
    with open(state_file, 'w') as f:
        f.write("invalid json")
    
    # create a tracker that should try to load the invalid state
    with patch("cool_squad.utils.token_budget.logger") as mock_logger:
        tracker = TokenBudgetTracker()
        
        # check that the error was logged
        mock_logger.error.assert_called_once()
        assert "Error loading token budget state" in mock_logger.error.call_args[0][0]
    
    # check that the tracker was initialized with default values
    assert len(tracker.providers) == 0
    assert len(tracker.provider_budgets) == 0 