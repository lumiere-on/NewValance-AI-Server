import os, json, boto3
from botocore.exceptions import ClientError
from datetime import datetime
from pathlib import Path
from .logger import logger
from dotenv import load_dotenv
load_dotenv()  

AWS_REGION  = os.getenv("AWS_REGION", "ap-northeast-2")
BUCKET_NAME = os.getenv("S3_BUCKET",  "newvalance")

s3 = boto3.client(
    "s3",
    region_name = AWS_REGION,
    aws_access_key_id     = os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def _key(name: str) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    return f"output/{today}/{name}"

def upload_file(local_path: str, key: str | None = None) -> str:
    key = key or _key(Path(local_path).name)
    try:
        #https://471112523412-3enkdsfj.ap-northeast-2.console.aws.amazon.com/s3/home?region=ap-northeast-2#
        s3.upload_file(local_path, BUCKET_NAME, key)
        url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
        logger.info(f"Uploaded {local_path} → {url}")
        return url
    except ClientError as e:
        logger.error(e)
        raise

def upload_json(data: dict, base_name: str) -> str:
    key = _key(f"{base_name}.json")
    body = json.dumps(data, ensure_ascii=False).encode()
    s3.put_object(
        Body=body, 
        Bucket=BUCKET_NAME, 
        Key=key,
        ContentType="application/json; charset=utf-8"
    )
    url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"
    logger.info(f"Uploaded JSON → {url}")
    return url

