#!/bin/bash
# Script per deploy su PythonAnywhere

echo "Deploying to PythonAnywhere..."

# Set environment variables
export MONGODB_URL="your_atlas_connection_string"
export SECRET_KEY="your-secret-key"

# Install requirements
pip3.10 install --user -r requirements.txt

# Create data directory
mkdir -p /home/lser93/mysite/data

# Copy configuration files
cp data/class_hierarchy.json /home/lser93/mysite/data/

echo "Deployment completed!"