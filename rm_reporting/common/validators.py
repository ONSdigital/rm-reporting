import json
import uuid


def parse_uuid(uuid_string):

    try:
        # Check if data is in valid UUID format
        return str(uuid.UUID(uuid_string))
    except ValueError:
        return False


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)