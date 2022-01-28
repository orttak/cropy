import boto3
import os
import json

region = os.environ.get('AWS_REGION') 
access_key = os.environ.get('ACCESS_KEY')
secret_key = os.environ.get('SECRET_KEY')
bucket_name = "sentinel2-trial"

s3_client = boto3.client(
    's3',
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name=region
)

def send_file_s3(source_img_path,bucket_name,target_img_path):
    """
    Send each item to target s3 bucket. Data  will be copied under bucket (e.g: bucket_name/target_file.tif)
    If you want to push data under subfolder you can spesify with target_img_path parameter.
        > subfolder1= target_path
        > img_name = output_name.tif
        > target_img_path=f"{subfolder1}/{img_name}"
    """
    response = s3_client.upload_file(source_img_path, bucket_name, target_img_path)

def send_folder_s3(download_path,bucket_name):
    """
    Send target folder to bucket with relative pathname
    
    Sample scnerio
    local path :    "raw_sentinel_without_cloud2/2018-10-30/S2A_37SDA_20181030_0_L2A/S2A_37SDA_20181030_0_L2A_B02_subset.tif"
    realtive path:  "2018-10-30/S2A_37SDA_20181030_0_L2A/S2A_37SDA_20181030_0_L2A_B02_subset.tif"
    
    s3 path> target_bucket/relative_path
             target_bucket/2018-10-30/S2A_37SDA_20181030_0_L2A/S2A_37SDA_20181030_0_L2A_B02_subset.tif
    """
    for root, dirs, files in os.walk(download_path):
        for filename in files:
            # construct the full local path
            local_path = os.path.join(root, filename)
            # construct the full relative path
            relative_path = os.path.relpath(local_path, download_path)
            response = s3_client.upload_file(local_path, bucket_name,relative_path)
        