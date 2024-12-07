from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from app.schemas.validators import LogEntrySchema, OutputSchema, StepSchema

# Create APISpec
spec = APISpec(
    title="JSON Log Processor API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
    info={
        "description": "API for processing and validating JSON logs",
        "contact": {"email": "support@example.com"}
    },
    servers=[
        {
            "url": "/",
            "description": "Development server"
        }
    ],
    tags=[
        {"name": "logs", "description": "Log processing operations"},
        {"name": "validation", "description": "Validation operations"},
        {"name": "monitoring", "description": "Monitoring and statistics"}
    ]
)

# Register schemas with unique names and only once
if "LogEntrySchema" not in spec.components.schemas:
    spec.components.schema("LogEntrySchema", schema=LogEntrySchema)
if "OutputContentSchema" not in spec.components.schemas:
    spec.components.schema("OutputContentSchema", schema=OutputSchema)
if "StepContentSchema" not in spec.components.schemas:
    spec.components.schema("StepContentSchema", schema=StepSchema)

# Add basic security schemes
spec.components.security_scheme("ApiKeyAuth", {
    "type": "apiKey",
    "in": "header",
    "name": "X-API-Key"
})

# Define common responses
spec.components.response("ErrorResponse", {
    "description": "Error response",
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "detail": {"type": "string"}
                }
            }
        }
    }
})

# Define common parameters
spec.components.parameter("limit", {
    "in": "query",
    "name": "limit",
    "schema": {"type": "integer", "default": 100},
    "description": "Maximum number of records to return"
})

# Define request bodies
spec.components.schema(
    "BatchRequest",
    {
        "type": "array",
        "items": {"$ref": "#/components/schemas/LogEntrySchema"}
    }
)

def get_apispec():
    """Get the APISpec object"""
    return spec

def get_swagger_config():
    """Get Swagger UI configuration"""
    return {
        'app_name': "JSON Log Processor API",
        'dom_id': '#swagger-ui',
        'url': '/swagger.json',
        'layout': "BaseLayout",
        'deepLinking': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'syntaxHighlight': {
            'activated': True,
            'theme': "monokai"
        },
        'displayRequestDuration': True,
        'filter': True,
        'supportedSubmitMethods': ['get', 'post'],
        'validatorUrl': None,  # Disable validator
        'oauth2RedirectUrl': None,  # Disable OAuth2
        'docExpansion': 'list'  # Show all endpoints expanded
    }
