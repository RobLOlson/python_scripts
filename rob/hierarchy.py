#hierarchy.py
#Provides functions and classes for organizing text into fields in a console.
# Convenience Functions:
#
#  hier_out(...) <-- Takes a nested list and generates an ASCII tree
#
# Classes:
#
#  Hierarchy(...) <-- Represents objects that associate in a hierarchy
#
# One-off niche helper functions:
#
#   join_contiguous(...) <-- Merges consecutive, nested lists
#   list_depth(...) <-- returns the depth of nesting as an integer
#
#
#Rob O.
#Last Updated: 8/25/2014

import weakref


class HierarchyError(Exception):
    """Indicates an exception emanating from the Hierarchy class."""

class Hierarchy(object):
    """Initializer is an element name, or a hierarchically nested list.

Objects that subclass Hierarchy will be able to:

* Have children via the self.insert(...)
* Change parentage by assigning to the self.parent attribute
* Reorganize their children with the self.permute_children(...) method

A "hierarchically nested list" is converted into a hierarchy as follows:

* The first string in the list is the element's name.
* If the list has no string element, its name is derived from its parent's name.
* If the list has no parent (i.e., if the element is the root), its default
    name is 'root'.
* Remaining non-list elements are passed to the initializer so they can be
    used by Sub-Classes (the base class ignores the remaining elements).
* Remaining list elements are recursively parsed following the above criteria.

NOTE: The parser is flexible enough to handle any nested list, although the
      result may need tweaking if the original list was not properly structured.
      The hier_out(...) function will give you a visual indication of how the
      Hierarchy class will interpret any given nested list.

EXAMPLES:

>>> print Hierarchy('A hierarchical singleton')
+------------------------+
|A hierarchical singleton|
+------------------------+
>>> h = Hierarchy('root')
>>> h.insert('child')
>>> print h
+-------+
| root  |
|+-----+|
||child||
|+-----+|
+-------+
>>> print Hierarchy(['root',['child 1',['grand-child']],['child 2']])
+------------------------+
|          root          |
|+-------------++-------+|
||   child 1   ||child 2||
||+-----------+|+-------+|
|||grand-child||         |
||+-----------+|         |
|+-------------+         |
+------------------------+
"""
    def __init__(self, initializer='root', parent=None, *args): #Remove *args?


        self.name = None
        self._sisters = []
        self._daughters = []
        self._parent = None
        self._origin = self

        #Attempt to construct an arbitrarily nested hierarchy
        if isinstance(initializer, (list, tuple, dict)):

            #this recursive function does all the work
            temp = self._parse_list(initializer)

            if temp._parent == self:
                temp._parent = None

            for k in temp.__dict__.keys():
                setattr(self, k, getattr(temp, k))

        #construct a hierarchical singleton
        #which can be subsequently attached to an existing hierarchy
        else:
            self.name = initializer

            if parent:
                self.parent = parent

    def __getitem__(self, name):
        """Experimenting with special syntax...
A string index with the '=' symbol will be broken into two parts.
Example:
'name=super man' will return the first element with self.name == 'super man'.
'ID=99701' will return the first element with self.ID == 99701.

NOTE: Nested attributes are not allowed.  Only primitives and built-ins should
      be used in this way."""

        if isinstance(name, int):
            return self._daughters[name]

        if name.count("=") > 1:
            raise HierarchyError("'=' can appear only once per index specifier.")

        if '=' in name:
            attribute, value = name.split('=')
            attribute  = attribute.strip()
            value = value.strip()

            #return self._traverse(self.origin, value, attribute)
            return self._traverse(self, value, attribute)
        else:

            #the commented out return statement will return the first matching
            #element from ANYWHERE IN THE TREE...(the above return statment too)
            #As is, self.__get__item(...) only searches daughters of self.
            #return self._traverse(self.origin, value, attribute)
            return self._traverse(self, name)
        raise ValueError("{} not found in hierarchy.".format(name))

    def __setitem__(self, name, value):

        if "ID={}".format(value.ID) in self:
            raise HierarchyError("Cannot assign objects already in the hierarchy.")

        if isinstance(value, Hierarchy):

            if self[name]:

                if value._parent:
                    vp = value._parent
                    vp._daughters.remove(value)
                    for daughter in vp._daughters:
                        daughter._sisters.remove(value)

                target = self[name]
                tp = target._parent
                tp._daughters.remove(target)
                for daughter in tp._daughters:
                    daughter._sisters.remove(target)

                value.parent = tp


            else:
                raise ValueError("'{}' was not found.".format(name))
        else:
            raise HierarchyError("{} must be a hierarchical type.".format(value))

    def __len__(self):
        if self._daughters:
            return sum([len(daughter) for daughter in self._daughters])+1
        else:
            return 1

    def __repr__(self):
        class_Name = str(self.__class__)
        dot_Index = class_Name.rindex('.')
        class_Name = class_Name[dot_Index+1:-2]
        #class_Name = re.search(r"\.([A-Za-z_]+)'>$", class_Name)[0]

        return "{}('{}')".format(class_Name,self.name)

    def __str__(self):
        return self.render()

    def __contains__(self, value):
        try:
            self[value]
            return True
        except ValueError:
            return False

    @property
    def ID(self):
        """Read only."""
        return hash(self)

    @property
    def sisters(self):
        """Read only."""
        return self._sisters

    @property
    def daughters(self):
        """Read only."""
        return self._daughters
    @property
    def origin(self):
        """Read only."""
        return self._origin

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, target):
        """Removes self from current parent and makes target self's new parent.
Also cleans up secondary references, lateral references, etc."""

        try:
            self._traverse(self, target.ID, 'ID')
            raise HierarchyError("Cannot make a child element a parent.")
        except ValueError:
            pass

        if self._parent:
            old_Parent = self._parent
            old_Parent._daughters.remove(self)
            for daughter in old_Parent._daughters:
                daughter._sisters.remove(self)

        self._sisters = target._daughters[:]

        if target._daughters:
            for daughter in target._daughters:
                daughter._sisters.append(self)


        target._daughters.append(self)

        self._parent = target
        self._propagate(self, "_origin", target.origin)

    def _copy(self, depth = -1):
        """The recursive part of the self.copy() method."""
        temp = self.__class__(self.name)

        temp.__dict__ = self.__dict__.copy()

        if depth == 0:
            temp._daughters = []

        if depth > 0 or depth == -1:

            if depth > 0:
                depth -= 1

            #daughters are cached and the list is emptied so that copies
            #can be re-inserted individually using copy.parent assignment
            temp_daughters = [daughter.copy(depth) for daughter in temp._daughters]
            temp._daughters = []
            for daughter in temp_daughters:
                daughter._sisters = temp_daughters[:].remove(daughter)
                daughter.parent = temp

        return temp

    def _propagate(self, root, attribute, value):
        """Assign value to root.attribute and all of root's daughter.attribute."""

        setattr(root, attribute, value)

        for daughter in root._daughters:
            self._propagate(daughter, attribute, value)

    def _traverse(self, root, target, attribute = "name"):
        """Search the hierarchy from root->leaves for an element with target attribute."""
        prop = getattr(root, attribute, None)
        if prop:
            if prop == prop.__class__(target):
                return root
            else:
                for daughter in root._daughters:
                    temp = self._traverse(daughter, target, attribute)
                    if temp:
                        return temp

        if root==self:
            raise ValueError("{} not found in the hierarchy.".format(target))

    def _parse_list(self, nested_List):
        """Recursively turn a nested list/dictionary into a tree of Hierarchy objects."""

        # Handle the empty edge case
        if not nested_List:
            nested_list = ["root"]
        # Convert dictionary into a (str, list) tuple corresponding to (key, value)
        elif isinstance(nested_List, dict):
            nested_list = ["dict"]+[[str(k)+":->", (v if isinstance(v, (list, dict)) else [v])] for k, v in nested_List.items()]
        else:
            nested_list = nested_List[:]


        sub_Lists = [elem for elem in nested_list if isinstance(elem, (list, tuple, dict))]
        extra_Args = [elem for elem in nested_list if not isinstance(elem, (list, tuple, dict))]

        temp = self.__class__(", ".join([str(elem) for elem in extra_Args]), self, *extra_Args)

        daughters = [temp._parse_list(daughter) for daughter in sub_Lists]

        temp._daughters = daughters

        for daughter in daughters:
            daughter._parent = temp

        return temp

    def _list_depth(self, root):
        if root._daughters:
            return max([self._list_depth(elem) for elem in root.daughters])+1
        else:
            return 1

    def _frame_down(self, root, attributes=[]):
        from textframe import frame, parallelize
        contents = ""
        for attr in attributes:
            line = "{}.{}: {}".format(root.name,
                                      attr,
                                      getattr(root, attr, "Error"))
            contents += line + "\n"

        if contents:
            #strip trailing new line
            contents = contents[:-1]

        if not attributes:
            contents = root.name
        if root._daughters:
            daughter_boxes = [self._frame_down(elem, attributes=attributes) for elem in root._daughters]
            return frame(contents+("\n" if contents else "")+\
                         parallelize(daughter_boxes), hJust="c")
        else:
            return frame(contents, hJust='c')

    def _stringify(self, attributes=[], depth = 0):
        """Recursively lay self out along one line for each level of nesting.
TODO: Make indent and grouper variables to customize output style."""

        from text import parallelize

        if 'name' in attributes:
            attributes.remove('name')

        head = "\n"*depth + self.name
        attrs = ", ".join([repr(getattr(self, attr, "Error")) for attr in attributes])
        if attrs:
            head += "({})".format(attrs)

        foot = "\n"*depth + ">"

        if self._daughters:
            head += "<"

            canvas = [head]
            for daughter in self._daughters:
                canvas.append(daughter._stringify(attributes = attributes,
                                                  depth = depth+1))

                if self._daughters.index(daughter) != len(self._daughters)-1:
                    canvas.append("\n"*(depth+1) + ", ")
            canvas.append(foot)

            return parallelize(canvas)

        else:
            return head

    def _verticalize(self, attributes = [], depth = 0):
        """Recursively lay self out on lines.
TODO: Make indent and grouper variables to customize output style."""

        if 'name' in attributes:
            attributes.remove('name')

        attrs = ", ".join([repr(getattr(self, attr, "Error")) for attr in attributes])
        if attrs:
            attrs = "({})".format(attrs)

        if self._daughters:
            base_String = "  "*depth + str(self.name)+ attrs +"\n"+ "  "*depth + "<\n"
            for daughter in self._daughters:
                base_String += daughter._verticalize(attributes= attributes,
                                                     depth = depth+1) + "\n"

            base_String += "  "*depth + ">"

            return base_String

        else:
            return "  "*depth+str(self.name)+attrs

    def render(self, attributes=[], mode = "frames"):
        """Display the hierarchy visually.  Attributes is a list of attributes.

3 supported rendering modes:
MODE       - VALID STRING CODES
----------------------
frames     - 'frames', 'f'
vertical   - 'vertical', 'v'
horizontal - 'horizontal', 'h'"""

        try:
            from text import frame, parallelize
        except ImportError:
            mode = "v"

        #if my text module is available, use it to frame the hierarchy
        if mode in ("frames", "f"):
            return self._frame_down(self, attributes = attributes)

        #horizontal mode also requires my text module
        elif mode in ("horizontal", "h"):
            return self._stringify(attributes = attributes, depth = 0)

        #this is a simple fall-back representation
        elif mode in ("vertical", "v"):
            return self._verticalize(attributes = attributes, depth=0)

        return self._frame_down(self, attributes = attributes)

    def insert(self, *args):
        """If first argument is hierarchical, it is simply added as a child of self.
Otherwise, arguments are taken and passed to self.__init__(...) to generate
    a hierarchical object, which is added as a child of self."""

        if isinstance(args[0], Hierarchy):
            args[0].parent = self
        else:
            temp = self.__class__(*args)
            temp.parent = self

    def copy(self, depth=-1):
        """Return a copy of self including all children up to depth.
If depth == -1, copying is exhaustive.
If depth == 0, no children are copied (only self).
NOTE: Element ID's are based on location in memory.  (The copy will have a
different self.ID value than the original.)"""

        temp = self._copy(depth)
        temp._parent = None
        temp._propagate(temp, "_origin", temp)
        return temp

    def set_precedence(self, index):
        """Move this element to the index'th position among its siblings."""
        if self._parent:
            self._parent._daughters.remove(self)
            self._parent._daughters.insert(index,self)

        else:
            raise AttributeError("Root element has no index.")

    def permute_daughters(self, permutation):
        """Change the order of self's daughters to match that of permutation.
Examples:
The [0, 1, 2] permutation is the identity permutation.
The [2, 1, 0] permutation is equivalent to using reversed.
The [0,2,4,...,1,3,5,...] permutation organizes daughters by parity."""

        if len(permutation) != len(self._daughters):
            raise HierarchyError("Permutation must have exactly 1 distinct index for each daughter.")

        if sorted(permutation)!=range(len(permutation)):
            raise HierarchyError("Permutation indeces must range from 0 to n in increments of 1.")

        #This code allows greater flexibility in the permutation argument
        #Any iterable with a distinct ordering will work
        #But that seemed like a good hiding place for bugs, so its out for now.
        #permutation = [permutation.index(elem) for elem in sorted(permutation)]

        for elem, index in zip(self._daughters[:], permutation):
            elem.set_precedence(index)

    def transfer(self):
        pass


def list_depth(nestedList):
    """A non-list object has 0 depth.  A simple list has a depth of 1.  Etc."""

    if isinstance(nestedList, (list, tuple)):
        return max([list_depth(elem) for elem in nestedList])+1
    else:
        return 0

def join_contiguous(theList, depth = -1):
    """Joins 2 or more consecutive containers in theList, up to specified depth.
If depth == -1, ALL levels of nesting are affected.
If depth == 0, the function does nothing.
If depth == 1, once-nested lists are affected.
If depth == 2, twice-nested lists are also affected.
...etc..."""

    if depth > 0 or depth == -1:

        i = 0
        #This loop cycles through the outer-most list, looking for 2 consecutive
        #list or tuple elements.  Those 2 elements are replaced by the union.
        #The union is, itself, a list so that if there is a 3rd consecutive
        #list or tuple, it will be caught during the loop's, next iteration, etc
        while i + 1 < len(theList):
            if isinstance(theList[i], (tuple, list)):
                if isinstance(theList[i+1], (tuple, list)):
                    temp = list(theList[i]) + list(theList[i+1])
                    theList.insert(i, temp)
                    del theList[i+1]
                    del theList[i+1]
                    continue
            i+=1

        if depth == -1:
            depth += 1

        #This loop goes through the list, replacing each nested list with
        #a copy that has, itself, been conjoined by a recursive call of
        #this function
        for subList in theList[:]:
            if isinstance(subList, (list, tuple)):
                n = theList.index(subList)
                theList.remove(subList)
                theList.insert(n, join_contiguous(subList, depth-1))
    return theList

def hier_out(hierarchical_Object, mode = 'f'):
    """Returns a string representation of the passed object.

EXAMPLES:
>>> print hier_out(['parent',['child']])
+-------+
|parent |
|+-----+|
||child||
|+-----+|
+-------+
>>> print hier_out(['parent',['child',['grand-child']]], mode = 'v')
parent
<
  child
  <
    grand-child
  >
>
>>> print hier_out(['root',['1',['a'],['b']],['2',['i'],['ii']]], mode = 'h')
root<                 >
     1<    >, 2<     >
       a, b     i, ii
"""
    try:
        return hierarchical_Object.render(mode= mode)
    except AttributeError:
        return Hierarchy(hierarchical_Object).render(mode= mode)

if __name__ == "__main__":
    import unittest, doctest
    from testhierarchy import *

    #A simple instance for debugging purposes
    h = Hierarchy(['r',['t'],['b']])

    doctest.testmod()
    unittest.main()
