import uuid


def is_valid_uuid(uuid_string):
    try:
        # Check if data is in valid UUID format
        str(uuid.UUID(uuid_string))
        return True
    except ValueError:
        return False
