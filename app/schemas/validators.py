from marshmallow import Schema, fields, validates_schema, ValidationError, EXCLUDE
from datetime import datetime
from app.utils.logger import log_function_call, log_validation_result, logger

class StepSchema(Schema):
    """Schema for validating individual steps"""
    class Meta:
        unknown = EXCLUDE
    
    step = fields.Integer(required=True)
    description = fields.String(required=True)
    pseudoCode = fields.List(fields.String(), required=True)
    
    @validates_schema
    def validate_step_data(self, data, **kwargs):
        if data['step'] < 1:
            raise ValidationError("Step number must be positive")
        if not data['description'].strip():
            raise ValidationError("Description cannot be empty")
        if not data['pseudoCode']:
            raise ValidationError("PseudoCode list cannot be empty")

class OutputSchema(Schema):
    """Schema for validating the output structure"""
    class Meta:
        unknown = EXCLUDE
    
    steps = fields.List(fields.Nested(StepSchema), required=True)
    
    @validates_schema
    def validate_steps(self, data, **kwargs):
        if not data['steps']:
            raise ValidationError("Output must contain at least one step")
        
        # Verify step numbers are sequential
        step_numbers = [step['step'] for step in data['steps']]
        if sorted(step_numbers) != list(range(1, len(step_numbers) + 1)):
            raise ValidationError("Step numbers must be sequential starting from 1")

class LogEntrySchema(Schema):
    """Schema for validating JSON log entries"""
    class Meta:
        unknown = EXCLUDE
    
    model = fields.String(required=True)
    input = fields.String(required=True)
    output = fields.Nested(OutputSchema, required=True)
    response_time_seconds = fields.Float(required=True)
    timestamp = fields.DateTime(required=True)
    
    @validates_schema
    def validate_log_entry(self, data, **kwargs):
        if not data['model'].strip():
            raise ValidationError("Model name cannot be empty")
        if not data['input'].strip():
            raise ValidationError("Input cannot be empty")
        if data['response_time_seconds'] <= 0:
            raise ValidationError("Response time must be positive")
        if data['timestamp'] > datetime.utcnow():
            raise ValidationError("Timestamp cannot be in the future")

def detect_json_type(data: dict) -> str:
    """
    Detect the type of JSON data
    Returns: str indicating the type ('log_entry', 'schema', 'unknown')
    """
    # Check if it's a JSON Schema
    if '$schema' in data and 'type' in data:
        logger.info("Detected JSON Schema document")
        return 'schema'
    
    # Check if it's a log entry
    if all(key in data for key in ['model', 'input', 'output', 'response_time_seconds', 'timestamp']):
        logger.info("Detected Log Entry document")
        return 'log_entry'
    
    logger.warning("Unknown JSON document type")
    return 'unknown'

@log_function_call
def validate_json_data(data: dict) -> tuple:
    """
    Validate JSON data against appropriate schema
    Returns: (is_valid: bool, result: dict, errors: list)
    """
    try:
        # Detect JSON type
        json_type = detect_json_type(data)
        
        if json_type == 'schema':
            # Validate JSON Schema structure
            required_schema_fields = ['$schema', 'type', 'properties']
            missing_fields = [field for field in required_schema_fields if field not in data]
            
            if missing_fields:
                error_msg = f"Invalid JSON Schema: Missing required fields: {', '.join(missing_fields)}"
                logger.error(error_msg)
                return False, None, [{"field": "schema", "message": error_msg}]
            
            logger.info("Valid JSON Schema document")
            return True, {
                "type": "json_schema",
                "title": data.get('title', 'Untitled Schema'),
                "description": data.get('description', 'No description provided'),
                "properties_count": len(data.get('properties', {}))
            }, None
            
        elif json_type == 'log_entry':
            # Validate log entry
            schema = LogEntrySchema()
            try:
                result = schema.load(data)
                log_validation_result(True, str(data.get('timestamp', 'unknown')))
                return True, result, None
            except ValidationError as e:
                logger.error(f"Log entry validation failed: {str(e)}")
                errors = [
                    {"field": field, "message": ", ".join(messages)}
                    for field, messages in e.messages.items()
                ]
                log_validation_result(False, str(data.get('timestamp', 'unknown')), errors)
                return False, None, errors
        else:
            error_msg = "Unrecognized JSON format"
            logger.error(error_msg)
            return False, None, [{"field": "format", "message": error_msg}]
            
    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(error_msg)
        return False, None, [{"field": "validation", "message": error_msg}]

@log_function_call
def validate_batch(data_list: list) -> tuple:
    """
    Validate a batch of JSON entries
    Returns: (valid_entries: list, invalid_entries: list)
    """
    valid_entries = []
    invalid_entries = []
    
    for idx, entry in enumerate(data_list):
        is_valid, result, errors = validate_json_data(entry)
        if is_valid:
            valid_entries.append(result)
        else:
            invalid_entries.append({
                "index": idx,
                "data": entry,
                "errors": errors
            })
    
    logger.info(f"Batch validation complete. Valid: {len(valid_entries)}, Invalid: {len(invalid_entries)}")
    return valid_entries, invalid_entries
