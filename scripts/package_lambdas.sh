#!/bin/bash
# package_lambdas.sh

echo "Packaging Lambda function..."
cd backend
rm -f billing-hourly-fetch.zip
mkdir -p build
cp -r app build/
pip install -r requirements.txt -t build/
cd build
zip -r ../billing-hourly-fetch.zip .
cd ..
rm -rf build
echo "Package created: backend/billing-hourly-fetch.zip"
