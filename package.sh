#!/bin/bash
echo "Remove current package wzdx_trigger_ingest.zip"
rm -rf wzdx_trigger_ingest.zip
pip install -r requirements.txt --upgrade --target package/
cp lambda__wzdx_trigger_ingest.py s3_helper.py socrata_util.py wzdx_registry.py package/
mv package/lambda__wzdx_trigger_ingest.py package/lambda_function.py
cd package && zip -r ../wzdx_trigger_ingest.zip * && cd ..
rm -rf package
echo "Created package in wzdx_trigger_ingest.zip"
