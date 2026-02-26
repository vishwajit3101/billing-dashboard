#!/bin/bash
# deploy.sh

echo "Starting deployment..."
./scripts/package_lambdas.sh

cd infrastructure
terraform init
terraform apply -auto-approve
cd ..

echo "Deployment complete."
