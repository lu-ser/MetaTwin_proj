template={
    "swagger": "2.0",
    "info": {
        "title": "API Documentation",
        "description": "API documentation for all endpoints.",
        "version": "3.0"
    },
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "devices": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/Device"
                    }
                }
            }
        },
        "Device": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string"
                },
                "attributes": {
                    "type": "object"
                }
            }
        }
    }
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}