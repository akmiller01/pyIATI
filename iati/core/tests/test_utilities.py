"""A module containing tests for the library implementation of accessing utilities."""
from lxml import etree
import iati.core.resources
import iati.core.utilities


class TestUtilities(object):
    """A container for tests relating to utilities"""

    def test_convert_to_schema(self):
        """Check that an etree can be converted to a schema."""
        path = iati.core.resources.path_schema('iati-activities-schema')

        tree = iati.core.resources.load_as_tree(path)
        if not tree:
            assert False
        schema = iati.core.utilities.convert_to_schema(tree)

        assert isinstance(schema, etree.XMLSchema)
