import pytest
import json
from pathlib import Path
from app.utils.json_parser import (
    validate_json_structure,
    parse_timestamp,
    analyze_json_content,
    JSONParsingError
)
from app.models.pydantic import LogEntry

# Load test data from source.json
SOURCE_PATH = Path("source.json")
with open(SOURCE_PATH) as f:
    TEST_DATA = json.load(f)

def test_validate_json_structure():
    """Test JSON structure validation"""
    is_valid, error_msg = validate_json_structure(TEST_DATA)
    assert is_valid, f"Source JSON should be valid, but got error: {error_msg}"

def test_parse_timestamp():
    """Test timestamp parsing"""
    timestamp = TEST_DATA['timestamp']
    parsed = parse_timestamp(timestamp)
    assert parsed.year == 2024
    assert parsed.month == 12
    assert parsed.day == 7

def test_analyze_json_content():
    """Test JSON content analysis"""
    analysis = analyze_json_content(TEST_DATA)
    assert analysis['model_used'] == "claude-3-opus-20240229"
    assert analysis['num_steps'] == len(TEST_DATA['output']['steps'])
    assert analysis['response_time'] == TEST_DATA['response_time_seconds']

def test_pydantic_model_validation():
    """Test full Pydantic model validation"""
    try:
        log_entry = LogEntry(**TEST_DATA)
        assert log_entry.model == TEST_DATA['model']
        assert len(log_entry.output.steps) == len(TEST_DATA['output']['steps'])
    except Exception as e:
        pytest.fail(f"Pydantic validation failed: {str(e)}")

def test_invalid_json_structure():
    """Test invalid JSON detection"""
    invalid_data = {
        "model": "test-model",
        # Missing required fields
    }
    is_valid, error_msg = validate_json_structure(invalid_data)
    assert not is_valid
    assert "Missing required field" in error_msg

def test_step_structure():
    """Test steps structure validation"""
    for step in TEST_DATA['output']['steps']:
        assert 'step' in step
        assert 'description' in step
        assert 'pseudoCode' in step
        assert isinstance(step['pseudoCode'], list)
