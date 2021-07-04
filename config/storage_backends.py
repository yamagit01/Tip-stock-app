import json
import os

from django.conf import settings
from django.contrib.staticfiles.storage import (FileSystemStorage,
                                                ManifestFilesMixin,
                                                StaticFilesStorage)
from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage


class LocalManifestFilesMixin(ManifestFilesMixin):
    
    manifest_location = os.path.abspath(settings.BASE_DIR)  # or settings.PROJECT_ROOT depending on how you've set it up in your settings file.
    manifest_storage = FileSystemStorage(location=manifest_location)

    def read_manifest(self):
        try:
            with self.manifest_storage.open(self.manifest_name) as manifest:
                return manifest.read().decode()
        except FileNotFoundError:
            return None

    def save_manifest(self):
        payload = {'paths': self.hashed_files, 'version': self.manifest_version}
        if self.manifest_storage.exists(self.manifest_name):
            self.manifest_storage.delete(self.manifest_name)
        contents = json.dumps(payload).encode()
        self.manifest_storage._save(self.manifest_name, ContentFile(contents))


class PublicStaticStorage(LocalManifestFilesMixin, S3Boto3Storage):
    location = 'static'
    default_acl = 'public-read'

    def __init__(self, *args, **kwargs):
        kwargs['custom_domain'] = settings.AWS_CLOUDFRONT_DOMAIN
        super().__init__(*args, **kwargs)


class PublicMediaStorage(S3Boto3Storage):
    location = 'media'
    default_acl = 'public-read'
    file_overwrite = False
    
    def __init__(self, *args, **kwargs):
        kwargs['custom_domain'] = settings.AWS_CLOUDFRONT_DOMAIN
        super().__init__(*args, **kwargs)


class CollectStaticStorage(LocalManifestFilesMixin, StaticFilesStorage):
    pass
