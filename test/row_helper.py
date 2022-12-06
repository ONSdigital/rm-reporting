class Row(object):
    """
    This is going represent a row returned from SqlAlchemy.  It's not a true representation, but creating a LegacyRow
    in a matching format is incredibly difficult.  We'll just set the attributes that we need against it, and then it
    becomes a close enough approximation.

    This object can be instantiated with any arbitrary attributes for easy setup.  For example:
    row = Row(first_name="John")

    # Both of these are equivalent and will return "John"
    getattr(row, "first_name")
    row.first_name
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
