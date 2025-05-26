# Digital Twin Platform API Documentation

## Overview

This platform allows you to create and manage IoT devices and their digital twins. The system supports two approaches: devices based on a predefined ontology (which isn't necessary for normal use) and devices based on custom templates. 
## Authentication

Before using the APIs, you need to register and obtain an access token.

### Registration

```bash
POST /auth/register
Content-Type: application/json

{
    "name": "Your Name",
    "email": "email@example.com", 
    "password": "password123"
}
```

### Login

```bash
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=email@example.com&password=password123
```

You'll receive an `access_token` that you must include in subsequent requests as `Authorization: Bearer {token}`.

## Template Management

Templates define the structure of your devices. You can create completely custom templates instead of using the predefined ontology.

### Create a Custom Template

```bash
POST /templates/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "name": "Environmental Sensor Template",
    "description": "Template for environmental sensors",
    "version": "1.0.0",
    "attributes": {
        "temperature": {
            "name": "temperature",
            "type": "number",
            "unit_measure": "°C",
            "description": "Temperature measurement",
            "constraints": {
                "required": true,
                "min_value": -50,
                "max_value": 100
            }
        },
        "humidity": {
            "name": "humidity", 
            "type": "number",
            "unit_measure": "%",
            "description": "Humidity measurement",
            "constraints": {
                "required": true,
                "min_value": 0,
                "max_value": 100
            }
        }
    },
    "is_ontology_based": false
}
```

### List Existing Templates

```bash
GET /templates/
Authorization: Bearer {your_token}
```

## Device Management

Once you have a template, you can create devices based on it.

### Create a Device from Template

```bash
POST /devices/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "name": "Office Sensor",
    "template_id": "{template_id}",
    "attributes": {
        "temperature": {
            "value": 23.5,
            "unit_measure": "°C"
        },
        "humidity": {
            "value": 65.2,
            "unit_measure": "%"
        }
    }
}
```

This will automatically create an associated digital twin as well. You'll receive an `api_key` that the device can use to send data.

### Send Data from Device

Devices can send data using their API key:

```bash
POST /devices/data
X-API-Key: {device_api_key}
Content-Type: application/json

{
    "temperature": 24.1,
    "humidity": 67.8
}
```

### List Devices

```bash
GET /devices/
Authorization: Bearer {your_token}
```

## Digital Twins

Digital twins are automatically created when you create a device, but you can also manage them directly.

### List Digital Twins

```bash
GET /digital-twins/
Authorization: Bearer {your_token}
```

### Get Data from a Digital Twin

```bash
GET /digital-twins/{digital_twin_id}/data
Authorization: Bearer {your_token}
```

### Generate Random Data (for Testing)

```bash
POST /digital-twins/{digital_twin_id}/generate-data
Authorization: Bearer {your_token}
```

## User Management

### Create Additional Users

```bash
POST /users/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "name": "New User",
    "email": "newuser@example.com"
}
```

### Get User's Devices

```bash
GET /users/{user_id}/devices
Authorization: Bearer {your_token}
```

## Notes on Ontology

The system includes a predefined ontology with various sensor types (altimeter, heart rate monitor, etc.), but you don't need to use it. Custom templates offer greater flexibility and are the recommended approach for most use cases.

If you still want to explore the ontology:

```bash
GET /sensors/types  # List all available types
GET /sensors/types/{sensor_type}  # Details of a specific type
```

