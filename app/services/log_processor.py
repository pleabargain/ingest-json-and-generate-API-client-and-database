from typing import Dict, List, Tuple
from datetime import datetime
from app.models.database import db, LogEntry, ValidationError
from app.schemas.validators import validate_json_data, validate_batch
from app.utils.logger import log_function_call, logger

class LogProcessingError(Exception):
    """Custom exception for log processing errors"""
    pass

@log_function_call
def process_single_log(data: Dict) -> Tuple[bool, Dict]:
    """
    Process a single JSON file
    Returns: (success: bool, result: dict)
    """
    try:
        is_valid, result, errors = validate_json_data(data)
        
        if not is_valid:
            error_msg = "Validation failed"
            if errors:
                error_msg = errors[0].get('message', 'Unknown validation error')
            
            ValidationError.log_error(
                "ValidationError",
                error_msg,
                {"errors": errors, "data": data}
            )
            return False, {"errors": errors}
        
        # Handle different types of valid JSON
        if isinstance(result, dict) and result.get('type') == 'json_schema':
            logger.info(f"Successfully processed JSON Schema: {result.get('title')}")
            return True, {
                "message": "Valid JSON Schema document",
                "details": {
                    "title": result.get('title'),
                    "description": result.get('description'),
                    "properties": result.get('properties_count')
                }
            }
        
        # For log entries, store in database
        if isinstance(result, dict) and all(key in result for key in ['model', 'input', 'output']):
            log_entry = LogEntry(
                model=result['model'],
                input_text=result['input'],
                output=result['output'],
                response_time=result['response_time_seconds'],
                timestamp=result['timestamp']
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info(f"Successfully processed log entry: {log_entry.id}")
            return True, {
                "message": "Log entry processed successfully",
                "id": log_entry.id
            }
        
        # For other valid JSON types
        logger.info("Successfully processed JSON document")
        return True, {
            "message": "Valid JSON document",
            "type": result.get('type', 'unknown'),
            "details": result
        }
    
    except Exception as e:
        error_msg = f"Error processing JSON: {str(e)}"
        logger.error(error_msg)
        ValidationError.log_error("ProcessingError", error_msg, data)
        return False, {"error": error_msg}

@log_function_call
def process_batch_logs(data_list: List[Dict]) -> Dict:
    """
    Process a batch of JSON entries
    Returns: Summary of processing results
    """
    if not isinstance(data_list, list):
        raise LogProcessingError("Input must be a list of JSON documents")
    
    processed_entries = []
    failed_entries = []
    
    for entry in data_list:
        success, result = process_single_log(entry)
        if success:
            processed_entries.append(result)
        else:
            failed_entries.append(result)
    
    summary = {
        "total_received": len(data_list),
        "successfully_processed": len(processed_entries),
        "processing_failed": len(failed_entries),
        "processed_entries": processed_entries,
        "failed_entries": failed_entries
    }
    
    logger.info(f"Batch processing complete. Success: {len(processed_entries)}, Failed: {len(failed_entries)}")
    return summary

@log_function_call
def get_processing_stats() -> Dict:
    """Get statistics about processed logs"""
    try:
        total_logs = LogEntry.query.count()
        total_errors = ValidationError.query.count()
        latest_log = LogEntry.query.order_by(LogEntry.created_at.desc()).first()
        
        stats = {
            "total_logs_processed": total_logs,
            "total_validation_errors": total_errors,
            "last_processed": latest_log.created_at.isoformat() if latest_log else None,
            "status": "healthy"
        }
        
        logger.info(f"Stats retrieved: {stats}")
        return stats
    except Exception as e:
        error_msg = f"Error getting statistics: {str(e)}"
        logger.error(error_msg)
        return {
            "error": "Failed to retrieve statistics",
            "status": "error",
            "details": str(e)
        }

@log_function_call
def get_recent_errors(limit: int = 100) -> List[Dict]:
    """Get recent validation errors"""
    try:
        errors = ValidationError.query\
            .order_by(ValidationError.created_at.desc())\
            .limit(limit)\
            .all()
        
        error_list = [
            {
                "id": error.id,
                "type": error.error_type,
                "message": error.error_message,
                "timestamp": error.created_at.isoformat(),
                "data": error.data_snapshot
            }
            for error in errors
        ]
        
        logger.info(f"Retrieved {len(error_list)} recent errors")
        return error_list
    except Exception as e:
        error_msg = f"Error retrieving validation errors: {str(e)}"
        logger.error(error_msg)
        return []
