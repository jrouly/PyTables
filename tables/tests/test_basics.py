import sys
import unittest
import os
import tempfile
import warnings

import numpy

from tables import *
from tables.flavor import all_flavors, array_of_flavor
from tables.tests import common
from tables.tests.common import cleanup
from tables.tests.common import verbose

# To delete the internal attributes automagically
unittest.TestCase.tearDown = cleanup


class OpenFileTestCase(common.PyTablesTestCase):

    def setUp(self):
        # Create an HDF5 file
        self.file = tempfile.mktemp(".h5")
        fileh = openFile(self.file, mode = "w", title="File title")
        root = fileh.root
        # Create an array
        fileh.createArray(root, 'array', [1,2],
                          title = "Array example")
        table = fileh.createTable(root, 'table', {'var1':Col.from_kind('int')},
                                   "Table example")
        # Create another array object
        array = fileh.createArray(root, 'anarray',
                                  [1], "Array title")
        table = fileh.createTable(root, 'atable', {'var1':Col.from_kind('int')},
                                   "Table title")
        # Create a group object
        group = fileh.createGroup(root, 'agroup',
                                  "Group title")
        group._v_attrs.testattr = 42
        # Create a some objects there
        array1 = fileh.createArray(group, 'anarray1',
                                   [1,2,3,4,5,6,7], "Array title 1")
        array1.attrs.testattr = 42
        array2 = fileh.createArray(group, 'anarray2',
                                   [2], "Array title 2")
        table1 = fileh.createTable(group, 'atable1', {'var1':Col.from_kind('int')},
                                   "Table title 1")
        ra = numpy.rec.array([(1,11,'a')],formats='u1,f4,a1')
        table2 = fileh.createTable(group, 'atable2', ra,
                                   "Table title 2")
        # Create a lonely group in first level
        group2 = fileh.createGroup(root, 'agroup2',
                                  "Group title 2")
        # Create a new group in the second level
        group3 = fileh.createGroup(group, 'agroup3',
                                   "Group title 3")

        # Create an array in the root with the same name as one in 'agroup'
        fileh.createArray(root, 'anarray1', [1,2],
                          title = "Array example")

        fileh.close()

    def tearDown(self):
        # Remove the temporary file
        os.remove(self.file)
        cleanup(self)

    def test00_newFile(self):
        """Checking creation of a new file"""

        # Create an HDF5 file
        file = tempfile.mktemp(".h5")
        fileh = openFile(file, mode = "w")
        arr = fileh.createArray(fileh.root, 'array', [1,2],
                                title = "Array example")
        # Get the CLASS attribute of the arr object
        class_ = fileh.root.array.attrs.CLASS

        # Close and delete the file
        fileh.close()
        os.remove(file)

        assert class_.capitalize() == "Array"

    def test01_openFile(self):
        """Checking opening of an existing file"""

        # Open the old HDF5 file
        fileh = openFile(self.file, mode = "r")
        # Get the CLASS attribute of the arr object
        title = fileh.root.array.getAttr("TITLE")

        assert title == "Array example"
        fileh.close()

    def test01b_trMap(self):
        """Checking the translation table capability for reading"""

        # Open the old HDF5 file
        trMap = {"pythonarray": "array"}
        fileh = openFile(self.file, mode = "r", trMap=trMap)
        # Get the array objects in the file
        array_ = fileh.getNode("/pythonarray")

        assert array_.name == "pythonarray"
        assert array_._v_hdf5name == "array"

        # This should throw an LookupError exception
        try:
            # Try to get the 'array' object in the old existing file
            array_ = fileh.getNode("/array")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")

        fileh.close()

    def test01c_trMap(self):
        """Checking the translation table capability for writing"""

        # Create an HDF5 file
        file = tempfile.mktemp(".h5")
        trMap = {"pythonarray": "array"}
        fileh = openFile(file, mode = "w", trMap=trMap)
        arr = fileh.createArray(fileh.root, 'pythonarray', [1,2],
                                title = "Title example")

        # Get the array objects in the file
        array_ = fileh.getNode("/pythonarray")
        assert array_.name == "pythonarray"
        assert array_._v_hdf5name == "array"

        fileh.close()

        # Open the old HDF5 file (without the trMap parameter)
        fileh = openFile(self.file, mode = "r")
        # Get the array objects in the file
        array_ = fileh.getNode("/array")

        assert array_.name == "array"
        assert array_._v_hdf5name == "array"

        # This should throw an LookupError exception
        try:
            # Try to get the 'pythonarray' object in the old existing file
            array_ = fileh.getNode("/pythonarray")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")

        fileh.close()
        # Remove the temporary file
        os.remove(file)


    def test02_appendFile(self):
        """Checking appending objects to an existing file"""

        # Append a new array to the existing file
        fileh = openFile(self.file, mode = "r+")
        fileh.createArray(fileh.root, 'array2', [3,4],
                          title = "Title example 2")
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Get the CLASS attribute of the arr object
        title = fileh.root.array2.getAttr("TITLE")

        assert title == "Title example 2"
        fileh.close()

    def test02b_appendFile2(self):
        """Checking appending objects to an existing file ("a" version)"""

        # Append a new array to the existing file
        fileh = openFile(self.file, mode = "a")
        fileh.createArray(fileh.root, 'array2', [3,4],
                          title = "Title example 2")
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Get the CLASS attribute of the arr object
        title = fileh.root.array2.getAttr("TITLE")

        assert title == "Title example 2"
        fileh.close()

    # Begin to raise errors...

    def test03_appendErrorFile(self):
        """Checking appending objects to an existing file in "w" mode"""

        # Append a new array to the existing file but in write mode
        # so, the existing file should be deleted!
        fileh = openFile(self.file, mode = "w")
        fileh.createArray(fileh.root, 'array2', [3,4],
                          title = "Title example 2")
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")

        try:
            # Try to get the 'array' object in the old existing file
            arr = fileh.root.array
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test04a_openErrorFile(self):
        """Checking opening a non-existing file for reading"""

        try:
            fileh = openFile("nonexistent.h5", mode = "r")
        except IOError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next IOError was catched!"
                print value
        else:
            self.fail("expected an IOError")

    def test04b_alternateRootFile(self):
        """Checking alternate root access to the object tree"""

        # Open the existent HDF5 file
        fileh = openFile(self.file, mode = "r", rootUEP="/agroup")
        # Get the CLASS attribute of the arr object
        if verbose:
            print "\nFile tree dump:", fileh
        title = fileh.root.anarray1.getAttr("TITLE")

        assert title == "Array title 1"
        fileh.close()

    # This test works well, but HDF5 emits a series of messages that
    # may loose the user. It is better to deactivate it.
    def notest04c_alternateRootFile(self):
        """Checking non-existent alternate root access to the object tree"""

        try:
            fileh = openFile(self.file, mode = "r", rootUEP="/nonexistent")
        except RuntimeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next RuntimeError was catched!"
                print value
        else:
            self.fail("expected an IOError")

    def test05a_removeGroupRecursively(self):
        """Checking removing a group recursively"""

        # Delete a group with leafs
        fileh = openFile(self.file, mode = "r+")

        try:
            fileh.removeNode(fileh.root.agroup)
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected a NodeError")

        # This should work now
        fileh.removeNode(fileh.root, 'agroup', recursive=1)

        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Try to get the removed object
        try:
            object = fileh.root.agroup
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        # Try to get a child of the removed object
        try:
            object = fileh.getNode("/agroup/agroup3")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test05b_removeGroupRecursively(self):
        """Checking removing a group recursively and access to it immediately"""

        if verbose:
            print '\n', '-=' * 30
            print "Running %s.test05b_removeGroupRecursively..." % self.__class__.__name__

        # Delete a group with leafs
        fileh = openFile(self.file, mode = "r+")

        try:
            fileh.removeNode(fileh.root, 'agroup')
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected a NodeError")

        # This should work now
        fileh.removeNode(fileh.root, 'agroup', recursive=1)

        # Try to get the removed object
        try:
            object = fileh.root.agroup
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        # Try to get a child of the removed object
        try:
            object = fileh.getNode("/agroup/agroup3")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test06_removeNodeWithDel(self):
        """Checking removing a node using ``__delattr__()``"""

        fileh = openFile(self.file, mode = "r+")

        try:
            # This should fail because there is no *Python attribute*
            # called ``agroup``.
            del fileh.root.agroup
        except AttributeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next AttributeError was catched!"
                print value
        else:
            self.fail("expected an AttributeError")

        fileh.close()

    def test06a_removeGroup(self):
        """Checking removing a lonely group from an existing file"""

        fileh = openFile(self.file, mode = "r+")
        fileh.removeNode(fileh.root, 'agroup2')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Try to get the removed object
        try:
            object = fileh.root.agroup2
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test06b_removeLeaf(self):
        """Checking removing Leaves from an existing file"""

        fileh = openFile(self.file, mode = "r+")
        fileh.removeNode(fileh.root, 'anarray')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Try to get the removed object
        try:
            object = fileh.root.anarray
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test06c_removeLeaf(self):
        """Checking removing Leaves and access it immediately"""

        fileh = openFile(self.file, mode = "r+")
        fileh.removeNode(fileh.root, 'anarray')

        # Try to get the removed object
        try:
            object = fileh.root.anarray
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test06d_removeLeaf(self):
        """Checking removing a non-existent node"""

        fileh = openFile(self.file, mode = "r+")

        # Try to get the removed object
        try:
            fileh.removeNode(fileh.root, 'nonexistent')
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test06e_removeTable(self):
        """Checking removing Tables from an existing file"""

        fileh = openFile(self.file, mode = "r+")
        fileh.removeNode(fileh.root, 'atable')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Try to get the removed object
        try:
            object = fileh.root.atable
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test07_renameLeaf(self):
        """Checking renaming a leave and access it after a close/open"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.anarray, 'anarray2')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Ensure that the new name exists
        array_ = fileh.root.anarray2
        assert array_.name == "anarray2"
        assert array_._v_pathname == "/anarray2"
        assert array_._v_depth == 1
        # Try to get the previous object with the old name
        try:
            object = fileh.root.anarray
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test07b_renameLeaf(self):
        """Checking renaming Leaves and accesing them immediately"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.anarray, 'anarray2')

        # Ensure that the new name exists
        array_ = fileh.root.anarray2
        assert array_.name == "anarray2"
        assert array_._v_pathname == "/anarray2"
        assert array_._v_depth == 1
        # Try to get the previous object with the old name
        try:
            object = fileh.root.anarray
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test07c_renameLeaf(self):
        """Checking renaming Leaves and modify attributes after that"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.anarray, 'anarray2')
        fileh.root.anarray2.attrs.TITLE = "hello"
        # Ensure that the new attribute has been written correctly
        array_ = fileh.root.anarray2
        assert array_.title == "hello"
        assert array_.attrs.TITLE == "hello"
        fileh.close()

    def test07d_renameLeaf(self):
        """Checking renaming a Group under a nested group"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.agroup.anarray2, 'anarray3')

        # Ensure that we can access n attributes in the new group
        node = fileh.root.agroup.anarray3
        assert node._v_title == "Array title 2"
        fileh.close()

    def test08_renameToExistingLeaf(self):
        """Checking renaming a node to an existing name"""

        # Open this file
        fileh = openFile(self.file, mode = "r+")
        # Try to get the previous object with the old name
        try:
            fileh.renameNode(fileh.root.anarray, 'array')
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test08b_renameToNotValidNaturalName(self):
        """Checking renaming a node to a non-valid natural name"""

        # Open this file
        fileh = openFile(self.file, mode = "r+")
        warnings.filterwarnings("error", category=NaturalNameWarning)
        # Try to get the previous object with the old name
        try:
            fileh.renameNode(fileh.root.anarray, 'array 2')
        except NaturalNameWarning:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NaturalNameWarning was catched!"
                print value
        else:
            self.fail("expected an NaturalNameWarning")
        # Reset the warning
        warnings.filterwarnings("default", category=NaturalNameWarning)
        fileh.close()

    def test09_renameGroup(self):
        """Checking renaming a Group and access it after a close/open"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.agroup, 'agroup3')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Ensure that the new name exists
        group = fileh.root.agroup3
        assert group._v_name == "agroup3"
        assert group._v_pathname == "/agroup3"
        # The children of this group also must be accessible through the
        # new name path
        group2 = fileh.getNode("/agroup3/agroup3")
        assert group2._v_name == "agroup3"
        assert group2._v_pathname == "/agroup3/agroup3"
        # Try to get the previous object with the old name
        try:
            object = fileh.root.agroup
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        # Try to get a child with the old pathname
        try:
            object = fileh.getNode("/agroup/agroup3")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test09b_renameGroup(self):
        """Checking renaming a Group and access it immediately"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.agroup, 'agroup3')

        # Ensure that the new name exists
        group = fileh.root.agroup3
        assert group._v_name == "agroup3"
        assert group._v_pathname == "/agroup3"
        # The children of this group also must be accessible through the
        # new name path
        group2 = fileh.getNode("/agroup3/agroup3")
        assert group2._v_name == "agroup3"
        assert group2._v_pathname == "/agroup3/agroup3"
        # Try to get the previous object with the old name
        try:
            object = fileh.root.agroup
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        # Try to get a child with the old pathname
        try:
            object = fileh.getNode("/agroup/agroup3")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test09c_renameGroup(self):
        """Checking renaming a Group and modify attributes afterwards"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.agroup, 'agroup3')

        # Ensure that we can modify attributes in the new group
        group = fileh.root.agroup3
        group._v_attrs.TITLE = "Hello"
        assert group._v_title == "Hello"
        assert group._v_attrs.TITLE == "Hello"
        fileh.close()

    def test09d_renameGroup(self):
        """Checking renaming a Group under a nested group"""

        fileh = openFile(self.file, mode = "r+")
        fileh.renameNode(fileh.root.agroup.agroup3, 'agroup4')

        # Ensure that we can access n attributes in the new group
        group = fileh.root.agroup.agroup4
        assert group._v_title == "Group title 3"
        fileh.close()

    def test10_moveLeaf(self):
        """Checking moving a leave and access it after a close/open"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup("/", "newgroup")
        fileh.moveNode(fileh.root.anarray, newgroup, 'anarray2')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Ensure that the new name exists
        array_ = fileh.root.newgroup.anarray2
        assert array_.name == "anarray2"
        assert array_._v_pathname == "/newgroup/anarray2"
        assert array_._v_depth == 2
        # Try to get the previous object with the old name
        try:
            object = fileh.root.anarray
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test10b_moveLeaf(self):
        """Checking moving a leave and access it without a close/open"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup("/", "newgroup")
        fileh.moveNode(fileh.root.anarray, newgroup, 'anarray2')

        # Ensure that the new name exists
        array_ = fileh.root.newgroup.anarray2
        assert array_.name == "anarray2"
        assert array_._v_pathname == "/newgroup/anarray2"
        assert array_._v_depth == 2
        # Try to get the previous object with the old name
        try:
            object = fileh.root.anarray
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test10c_moveLeaf(self):
        """Checking moving Leaves and modify attributes after that"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup("/", "newgroup")
        fileh.moveNode(fileh.root.anarray, newgroup, 'anarray2')
        fileh.root.newgroup.anarray2.attrs.TITLE = "hello"
        # Ensure that the new attribute has been written correctly
        array_ = fileh.root.newgroup.anarray2
        assert array_.title == "hello"
        assert array_.attrs.TITLE == "hello"
        fileh.close()

    def test10d_moveToExistingLeaf(self):
        """Checking moving a leaf to an existing name"""

        # Open this file
        fileh = openFile(self.file, mode = "r+")
        # Try to get the previous object with the old name
        try:
            fileh.moveNode(fileh.root.anarray, fileh.root, 'array')
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test10_2_moveTable(self):
        """Checking moving a table and access it after a close/open"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup("/", "newgroup")
        fileh.moveNode(fileh.root.atable, newgroup, 'atable2')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Ensure that the new name exists
        table_ = fileh.root.newgroup.atable2
        assert table_.name == "atable2"
        assert table_._v_pathname == "/newgroup/atable2"
        assert table_._v_depth == 2
        # Try to get the previous object with the old name
        try:
            object = fileh.root.atable
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test10_2b_moveTable(self):
        """Checking moving a table and access it without a close/open"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup("/", "newgroup")
        fileh.moveNode(fileh.root.atable, newgroup, 'atable2')

        # Ensure that the new name exists
        table_ = fileh.root.newgroup.atable2
        assert table_.name == "atable2"
        assert table_._v_pathname == "/newgroup/atable2"
        assert table_._v_depth == 2
        # Try to get the previous object with the old name
        try:
            object = fileh.root.atable
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test10_2c_moveTable(self):
        """Checking moving tables and modify attributes after that"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup("/", "newgroup")
        fileh.moveNode(fileh.root.atable, newgroup, 'atable2')
        fileh.root.newgroup.atable2.attrs.TITLE = "hello"
        # Ensure that the new attribute has been written correctly
        table_ = fileh.root.newgroup.atable2
        assert table_.title == "hello"
        assert table_.attrs.TITLE == "hello"
        fileh.close()

    def test10_2d_moveToExistingTable(self):
        """Checking moving a table to an existing name"""

        # Open this file
        fileh = openFile(self.file, mode = "r+")
        # Try to get the previous object with the old name
        try:
            fileh.moveNode(fileh.root.atable, fileh.root, 'table')
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test10_2e_moveToExistingTableOverwrite(self):
        """Checking moving a table to an existing name, overwriting it"""

        fileh = openFile(self.file, mode = "r+")

        srcNode = fileh.root.atable
        fileh.moveNode(srcNode, fileh.root, 'table', overwrite = True)
        dstNode = fileh.root.table

        self.assert_(srcNode is dstNode)
        fileh.close()

    def test11_moveGroup(self):
        """Checking moving a Group and access it after a close/open"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup(fileh.root, 'newgroup')
        fileh.moveNode(fileh.root.agroup, newgroup, 'agroup3')
        fileh.close()

        # Open this file in read-only mode
        fileh = openFile(self.file, mode = "r")
        # Ensure that the new name exists
        group = fileh.root.newgroup.agroup3
        assert group._v_name == "agroup3"
        assert group._v_pathname == "/newgroup/agroup3"
        assert group._v_depth == 2
        # The children of this group must also be accessible through the
        # new name path
        group2 = fileh.getNode("/newgroup/agroup3/agroup3")
        assert group2._v_name == "agroup3"
        assert group2._v_pathname == "/newgroup/agroup3/agroup3"
        assert group2._v_depth == 3
        # Try to get the previous object with the old name
        try:
            object = fileh.root.agroup
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        # Try to get a child with the old pathname
        try:
            object = fileh.getNode("/agroup/agroup3")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test11b_moveGroup(self):
        """Checking moving a Group and access it immediately"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup(fileh.root, 'newgroup')
        fileh.moveNode(fileh.root.agroup, newgroup, 'agroup3')
        # Ensure that the new name exists
        group = fileh.root.newgroup.agroup3
        assert group._v_name == "agroup3"
        assert group._v_pathname == "/newgroup/agroup3"
        assert group._v_depth == 2
        # The children of this group must also be accessible through the
        # new name path
        group2 = fileh.getNode("/newgroup/agroup3/agroup3")
        assert group2._v_name == "agroup3"
        assert group2._v_pathname == "/newgroup/agroup3/agroup3"
        assert group2._v_depth == 3
        # Try to get the previous object with the old name
        try:
            object = fileh.root.agroup
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        # Try to get a child with the old pathname
        try:
            object = fileh.getNode("/agroup/agroup3")
        except LookupError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next LookupError was catched!"
                print value
        else:
            self.fail("expected an LookupError")
        fileh.close()

    def test11c_moveGroup(self):
        """Checking moving a Group and modify attributes afterwards"""

        fileh = openFile(self.file, mode = "r+")
        newgroup = fileh.createGroup(fileh.root, 'newgroup')
        fileh.moveNode(fileh.root.agroup, newgroup, 'agroup3')

        # Ensure that we can modify attributes in the new group
        group = fileh.root.newgroup.agroup3
        group._v_attrs.TITLE = "Hello"
        group._v_attrs.hola = "Hello"
        assert group._v_title == "Hello"
        assert group._v_attrs.TITLE == "Hello"
        assert group._v_attrs.hola == "Hello"
        fileh.close()

    def test11d_moveToExistingGroup(self):
        """Checking moving a group to an existing name"""

        # Open this file
        fileh = openFile(self.file, mode = "r+")
        # Try to get the previous object with the old name
        try:
            fileh.moveNode(fileh.root.agroup, fileh.root, 'agroup2')
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test11e_moveToExistingGroupOverwrite(self):
        """Checking moving a group to an existing name, overwriting it"""

        fileh = openFile(self.file, mode = "r+")

        # agroup2 -> agroup
        srcNode = fileh.root.agroup2
        fileh.moveNode(srcNode, fileh.root, 'agroup', overwrite = True)
        dstNode = fileh.root.agroup

        self.assert_(srcNode is dstNode)
        fileh.close()

    def test12a_moveNodeOverItself(self):
        """Checking moving a node over itself"""

        fileh = openFile(self.file, mode = "r+")

        # array -> array
        srcNode = fileh.root.array
        fileh.moveNode(srcNode, fileh.root, 'array')
        dstNode = fileh.root.array

        self.assert_(srcNode is dstNode)
        fileh.close()

    def test12b_moveGroupIntoItself(self):
        """Checking moving a group into itself"""

        # Open this file
        fileh = openFile(self.file, mode = "r+")
        try:
            # agroup2 -> agroup2/
            fileh.moveNode(fileh.root.agroup2, fileh.root.agroup2)
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test13a_copyLeaf(self):
        "Copying a leaf."

        fileh = openFile(self.file, mode = "r+")

        # array => agroup2/
        newNode = fileh.copyNode(fileh.root.array, fileh.root.agroup2)
        dstNode = fileh.root.agroup2.array

        self.assert_(newNode is dstNode)
        fileh.close()

    def test13b_copyGroup(self):
        "Copying a group."

        fileh = openFile(self.file, mode = "r+")

        # agroup2 => agroup/
        newNode = fileh.copyNode(fileh.root.agroup2, fileh.root.agroup)
        dstNode = fileh.root.agroup.agroup2

        self.assert_(newNode is dstNode)
        fileh.close()

    def test13c_copyGroupSelf(self):
        "Copying a group into itself."

        fileh = openFile(self.file, mode = "r+")

        # agroup2 => agroup2/
        newNode = fileh.copyNode(fileh.root.agroup2, fileh.root.agroup2)
        dstNode = fileh.root.agroup2.agroup2

        self.assert_(newNode is dstNode)
        fileh.close()

    def test13d_copyGroupRecursive(self):
        "Recursively copying a group."

        fileh = openFile(self.file, mode = "r+")

        # agroup => agroup2/
        newNode = fileh.copyNode(
            fileh.root.agroup, fileh.root.agroup2, recursive = True)
        dstNode = fileh.root.agroup2.agroup

        self.assert_(newNode is dstNode)
        dstChild1 = dstNode.anarray1
        dstChild2 = dstNode.anarray2
        dstChild3 = dstNode.agroup3
        fileh.close()

    def test14a_copyNodeExisting(self):
        "Copying over an existing node."

        fileh = openFile(self.file, mode = "r+")
        try:
            # agroup2 => agroup
            fileh.copyNode(fileh.root.agroup2, newname = 'agroup')
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test14b_copyNodeExistingOverwrite(self):
        "Copying over an existing node, overwriting it."

        fileh = openFile(self.file, mode = "r+")

        # agroup2 => agroup
        newNode = fileh.copyNode(fileh.root.agroup2, newname = 'agroup',
                                 overwrite = True)
        dstNode = fileh.root.agroup

        self.assert_(newNode is dstNode)
        fileh.close()

    def test14c_copyNodeExistingSelf(self):
        "Copying over self."

        fileh = openFile(self.file, mode = "r+")
        try:
            # agroup => agroup
            fileh.copyNode(fileh.root.agroup, newname = 'agroup')
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test14d_copyNodeExistingOverwriteSelf(self):
        "Copying over self, trying to overwrite."

        fileh = openFile(self.file, mode = "r+")
        try:
            # agroup => agroup
            fileh.copyNode(
                fileh.root.agroup, newname = 'agroup', overwrite = True)
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test14e_copyGroupSelfRecursive(self):
        "Recursively copying a group into itself."

        fileh = openFile(self.file, mode = "r+")
        try:
            # agroup => agroup/
            fileh.copyNode(
                fileh.root.agroup, fileh.root.agroup, recursive = True)
        except NodeError:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next NodeError was catched!"
                print value
        else:
            self.fail("expected an NodeError")
        fileh.close()

    def test15a_oneStepMove(self):
        "Moving and renaming a node in a single action."

        fileh = openFile(self.file, mode = "r+")

        # anarray1 -> agroup/array
        srcNode = fileh.root.anarray1
        fileh.moveNode(srcNode, fileh.root.agroup, 'array')
        dstNode = fileh.root.agroup.array

        self.assert_(srcNode is dstNode)
        fileh.close()

    def test15b_oneStepCopy(self):
        "Copying and renaming a node in a single action."

        fileh = openFile(self.file, mode = "r+")

        # anarray1 => agroup/array
        newNode = fileh.copyNode(
            fileh.root.anarray1, fileh.root.agroup, 'array')
        dstNode = fileh.root.agroup.array

        self.assert_(newNode is dstNode)
        fileh.close()

    def test16a_fullCopy(self):
        "Copying full data and user attributes."

        fileh = openFile(self.file, mode = "r+")

        # agroup => groupcopy
        srcNode = fileh.root.agroup
        newNode = fileh.copyNode(
            srcNode, newname = 'groupcopy', recursive = True)
        dstNode = fileh.root.groupcopy

        self.assert_(newNode is dstNode)
        self.assertEqual(srcNode._v_attrs.testattr, dstNode._v_attrs.testattr)
        self.assertEqual(
            srcNode.anarray1.attrs.testattr, dstNode.anarray1.attrs.testattr)
        self.assertEqual(srcNode.anarray1.read(), dstNode.anarray1.read())
        fileh.close()

    def test16b_partialCopy(self):
        "Copying partial data and no user attributes."

        fileh = openFile(self.file, mode = "r+")

        # agroup => groupcopy
        srcNode = fileh.root.agroup
        newNode = fileh.copyNode(
            srcNode, newname = 'groupcopy',
            recursive = True, copyuserattrs = False,
            start = 0, stop = 5, step = 2)
        dstNode = fileh.root.groupcopy

        self.assert_(newNode is dstNode)
        self.assert_(not hasattr(dstNode._v_attrs, 'testattr'))
        self.assert_(not hasattr(dstNode.anarray1.attrs, 'testattr'))
        self.assertEqual(srcNode.anarray1.read()[0:5:2], dstNode.anarray1.read())
        fileh.close()


class CheckFileTestCase(common.PyTablesTestCase):

    def test00_isHDF5File(self):
        """Checking isHDF5File function (TRUE case)"""

        # Create a PyTables file (and by so, an HDF5 file)
        file = tempfile.mktemp(".h5")
        fileh = openFile(file, mode = "w")
        arr = fileh.createArray(fileh.root, 'array', [1,2],
                                    title = "Title example")
        # For this method to run, it needs a closed file
        fileh.close()

        # When file has an HDF5 format, always returns 1
        if verbose:
            print "\nisHDF5File(%s) ==> %d" % (file, isHDF5File(file))
        assert isHDF5File(file) == 1

        # Then, delete the file
        os.remove(file)

    def test01_isHDF5File(self):
        """Checking isHDF5File function (FALSE case)"""

        # Create a regular (text) file
        file = tempfile.mktemp(".h5")
        fileh = open(file, "w")
        fileh.write("Hello!")
        fileh.close()

        version = isHDF5File(file)
        # When file is not an HDF5 format, always returns 0 or
        # negative value
        assert version <= 0

        # Then, delete the file
        os.remove(file)


    def test01x_isHDF5File_nonexistent(self):
        """Identifying a nonexistent HDF5 file."""
        self.assertRaises(IOError, isHDF5File, 'nonexistent')


    def test01x_isHDF5File_unreadable(self):
        """Identifying an unreadable HDF5 file."""

        if hasattr(os, 'getuid') and os.getuid() != 0:
            h5fname = tempfile.mktemp(suffix='.h5')
            openFile(h5fname, 'w').close()
            try:
                os.chmod(h5fname, 0)  # no permissions at all
                self.assertRaises(IOError, isHDF5File, h5fname)
            finally:
                os.remove(h5fname)


    def test02_isPyTablesFile(self):
        """Checking isPyTablesFile function (TRUE case)"""

        # Create a PyTables file
        file = tempfile.mktemp(".h5")
        fileh = openFile(file, mode = "w")
        arr = fileh.createArray(fileh.root, 'array', [1,2],
                                    title = "Title example")
        # For this method to run, it needs a closed file
        fileh.close()

        version = isPyTablesFile(file)
        # When file has a PyTables format, always returns "1.0" string or
        # greater
        if verbose:
            print
            print "\nPyTables format version number ==> %s" % \
              version
        assert version >= "1.0"

        # Then, delete the file
        os.remove(file)


    def test03_isPyTablesFile(self):
        """Checking isPyTablesFile function (FALSE case)"""

        # Create a regular (text) file
        file = tempfile.mktemp(".h5")
        fileh = open(file, "w")
        fileh.write("Hello!")
        fileh.close()

        version = isPyTablesFile(file)
        # When file is not a PyTables format, always returns 0 or
        # negative value
        assert version <= 0

        # Then, delete the file
        os.remove(file)

    def test04_openGenericHDF5File(self):
        """Checking opening of a generic HDF5 file"""

        warnings.filterwarnings("error", category=UserWarning)
        # Open an existing generic HDF5 file
        try:
            fileh = openFile(common.testFilename("ex-noattr.h5"), mode="r")
        except UserWarning:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next UserWarning was catched:"
                print value
            # Ignore the warning and actually open the file
            warnings.filterwarnings("ignore", category=UserWarning)
            fileh = openFile(common.testFilename("ex-noattr.h5"), mode="r")
        else:
            self.fail("expected an UserWarning")

        # Check for some objects inside

        # A group
        columns = fileh.getNode("/columns", classname="Group")
        assert columns._v_name == "columns"

        # An Array
        array_ = fileh.getNode(columns, "TDC", classname="Array")
        assert array_._v_name == "TDC"

        # (The new LRU code defers the appearance of a warning to this point).

        # An unsupported object (the deprecated H5T_ARRAY type in
        # Array, from pytables 0.8 on)
        ui = fileh.getNode(columns, "pressure", classname="UnImplemented")
        assert ui._v_name == "pressure"
        if verbose:
            print "UnImplement object -->",repr(ui)

        # Reset the warnings
        # Be careful with that, because this enables all the warnings
        # on the rest of the tests!
        #warnings.resetwarnings()
        # better use:
        warnings.filterwarnings("default", category=UserWarning)

        # A Table
        table = fileh.getNode("/detector", "table", classname="Table")
        assert table._v_name == "table"

        fileh.close()

    def test04b_UnImplementedOnLoading(self):
        """Checking failure loading resulting in an ``UnImplemented`` node"""

        ############### Note for developers ###############################
        # This test fails if you have the line:                           #
        # ##return childClass(self, childName)  # uncomment for debugging #
        # uncommented in Group.py!                                        #
        ###################################################################

        h5file = self.assertWarns(
            UserWarning, openFile, common.testFilename('smpl_unsupptype.h5'))
        try:
            node = self.assertWarns(
                UserWarning, h5file.getNode, '/CompoundChunked')
            self.assert_(isinstance(node, UnImplemented))
        finally:
            h5file.close()

    def test05_copyUnimplemented(self):
        """Checking that an UnImplemented object cannot be copied"""

        # Open an existing generic HDF5 file
        # We don't need to wrap this in a try clause because
        # it has already been tried and the warning will not happen again
        fileh = openFile(common.testFilename("ex-noattr.h5"), mode="r")
        # An unsupported object (the deprecated H5T_ARRAY type in
        # Array, from pytables 0.8 on)
        ui = fileh.getNode(fileh.root.columns, "pressure")
        assert ui._v_name == "pressure"
        if verbose:
            print "UnImplement object -->",repr(ui)

        # Check that it cannot be copied to another file
        file2 = tempfile.mktemp(".h5")
        fileh2 = openFile(file2, mode = "w")
        # Force the userwarning to issue an error
        warnings.filterwarnings("error", category=UserWarning)
        try:
            ui.copy(fileh2.root, "newui")
        except UserWarning:
            if verbose:
                (type, value, traceback) = sys.exc_info()
                print "\nGreat!, the next UserWarning was catched:"
                print value
        else:
            self.fail("expected an UserWarning")

        # Reset the warnings
        # Be careful with that, because this enables all the warnings
        # on the rest of the tests!
        #warnings.resetwarnings()
        # better use:
        warnings.filterwarnings("default", category=UserWarning)

        # Delete the new (empty) file
        fileh2.close()
        os.remove(file2)

        fileh.close()



class PythonAttrsTestCase(common.TempFileMixin, common.PyTablesTestCase):

    """Test interactions of Python attributes and child nodes."""

    def test00_attrOverChild(self):
        """Setting a Python attribute over a child node."""

        root = self.h5file.root

        # Create ``/test`` and overshadow it with ``root.test``.
        child = self.h5file.createArray(root, 'test', [1])
        attr = 'foobar'
        self.assertWarns(NaturalNameWarning,
                         setattr, root, 'test', attr)

        self.assert_(root.test is attr)
        self.assert_(root._f_getChild('test') is child)

        # Now bring ``/test`` again to light.
        del root.test

        self.assert_(root.test is child)

        # Now there is no *attribute* named ``test``.
        self.assertRaises(AttributeError,
                          delattr, root, 'test')


    def test01_childUnderAttr(self):
        """Creating a child node under a Python attribute."""

        h5file = self.h5file
        root = h5file.root

        # Create ``root.test`` and an overshadowed ``/test``.
        attr = 'foobar'
        root.test = attr
        self.assertWarns(NaturalNameWarning,
                         h5file.createArray, root, 'test', [1])
        child = h5file.getNode('/test')

        self.assert_(root.test is attr)
        self.assert_(root._f_getChild('test') is child)

        # Now bring ``/test`` again to light.
        del root.test

        self.assert_(root.test is child)

        # Now there is no *attribute* named ``test``.
        self.assertRaises(AttributeError,
                          delattr, root, 'test')


    def test02_nodeAttrInLeaf(self):
        """Assigning a ``Node`` value as an attribute to a ``Leaf``."""

        h5file = self.h5file

        array1 = h5file.createArray('/', 'array1', [1])
        array2 = h5file.createArray('/', 'array2', [1])

        # This may make the garbage collector work a little.
        array1.array2 = array2
        array2.array1 = array1

        # Check the assignments.
        self.assert_(array1.array2 is array2)
        self.assert_(array2.array1 is array1)
        self.assertRaises(TypeError,  # ``/array1`` is not a group
                          h5file.getNode, '/array1/array2')
        self.assertRaises(TypeError,  # ``/array2`` is not a group
                          h5file.getNode, '/array2/array3')


    def test03_nodeAttrInGroup(self):
        """Assigning a ``Node`` value as an attribute to a ``Group``."""

        h5file = self.h5file
        root = h5file.root

        array = h5file.createArray('/', 'array', [1])

        # Assign the array to a pair of attributes,
        # one of them overshadowing the original.
        root.arrayAlias = array
        self.assertWarns(NaturalNameWarning,
                         setattr, root, 'array', array)

        # Check the assignments.
        self.assert_(root.arrayAlias is array)
        self.assert_(root.array is array)
        self.assertRaises(NoSuchNodeError, h5file.getNode, '/arrayAlias')
        self.assert_(h5file.getNode('/array') is array)

        # Remove the attribute overshadowing the child.
        del root.array
        # Now there is no *attribute* named ``array``.
        self.assertRaises(AttributeError,
                          delattr, root, 'array')



class StateTestCase(common.TempFileMixin, common.PyTablesTestCase):

    """
    Test that ``File`` and ``Node`` operations check their state (open
    or closed, readable or writable) before proceeding.
    """

    def test00_fileCopyFileClosed(self):
        """Test copying a closed file."""

        h5cfname = tempfile.mktemp(suffix='.h5')
        self.h5file.close()

        try:
            self.assertRaises(ClosedFileError,
                              self.h5file.copyFile, h5cfname)
        finally:
            if os.path.exists(h5cfname):
                os.remove(h5fcname)
                self.fail("a (maybe incomplete) copy "
                          "of a closed file was created")


    def test01_fileCloseClosed(self):
        """Test closing an already closed file."""

        self.h5file.close()

        try:
            self.h5file.close()
        except ClosedFileError:
            self.fail("could not close an already closed file")


    def test02_fileFlushClosed(self):
        """Test flushing a closed file."""

        self.h5file.close()
        self.assertRaises(ClosedFileError, self.h5file.flush)


    def test03_fileFlushRO(self):
        """Flushing a read-only file."""

        self._reopen('r')

        try:
            self.h5file.flush()
        except FileModeError:
            self.fail("could not flush a read-only file")


    def test04_fileCreateNodeClosed(self):
        """Test creating a node in a closed file."""

        self.h5file.close()
        self.assertRaises(ClosedFileError,
                          self.h5file.createGroup, '/', 'test')


    def test05_fileCreateNodeRO(self):
        """Test creating a node in a read-only file."""

        self._reopen('r')
        self.assertRaises(FileModeError,
                          self.h5file.createGroup, '/', 'test')


    def test06_fileRemoveNodeClosed(self):
        """Test removing a node from a closed file."""

        self.h5file.createGroup('/', 'test')
        self.h5file.close()
        self.assertRaises(ClosedFileError,
                          self.h5file.removeNode, '/', 'test')


    def test07_fileRemoveNodeRO(self):
        """Test removing a node from a read-only file."""

        self.h5file.createGroup('/', 'test')
        self._reopen('r')
        self.assertRaises(FileModeError,
                          self.h5file.removeNode, '/', 'test')


    def test08_fileMoveNodeClosed(self):
        """Test moving a node in a closed file."""

        self.h5file.createGroup('/', 'test1')
        self.h5file.createGroup('/', 'test2')
        self.h5file.close()
        self.assertRaises(ClosedFileError,
                          self.h5file.moveNode, '/test1', '/', 'test2')


    def test09_fileMoveNodeRO(self):
        """Test moving a node in a read-only file."""

        self.h5file.createGroup('/', 'test1')
        self.h5file.createGroup('/', 'test2')
        self._reopen('r')
        self.assertRaises(FileModeError,
                          self.h5file.moveNode, '/test1', '/', 'test2')


    def test10_fileCopyNodeClosed(self):
        """Test copying a node in a closed file."""

        self.h5file.createGroup('/', 'test1')
        self.h5file.createGroup('/', 'test2')
        self.h5file.close()
        self.assertRaises(ClosedFileError,
                          self.h5file.copyNode, '/test1', '/', 'test2')


    def test11_fileCopyNodeRO(self):
        """Test copying a node in a read-only file."""

        self.h5file.createGroup('/', 'test1')
        self._reopen('r')
        self.assertRaises(FileModeError,
                          self.h5file.copyNode, '/test1', '/', 'test2')


    def test13_fileGetNodeClosed(self):
        """Test getting a node from a closed file."""

        self.h5file.createGroup('/', 'test')
        self.h5file.close()
        self.assertRaises(ClosedFileError, self.h5file.getNode, '/test')


    def test14_fileWalkNodesClosed(self):
        """Test walking a closed file."""

        self.h5file.createGroup('/', 'test1')
        self.h5file.createGroup('/', 'test2')
        self.h5file.close()
        self.assertRaises(ClosedFileError, self.h5file.walkNodes().next)


    def test15_fileAttrClosed(self):
        """Test setting and deleting a node attribute in a closed file."""

        self.h5file.createGroup('/', 'test')
        self.h5file.close()
        self.assertRaises(ClosedFileError,
                          self.h5file.setNodeAttr, '/test', 'foo', 'bar')
        self.assertRaises(ClosedFileError,
                          self.h5file.delNodeAttr, '/test', 'foo')


    def test16_fileAttrRO(self):
        """Test setting and deleting a node attribute in a read-only file."""

        self.h5file.createGroup('/', 'test')
        self.h5file.setNodeAttr('/test', 'foo', 'foo')
        self._reopen('r')
        self.assertRaises(FileModeError,
                          self.h5file.setNodeAttr, '/test', 'foo', 'bar')
        self.assertRaises(FileModeError,
                          self.h5file.delNodeAttr, '/test', 'foo')


    def test17_fileUndoClosed(self):
        """Test undo operations in a closed file."""

        self.h5file.enableUndo()
        self.h5file.createGroup('/', 'test2')
        self.h5file.close()
        self.assertRaises(ClosedFileError, self.h5file.isUndoEnabled)
        self.assertRaises(ClosedFileError, self.h5file.getCurrentMark)
        self.assertRaises(ClosedFileError, self.h5file.undo)
        self.assertRaises(ClosedFileError, self.h5file.disableUndo)


    def test18_fileUndoRO(self):
        """Test undo operations in a read-only file."""

        self.h5file.enableUndo()
        self.h5file.createGroup('/', 'test')
        self._reopen('r')
        self.assert_(self.h5file._undoEnabled == False)
        #self.assertRaises(FileModeError, self.h5file.undo)
        #self.assertRaises(FileModeError, self.h5file.disableUndo)


    def test19_getNode(self):
        """Test getting a child of a closed node."""

        g1 = self.h5file.createGroup('/', 'g1')
        g2 = self.h5file.createGroup('/g1', 'g2')

        # Close this *object* so that it should not be used.
        g1._f_close()
        self.assertRaises(ClosedNodeError, g1._f_getChild, 'g2')

        # Getting a node by its closed object is not allowed.
        self.assertRaises(ClosedNodeError,
                          self.h5file.getNode, g1)

        # Going through that *node* should reload it automatically.
        try:
            g2_ = self.h5file.getNode('/g1/g2')
        except ClosedNodeError:
            self.fail("closed parent group has not been reloaded")

        # Open nodes should still remain the same.
        self.assert_(g2_ is g2,
                     "open child of closed group has been reloaded")

        # And closed ones should not have been touched.
        g1_ = self.h5file.getNode('/g1/g2')
        self.assert_(g1_ is not g1, "closed node has been reused")


    def test20_removeNode(self):
        """Test removing a closed node."""

        # This test is a little redundant once we know that ``File.getNode()``
        # will reload a closed node, but anyway...

        group = self.h5file.createGroup('/', 'group')
        array = self.h5file.createArray('/group', 'array', [1])

        # The closed *object* can not be used.
        group._f_close()
        self.assertRaises(ClosedNodeError, group._f_remove)
        self.assertRaises(ClosedNodeError, self.h5file.removeNode, group)

        # Still, the *node* is reloaded when necessary.
        try:
            self.h5file.removeNode('/group', recursive=True)
        except ClosedNodeError:
            self.fail("closed node has not been reloaded")

        # Objects of descendent removed nodes
        # should have been automatically closed when removed.
        self.assertRaises(ClosedNodeError, array._f_remove)

        self.assert_('/group/array' not in self.h5file)  # just in case
        self.assert_('/group' not in self.h5file)  # just in case


    def test21_attrsOfNode(self):
        """Test manipulating the attributes of a closed node."""

        node = self.h5file.createGroup('/', 'test')
        nodeAttrs = node._v_attrs

        nodeAttrs.test = attr = 'foo'

        node._f_close()
        self.assertRaises(ClosedNodeError, getattr, node, '_v_attrs')
        # The design of ``AttributeSet`` does not yet allow this test.
        ## self.assertRaises(ClosedNodeError, getattr, nodeAttrs, 'test')

        self.assertEqual(self.h5file.getNodeAttr('/test', 'test'), attr)


    def test21b_attrsOfNode(self):
        """Test manipulating the attributes of a node in a read-only file."""

        self.h5file.createGroup('/', 'test')
        self.h5file.setNodeAttr('/test', 'test', 'foo')

        self._reopen('r')
        self.assertRaises(FileModeError,
                          self.h5file.setNodeAttr, '/test', 'test', 'bar')


    def test22_fileClosesNode(self):
        """Test node closing because of file closing."""

        node = self.h5file.createGroup('/', 'test')

        self.h5file.close()
        self.assertRaises(ClosedNodeError, getattr, node, '_v_attrs')


class FlavorTestCase(common.TempFileMixin, common.PyTablesTestCase):

    """
    Test that setting, getting and changing the ``flavor`` attribute
    of a leaf works as expected.
    """

    array_data = numpy.arange(10)

    def _reopen(self, mode='r'):
        super(FlavorTestCase, self)._reopen(mode)
        self.array = self.h5file.getNode('/test')
        return True

    def setUp(self):
        super(FlavorTestCase, self).setUp()
        self.array = self.h5file.createArray('/', 'test', self.array_data)

    def tearDown(self):
        self.array = None
        super(FlavorTestCase, self).tearDown()

    def test00_invalid(self):
        """Setting an invalid flavor."""
        self.assertRaises(FlavorError, setattr, self.array, 'flavor', 'foo')

    def test01_readonly(self):
        """Setting a flavor in a read-only file."""
        self._reopen(mode='r')
        self.assertRaises( FileModeError,
                           setattr, self.array, 'flavor', 'numpy' )

    def test02_change(self):
        """Changing the flavor and reading data."""
        for flavor in all_flavors:
            self.array.flavor = flavor
            self.assertEqual(self.array.flavor, flavor)
            idata = array_of_flavor(self.array_data, flavor)
            odata = self.array[:]
            self.assert_(common.allequal(odata, idata, flavor))

    def test03_store(self):
        """Storing a changed flavor."""
        for flavor in all_flavors:
            self.array.flavor = flavor
            self.assertEqual(self.array.flavor, flavor)
            self._reopen(mode='r+')
            self.assertEqual(self.array.flavor, flavor)

    def test04_missing(self):
        """Reading a dataset of a missing flavor."""
        flavor = self.array.flavor  # default is internal
        self.array._v_attrs.FLAVOR = 'foobar'  # breaks flavor
        self._reopen(mode='r')
        idata = array_of_flavor(self.array_data, flavor)
        odata = self.assertWarns(FlavorWarning, self.array.read)
        self.assert_(common.allequal(odata, idata, flavor))



#----------------------------------------------------------------------

def suite():
    theSuite = unittest.TestSuite()
    niter = 1

    for i in range(niter):
        theSuite.addTest(unittest.makeSuite(OpenFileTestCase))
        theSuite.addTest(unittest.makeSuite(CheckFileTestCase))
        theSuite.addTest(unittest.makeSuite(PythonAttrsTestCase))
        theSuite.addTest(unittest.makeSuite(StateTestCase))
        theSuite.addTest(unittest.makeSuite(FlavorTestCase))

    return theSuite


if __name__ == '__main__':
    unittest.main( defaultTest='suite' )

## Local Variables:
## mode: python
## End:
