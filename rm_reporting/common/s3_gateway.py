import json
import logging

import boto3
from structlog import wrap_logger

from rm_reporting.common.validators import UUIDEncoder

logger = wrap_logger(logging.getLogger(__name__))


class SimpleStorageServiceGateway:
    def __init__(self, config):
        self.bucket = config["S3_BUCKET"]
        self.access = config["S3_ACCESS_KEY"]
        self.secret = config["S3_SECRET_KEY"]
        self.s3 = boto3.client("s3", aws_access_key_id=self.access, aws_secret_access_key=self.secret)

    def _upload_json_file_to_aws(self, file_name, file):
        file_path = f"sdc-contacts/{file_name}"
        logger.info("uploading file to aws", file_name=file_path)
        self.s3.put_object(
            Body=json.dumps(file, cls=UUIDEncoder), Bucket=self.bucket, Key=file_path, ContentType="application/json"
        )
        logger.info("file successfully uploaded to AWS", file_name=file_path)

    def upload_spp_file(self, file_name, file):
        self._upload_json_file_to_aws(file_name, file)
