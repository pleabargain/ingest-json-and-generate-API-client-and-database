from flask import Blueprint, request, jsonify
from app.services.log_processor import (
    process_single_log,
    process_batch_logs,
    get_processing_stats,
    get_recent_errors,
    LogProcessingError
)
from app.utils.logger import log_function_call, logger

api = Blueprint('api', __name__)

@api.route('/health')
@log_function_call
def health_check():
    """Health check endpoint
    ---
    get:
      tags:
        - monitoring
      summary: Check API health status
      description: Returns the current health status and basic statistics
      responses:
        200:
          description: Health check successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  total_logs_processed:
                    type: integer
                  total_validation_errors:
                    type: integer
    """
    stats = get_processing_stats()
    return jsonify(stats)

@api.route('/validate', methods=['POST'])
@log_function_call
def validate_log():
    """Validate a single JSON log entry
    ---
    post:
      tags:
        - validation
      summary: Validate a single JSON log entry
      description: Validates the structure and content of a single JSON log entry
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LogEntrySchema'
      responses:
        200:
          description: Validation successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  valid:
                    type: boolean
                  id:
                    type: string
                  message:
                    type: string
        422:
          $ref: '#/components/responses/ErrorResponse'
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    try:
        success, result = process_single_log(request.json)
        if success:
            return jsonify(result), 200
        return jsonify(result), 422
    except Exception as e:
        logger.error(f"Error in validate_log: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/batch/process', methods=['POST'])
@log_function_call
def process_batch():
    """Process a batch of JSON log entries
    ---
    post:
      tags:
        - logs
      summary: Process multiple JSON log entries
      description: Validates and processes multiple JSON log entries in a single request
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BatchRequest'
      responses:
        200:
          description: Batch processing results
          content:
            application/json:
              schema:
                type: object
                properties:
                  total_received:
                    type: integer
                  successfully_processed:
                    type: integer
                  validation_failed:
                    type: integer
                  processing_failed:
                    type: integer
        400:
          $ref: '#/components/responses/ErrorResponse'
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    try:
        result = process_batch_logs(request.json)
        return jsonify(result), 200
    except LogProcessingError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in process_batch: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/errors')
@log_function_call
def get_errors():
    """Get recent validation errors
    ---
    get:
      tags:
        - monitoring
      summary: Retrieve recent validation errors
      description: Returns a list of recent validation errors with details
      parameters:
        - $ref: '#/components/parameters/limit'
      responses:
        200:
          description: List of validation errors
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: string
                    type:
                      type: string
                    message:
                      type: string
                    timestamp:
                      type: string
                      format: date-time
    """
    try:
        limit = request.args.get('limit', default=100, type=int)
        errors = get_recent_errors(limit)
        return jsonify(errors), 200
    except Exception as e:
        logger.error(f"Error in get_errors: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/stats')
@log_function_call
def get_stats():
    """Get processing statistics
    ---
    get:
      tags:
        - monitoring
      summary: Retrieve processing statistics
      description: Returns statistics about processed logs and system status
      responses:
        200:
          description: Processing statistics
          content:
            application/json:
              schema:
                type: object
                properties:
                  total_logs_processed:
                    type: integer
                  total_validation_errors:
                    type: integer
                  last_processed:
                    type: string
                    format: date-time
                  status:
                    type: string
    """
    try:
        stats = get_processing_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({"error": str(e)}), 500
