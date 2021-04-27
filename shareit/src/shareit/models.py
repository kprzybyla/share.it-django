__all__ = ["encode_secret", "Resource", "URL_MAXIMUM_LENGTH"]

import uuid
import base64
import hashlib
import binascii
import datetime

from typing import Any, Optional, Final

from django.db import models
from django.utils import timezone
from django.shortcuts import reverse

SHA_256_LENGTH: Final[int] = 256
HEX_BITS_PER_CHAR: Final[int] = 4

URL_MAXIMUM_LENGTH: Final[int] = 50
SECRET_HASH_MAXIMUM_LENGTH: Final[int] = SHA_256_LENGTH // HEX_BITS_PER_CHAR

ACCESSED_INIT_VALUE: Final[int] = 0
EXPIRATION_DATE_DELTA: Final[datetime.timedelta] = datetime.timedelta(hours=24)


def encode_secret(secret: str) -> str:
    """
    Encodes secret with SHA-256 algorithm.

    :param secret: secret to be encoded
    """

    return hashlib.sha256(secret.encode()).hexdigest()


def expiration_date(*, now: Optional[datetime.datetime] = None) -> datetime.datetime:
    """
    Generates expiration date starting from `now`.
    If `now` is not provided, uses current date.

    :param now: expiration date starting point
    """

    now = now or timezone.now()

    return now + EXPIRATION_DATE_DELTA


class Resource(models.Model):

    """
    Model for the resource object.

    - Uid contains the UUID
    - Url contains the protected url
    - Secret hash contains the SHA-256 hash of secret for the resource
    - Expiration date contains the date on which the resource will expire
    """

    uid = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4)
    url = models.CharField(max_length=URL_MAXIMUM_LENGTH)
    secret_hash = models.CharField(max_length=SECRET_HASH_MAXIMUM_LENGTH)
    expiration_date = models.DateTimeField(default=expiration_date)
    accessed = models.PositiveIntegerField(default=ACCESSED_INIT_VALUE)

    objects: Any
    DoesNotExist: Any

    def __str__(self) -> str:
        return f"Resource object ({self.uri!r})"

    @classmethod
    def create(cls, url: str, secret: str) -> "Resource":
        """
        Creates resource with encrypted secret.

        :param url: resource url
        :param secret: resource plaintext secret
        """

        resource = cls(url=url, secret_hash=encode_secret(secret))

        return resource

    @staticmethod
    def encode_uid(uuid_object: uuid.UUID) -> str:
        """
        Encodes UUID object to the string.

        :param uuid_object: decoded UUID
        """

        uid = base64.urlsafe_b64encode(uuid_object.bytes).decode()

        return uid

    @staticmethod
    def decode_uid(uid: str) -> Optional[uuid.UUID]:
        """
        Decodes string to the UUID object.

        :param uid: encoded UUID
        """

        try:
            uid_bytes = base64.urlsafe_b64decode(uid)
        except binascii.Error:
            return None

        try:
            uuid_object = uuid.UUID(bytes=uid_bytes)
        except ValueError:
            return None

        return uuid_object

    @property
    def uri(self) -> str:
        """
        Returns encoded UUID.
        """

        # noinspection PyTypeChecker
        return self.encode_uid(self.uid)

    def verify_secret(self, secret: str) -> bool:
        """
        Method for verifing the resource secret.

        :param secret: resource plaintext secret
        """

        secret_hash = encode_secret(secret)

        return secret_hash == self.secret_hash

    def get_absolute_url(self) -> str:
        """
        Absolute URL for accessing resource.
        """

        return reverse("access", args=[self.uri])
