import uuid


def is_valid_uuid(uuid_string):

    if len(uuid_string) > 36:
        return False

    try:
        # Check if data is in valid UUID format
        str(uuid.UUID(uuid_string))
    except ValueError:
        return False
    else:
        return True
