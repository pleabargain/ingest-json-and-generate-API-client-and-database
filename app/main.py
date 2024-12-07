from flask import Flask, jsonify, send_from_directory, redirect, request, render_template
from flask_swagger_ui import get_swaggerui_blueprint
from app.models.database import db, init_db
from app.routes.api import api
from app.utils.logger import logger, log_function_call
from app.swagger_config import get_apispec, get_swagger_config
from app.services.log_processor import process_single_log
import os
import json
from datetime import datetime

@log_function_call
def create_app(config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
    # Default configuration
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///json_logs.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JSON_SORT_KEYS=False,
        DEBUG=True,
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
    )
    
    # Update with any custom configuration
    if config:
        app.config.update(config)
    
    # Initialize extensions
    init_db(app)
    
    # Create necessary directories
    os.makedirs(app.static_folder, exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    # Serve swagger spec
    @app.route('/swagger.json')
    def serve_swagger_spec():
        return jsonify(get_apispec().to_dict())
    
    # Configure Swagger UI
    swagger_url = '/swagger'
    api_url = '/swagger.json'
    
    swaggerui_blueprint = get_swaggerui_blueprint(
        swagger_url,
        api_url,
        config={
            'app_name': "JSON Log Processor API",
            'dom_id': '#swagger-ui',
            'deepLinking': True,
            'showExtensions': True,
            'showCommonExtensions': True,
            'displayRequestDuration': True,
            'filter': True,
            'supportedSubmitMethods': ['get', 'post'],
            'validatorUrl': None,
            'docExpansion': 'list'
        }
    )
    
    # Register blueprints
    app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)
    app.register_blueprint(api, url_prefix='/api')
    
    @app.route('/upload', methods=['POST'])
    @log_function_call
    def upload_file():
        """Handle JSON file upload"""
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({"error": "Only JSON files are allowed"}), 400
        
        try:
            content = file.read()
            json_data = json.loads(content)
            success, result = process_single_log(json_data)
            
            response = {
                "success": success,
                "timestamp": datetime.now().isoformat(),
                "filename": file.filename,
                "result": result
            }
            
            logger.info(f"File upload processed: {file.filename}, Success: {success}")
            return jsonify(response), 200 if success else 422
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 400
        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            logger.error(error_msg)
            return jsonify({"error": error_msg}), 500

    @app.route('/logs')
    @log_function_call
    def view_logs():
        """View application logs"""
        try:
            log_file = 'logs/app_' + datetime.now().strftime('%Y%m%d') + '.log'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.readlines()
                return render_template('logs.html', logs=logs)
            else:
                logger.warning(f"Log file not found: {log_file}")
                return render_template('logs.html', logs=["No logs found for today"])
        except Exception as e:
            error_msg = f"Error reading logs: {str(e)}"
            logger.error(error_msg)
            return render_template('logs.html', logs=[f"Error reading logs: {error_msg}"])
    
    # Redirect /swagger/ to /swagger
    @app.route('/swagger/')
    def swagger_redirect():
        return redirect('/swagger')
    
    # Root endpoint with improved UI
    @app.route('/')
    @log_function_call
    def root():
        """Root endpoint with API documentation"""
        return render_template('index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
