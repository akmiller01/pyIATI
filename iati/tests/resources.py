"""A module to prove a way of locating and loading test resource files.

This is akin to the `iati.resources` module, but deals with test data.

"""
import os
import iati.resources


PATH_TEST_DATA = os.path.join(iati.resources.BASE_PATH, 'test_data')
"""The relative location of the folder containing IATI data files."""


def get_test_data_path(name, version=None):
    """Determine the path of an IATI data file with the given filename at the specified version of the Standard.

    Args:
        name (str): The name of the data file to locate. The name may contain forward slashes (`/`) to indicate a directory. Data files must be `.xml` files.
        version (str): The version of the Standard to return the data files for. Defaults to None. This means that the path is returned for a filename at the latest version of the Standard.

    Returns:
        str: The path to a file containing the specified data.

    Note:
        Does not check whether the specified data file actually exists.

    Warning:
        This is a function used for testing purposes and should be located in a different module. DO NOT reply on it remaining here.

        Needs to handle a more complex file structure than a single flat directory.

    Todo:
        Test this directly rather than just the indirect tests that exist at present.

    """
    # ensure the folders are in a OS-independent format
    if '/' in name:
        split_name = name.split('/')
        name = os.sep.join(split_name)

    # remove the '.xml' file extension if present
    if name[-4:] == iati.resources.FILE_DATA_EXTENSION:
        name = name[:-4]

    return os.path.join(PATH_TEST_DATA, iati.resources.get_folder_name_for_version(version), '{0}'.format(name) + iati.resources.FILE_DATA_EXTENSION)


def get_test_data_paths_in_folder(folder_name, version=None):
    """Determine the paths of all IATI data files in the specified folder under the root test folder.

    Args:
        name (str): The name of the folder within which to locate data files.
        version (str): The version of the Standard to return the data files for. Defaults to None. This means that the path is returned for a filename at the latest version of the Standard.

    Returns:
        list of str: The paths to data files in the specified folders.

    """
    # ensure the folders are in a OS-independent format
    if '/' in folder_name:
        split_name = folder_name.split('/')
        folder_name = os.sep.join(split_name)

    paths = list()
    root_folder = os.path.join(PATH_TEST_DATA, iati.resources.get_folder_name_for_version(version), folder_name)
    resource_folder = iati.resources.resource_filename(root_folder)

    for base_folder, _, file_names in os.walk(resource_folder):
        desired_files = [file_name for file_name in file_names if file_name[-4:] == iati.resources.FILE_DATA_EXTENSION]
        for file_name in desired_files:
            paths.append(os.path.join(base_folder, file_name))

    # de-resource the file-names so that they're not duplicated
    deresourced_paths = [path[path.find(root_folder):] for path in paths]

    return deresourced_paths


def get_test_ruleset_path(name, version=None):
    """Determine the path of an IATI test Ruleset file with the given filename at the specified version of the Standard.

    Args:
        name (str): The name of the data file to locate. The filename must not contain the '.xml' file extension.
        version (str): The version of the Standard to return the data files for. Defaults to None. This means that the path is returned for a filename at the latest version of the Standard.

    Returns:
        str: The path to a file containing the specified test Ruleset.

    Note:
        Does not check whether the specified file actually exists.

    Warning:
        This is a function used for testing purposes and should be located in a different module. DO NOT reply on it remaining here.

        Needs to handle a more complex file structure than a single flat directory.

    Todo:
        Might need removing. What is using it now?

    """
    return os.path.join(PATH_TEST_DATA, iati.resources.get_folder_name_for_version(version), 'rulesets/{0}'.format(name) + iati.resources.FILE_RULESET_EXTENSION)


def load_as_dataset(file_path, version=None):
    """Load a specified test data file as a Dataset.

    Args:
        file_path (str): The path of the file, relative to the root test data folder. Folders should be separated by a forward-slash (`/`).
        version (str): The version of the Standard to return the data files for. Defaults to None. This means that the path is returned for a filename at the latest version of the Standard.

    Returns:
        dataset: A Dataset containing the contents of the file at the specified location.

    Raises:
        iati.exceptions.ValidationError: If the provided XML does not conform to the IATI standard.

    """
    return iati.resources.load_as_dataset(iati.tests.resources.get_test_data_path(file_path, version))


def load_as_string(file_path, version=None):
    """Load a specified test data file as a string.

    Args:
        file_path (str): The path of the file, relative to the root test data folder. Folders should be separated by a forward-slash (`/`).
        version (str): The version of the Standard to return the data files for. Defaults to None. This means that the path is returned for a filename at the latest version of the Standard.

    Returns:
        str (python3) / unicode (python2): The contents of the file at the specified location.

    """
    return iati.resources.load_as_string(iati.tests.resources.get_test_data_path(file_path, version))
