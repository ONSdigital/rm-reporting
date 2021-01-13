import json
import logging

from google.cloud import storage
from structlog import wrap_logger

from rm_reporting.common.validators import UUIDEncoder

logger = wrap_logger(logging.getLogger(__name__))


class GoogleCloudStorageGateway:

    def __init__(self, config):
        self.project_id = config['GOOGLE_CLOUD_PROJECT']
        self.bucket_name = config['GCS_BUCKET_NAME']
        self.client = storage.Client(project=self.project_id)
        self.bucket = self.client.get_bucket(self.bucket_name)

    def _upload_json_file_to_gcs(self, file_name, file):
        logger.info('uploading file to GCS', file_name=file_name)
        blob = self.bucket.blob(file_name)
        blob.upload_from_string(
            data=json.dumps(file, cls=UUIDEncoder),
            content_type='application/json'
        )
        logger.info('file successfully uploaded to GCS', file_name=file_name)

    def upload_spp_file_to_gcs(self, file_name, file):
        self._upload_json_file_to_gcs(file_name, file)