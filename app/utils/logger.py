import logging
import functools
import time
from pathlib import Path
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(funcName)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("json_processor")

def log_function_call(func):
    """Decorator to log function calls with timing"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(f"Failed after {execution_time:.2f} seconds")
            raise
    
    return wrapper

def log_error(error_type: str, message: str, extra_data: dict = None):
    """Utility function to log errors with additional context"""
    error_context = {
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "extra_data": extra_data or {}
    }
    logger.error(f"Error occurred: {error_type}", extra={"error_details": error_context})
    return error_context

def log_validation_result(is_valid: bool, data_id: str, errors: list = None):
    """Utility function to log validation results"""
    if is_valid:
        logger.info(f"Validation successful for data_id: {data_id}")
    else:
        logger.warning(
            f"Validation failed for data_id: {data_id}",
            extra={"validation_errors": errors}
        )
