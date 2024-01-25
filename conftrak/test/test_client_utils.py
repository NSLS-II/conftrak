import pytest
import uuid

from conftrak.client.utils import doc_or_uid_to_uid


def test_docuid_uid():
    uid = str(uuid.uuid4())
    doc = dict(uid=uid)
    assert uid == doc_or_uid_to_uid(uid)
    assert uid == doc_or_uid_to_uid(doc)

