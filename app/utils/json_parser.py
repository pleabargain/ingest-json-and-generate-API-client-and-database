import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging
from ..models.pydantic import LogEntry, OutputContent, PseudoCodeStep

logger = logging.getLogger(__name__)

class JSONParsingError(Exception):
    """Custom exception for JSON parsing errors"""
    pass

def validate_json_structure(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate the basic structure of the JSON log entry
    Returns: (is_valid: bool, error_message: str)
    """
    required_fields = ['model', 'input', 'output', 'response_time_seconds', 'timestamp']
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate output structure
    if not isinstance(data['output'], dict):
        return False, "Output must be a dictionary"
    
    if 'steps' not in data['output']:
        return False, "Output must contain 'steps' array"
    
    if not isinstance(data['output']['steps'], list):
        return False, "Steps must be an array"
    
    # Validate steps structure
    for idx, step in enumerate(data['output']['steps']):
        if not isinstance(step, dict):
            return False, f"Step {idx} must be a dictionary"
        
        required_step_fields = ['step', 'description', 'pseudoCode']
        for field in required_step_fields:
            if field not in step:
                return False, f"Step {idx} missing required field: {field}"
        
        if not isinstance(step['pseudoCode'], list):
            return False, f"Step {idx} pseudoCode must be an array"
    
    return True, ""

def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string to datetime object
    Raises ValueError if invalid format
    """
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError as e:
        raise JSONParsingError(f"Invalid timestamp format: {str(e)}")

def process_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Process a JSON file containing multiple log entries
    Returns list of validated entries
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Handle both single entry and array of entries
        entries = data if isinstance(data, list) else [data]
        validated_entries = []
        
        for entry in entries:
            is_valid, error_msg = validate_json_structure(entry)
            if is_valid:
                # Convert to Pydantic model to ensure full validation
                try:
                    validated_entry = LogEntry(**entry)
                    validated_entries.append(validated_entry.model_dump())
                except Exception as e:
                    logger.error(f"Entry validation failed: {str(e)}")
            else:
                logger.error(f"Invalid entry structure: {error_msg}")
        
        return validated_entries
    
    except json.JSONDecodeError as e:
        raise JSONParsingError(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise JSONParsingError(f"Error processing JSON file: {str(e)}")

def extract_step_info(steps: List[Dict[str, Any]]) -> List[str]:
    """
    Extract descriptions from steps for quick overview
    """
    return [f"Step {step['step']}: {step['description']}" 
            for step in steps]

def analyze_json_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze JSON content and return useful metadata
    """
    try:
        return {
            "model_used": data.get("model"),
            "input_length": len(data.get("input", "")),
            "num_steps": len(data.get("output", {}).get("steps", [])),
            "total_pseudo_code_lines": sum(
                len(step.get("pseudoCode", []))
                for step in data.get("output", {}).get("steps", [])
            ),
            "response_time": data.get("response_time_seconds"),
            "timestamp": parse_timestamp(data.get("timestamp", ""))
        }
    except Exception as e:
        logger.error(f"Error analyzing JSON content: {str(e)}")
        raise JSONParsingError(f"Error analyzing JSON content: {str(e)}")
