"""A module containing a core representation of IATI Schemas."""
from lxml import etree
import iati.core.codelists
import iati.core.constants
import iati.core.exceptions
import iati.core.resources
import iati.core.utilities


class Schema(object):
    """Represenation of a Schema as defined within the IATI SSOT.

    Attributes:
        codelists (set): The Codelists asspciated with this Schema. This is a read-only attribute.
        root_element_name (str): The name of the root element within the schema - i.e. 'iati-activities' for the activity schema and 'iati-organisations' for the organisation schema.

    Warning:
        The private attribute allowing access to the base Schema Tree is likely to change in determining a good way of accessing the contained schema content.

    Todo:
        Determine a good API for accessing the XMLSchema that the iati.core.Schema represents.

        Determine how to distinguish and handle the different types of Schema - activity, organisation, codelist, other.

    """

    root_element_name = ''

    def __init__(self, path):
        """Initialise a Schema.

        Args:
            path (str): The path to the schema that is being initialised.

        Raises:
            iati.core.exceptions.SchemaError: An error occurred during the creation of the Schema.

        Warning:
            The format of the constructor is likely to change. It needs to be less reliant on the name acting as a UID, and allow for other attributes to be provided at this point.

            The raised exceptions are likely to change upon review of IATI-specific exceptions.

            Need to define a good API for accessing public and private attributes. Requiring something along the lines of `schema.schema` is likely not ideal. An improved understanding of use cases will be required for this.

        Todo:
            Allow for generation of schemas outside the IATI SSOT.

            Better use the try-except pattern.

            Allow the base schema to be modified after initialisation.

            Create test instance where the SchemaError is raised.

        """
        self._schema_base_tree = None
        self.codelists = set()

        try:
            loaded_tree = iati.core.resources.load_as_tree(path)
        except (IOError, OSError):
            msg = "Failed to load tree at '{0}' when creating Schema.".format(path)
            iati.core.utilities.log_error(msg)
            raise iati.core.exceptions.SchemaError
        else:
            self._schema_base_tree = loaded_tree
            self._flatten_includes()

    def _change_include_to_xinclude(self, tree):
        """Change the method in which common elements are included.

        lxml does not contain functionality to access elements within imports defined along the lines of: `<xsd:include schemaLocation="NAME.xsd" />`
        It does, however, contains functionality to access elements within imports defined along the lines of: `<xi:include href="NAME.xsd" parse="xml" />`
        when there is a namespace defined against the root schema element as `xmlns:xi="http://www.w3.org/2001/XInclude"`

        This changes instances of the former to the latter.

        Params:
            tree (etree._ElementTree): The tree within which xsd:include is to be changed to xi:include.

        Returns:
            etree._ElementTree: The modified tree.

        Todo:
            Make resource locations more able to handle the general case.

            Consider moving this out of Schema().

            Tidy this up.

            Consider using XSLT.

        """
        # identify the old info
        include_xpath = (iati.core.constants.NAMESPACE + 'include')
        include_el = tree.getroot().find(include_xpath)
        if include_el is None:
            return
        include_location = include_el.attrib['schemaLocation']

        # add namespace for XInclude
        xi_name = 'xi'
        xi_uri = 'http://www.w3.org/2001/XInclude'
        iati.core.utilities.add_namespace(tree, xi_name, xi_uri)
        new_nsmap = {}
        for key, value in iati.core.constants.NSMAP.items():
            new_nsmap[key] = value
        new_nsmap[xi_name] = xi_uri

        # create a new element
        xinclude_el = etree.Element(
            '{' + xi_uri + '}include',
            href=iati.core.resources.resource_filename(iati.core.resources.get_schema_path(include_location[:-4])),
            parse='xml',
            nsmap=new_nsmap
        )

        # make the path to `xml.xsd` reference the correct file
        import_xpath = (iati.core.constants.NAMESPACE + 'import')
        import_el = tree.getroot().find(import_xpath)
        import_el.attrib['schemaLocation'] = iati.core.resources.resource_filename(iati.core.resources.get_schema_path('xml'))

        # insert the new element
        tree.getroot().insert(import_el.getparent().index(import_el) + 1, xinclude_el)

        # remove the old element
        etree.strip_elements(tree.getroot(), include_xpath)

        return tree

    def _flatten_includes(self):
        """For a Schema that contains an xsd:include element, flatten includes so that all nodes are accessible through lxml.

        I.e. Identify the contents of files defined as `<xsd:include schemaLocation="NAME.xsd" />` and bring in the contents.

        Updates:
            self._schema_base_tree: To be the flattened schema. Makes no modification if the schema contains no xsd:include element.

        Todo:
            Consider moving this out of Schema().

            Tidy this up.

        """
        # Ensure that the include element is in a format that can be read by lxml
        tree = self._change_include_to_xinclude(self._schema_base_tree)

        # Adopt the included elements
        if tree is None:
            return
        else:
            tree.xinclude()

        # Find any nested `xsd:schema` elements that exist within the newly flattened schema
        schema_xpath = (iati.core.constants.NAMESPACE + 'schema')
        for nested_schema_el in tree.getroot().findall(schema_xpath):
            if isinstance(nested_schema_el, etree._Element):
                # Move contents of nested schema elements up a level
                for elem in nested_schema_el[:]:
                    # Do not duplicate an import statement
                    if 'schemaLocation' in elem.attrib:
                        continue
                    tree.getroot().insert(nested_schema_el.getparent().index(nested_schema_el) + 1, elem)
        # Remove the nested `xsd:schema` elements
        etree.strip_elements(tree.getroot(), schema_xpath)

    def get_xsd_element(self, xsd_element_name):
        """Return an lxml.etree represention for a given xsd:element, based on its name.

        Args:
            xsd_element_name (str): The name of the element to be returned.

        Returns:
            etree._ElementTree / None: The first element tree that matches the element name within the schema. Returns None if no XSD element found.

        """
        return self._schema_base_tree.find(
            '//xsd:element[@name="{0}"]'.format(xsd_element_name),
            namespaces=iati.core.constants.NSMAP
        )

    def get_child_xsd_elements(self, parent_element):
        """Return a list of child elements for a given lxml.etree represention of an xsd:element.

        Args:
            parent_element (etree._ElementTree): The parent represention of an XSD element to find children for.

        Returns:
            list of etree._ElementTree: A list containing representions of XSD elements that are children to the input element.  If there are no child elements, this will be an empty list.
        """
        child_elements_and_refs = parent_element.findall(
            'xsd:complexType/xsd:sequence/xsd:element',
            namespaces=iati.core.constants.NSMAP
        )  # This will find all elements defined directly within the schema, or cited by reference.

        # Look for corresponding complexType and add to the child_elements_and_refs
        if parent_element.get('type') is not None:
            complexType_children = self._schema_base_tree.findall(
                'xsd:complexType[@name="{0}"]/xsd:sequence/xsd:element'.format(parent_element.get('type')),
                namespaces=iati.core.constants.NSMAP
            )
            child_elements_and_refs = child_elements_and_refs + complexType_children

        output = []
        for element_or_ref in child_elements_and_refs:
            if element_or_ref.get('ref') is not None:
                # This element is defined via a reference to an xsd:element defined elsewhere in the schema.
                output.append(self.get_xsd_element(element_or_ref.get('ref')))
            elif element_or_ref.get('name') is not None:
                # This element is defined directly within the parent xsd:element.
                output.append(element_or_ref)

        return output

    def get_attributes_in_xsd_element(self, element):
        """Return a list of attribute elements that are contained within a given lxml.etree represention of an xsd:element.

        Args:
            element (etree._ElementTree): The lxml represention of an XSD element to find attributes for.

        Returns:
            list of etree._ElementTree: A list containing representions of XSD attributes that are contained witin the input element. If there are no attributes, this will be an empty list.
        """
        return element.findall(
            'xsd:complexType/xsd:attribute',
            namespaces=iati.core.constants.NSMAP
        )

    def is_attribute_xml_lang(self, element):
        """Perform a check on a lxml represention of an xsd:attribute to determine if it is an 'xml:lang' attribute.

        Args:
            element (etree._ElementTree): The lxml represention of the xsd:attribute to check.

        Returns:
            bool: True if the element is an 'xml:lang' attribute, or False if not.
        """
        if element.get('ref') == 'xml:lang':
            return True
        else:
            return False

    def get_xsd_element_or_attribute_name(self, element):
        """Returns the name of a given xsd:element or xsd:attribute element, as defined in the element's @name attribute.

        Args:
            element (etree._ElementTree): The represention of an xsd:element or xsd:attribute element to find the name for.

        Returns:
            str or None: The value within the xsd:element/@name or xsd:attribute/@name. None is returned if no name is found.
        """
        name = element.get('name')

        # Deal with the special case of the 'xml:lang' attributes, which are formally defined in the xml.xsd schema, but the documentation and usage restrictions are set in the IATI schemas.
        if self.is_attribute_xml_lang(element):
            name = 'xml:lang'

        return name


class ActivitySchema(Schema):
    """Represenation of an IATI Activity Schema as defined within the IATI SSOT."""

    root_element_name = 'iati-activities'


class OrganisationSchema(Schema):
    """Represenation of an IATI Organisation Schema as defined within the IATI SSOT."""

    root_element_name = 'iati-organisations'
