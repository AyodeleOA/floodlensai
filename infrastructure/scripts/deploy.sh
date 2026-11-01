#!/bin/bash
# FloodLens AI — Backend deployment script
# Requires AWS SAM CLI installed

set -e

echo "Building SAM application..."
sam build

echo "Deploying with guided parameters..."
sam deploy --guided

echo "Done."
