import hierarchy
import unittest

class SimpleTests(unittest.TestCase):
    def test_string_input(self):
        h = hierarchy.Hierarchy('root')
        self.assertEqual((h.name,
                          len(h),
                          h.parent,
                          h.origin.name),
                         
                         ('root',
                          1,
                          None,
                          'root'))

    def test_simple_list(self):
        h = hierarchy.Hierarchy(['root'])
        self.assertEqual((h.name,
                          len(h),
                          h.parent,
                          h.origin.name),
                         
                         ('root',
                          1,
                          None,
                          'root'))

    def test_once_nested_list(self):
        h = hierarchy.Hierarchy(['root',['child']])
        self.assertEqual((h.name,
                          h['child'].name,
                          len(h._daughters)),
                         
                         ('root',
                          'child',
                          1))
        
    def test_twice_nested_list(self):
        h = hierarchy.Hierarchy(['root',['child', ['grand-child']]])
        self.assertEqual((h.name,
                          h['child'].name,
                          len(h._daughters),
                          h['grand-child'].name,
                          len(h['child']._daughters)),
                         
                         ('root',
                          'child',
                          1,
                          'grand-child',
                          1))

    def test_multiple_children(self):
        h = hierarchy.Hierarchy(['root',['top'],['bottom']])

        self.assertEqual((h.name,
                          len(h._daughters),
                          h['top'].name,
                          h['bottom'].name,
                          h['top'].parent.name,
                          h['bottom'].parent.name),

                         ('root',
                          2,
                          'top',
                          'bottom',
                          'root',
                          'root'))
                          
    def test_deeply_nested(self):
        h = hierarchy.Hierarchy(['root', ['top',['menu'],['out']],['bot',['prompt']]])

        self.assertEqual((h.name,
                          len(h._daughters),
                          h['top'].name,
                          len(h['top']._daughters),
                          h['top']._daughters[0].name,
                          h['menu'].name,
                          h['out'].name,
                          h['prompt'].name,
                          h['prompt'].parent.name,
                          h['prompt'].parent.parent.name,
                          h['out'].origin.name),

                         ('root',
                          2,
                          'top',
                          2,
                          'menu',
                          'menu',
                          'out',
                          'prompt',
                          'bot',
                          'root',
                          'root'))

    def test_parent_argument(self):
        h = hierarchy.Hierarchy('root')
        g = hierarchy.Hierarchy('child', h)
        i = hierarchy.Hierarchy('grand-child', g)

        self.assertEqual((h.name,
                          g.name,
                          i.name,
                          h.parent,
                          g.parent.name,
                          i.parent.name,
                          h['root'].name,
                          g['child'].name,
                          i['grand-child'].name),
                         
                         ('root',
                          'child',
                          'grand-child',
                          None,
                          'root',
                          'child',
                          'root',
                          'child',
                          'grand-child'))
                          
    def test_nested_plus_parent(self):
        h = hierarchy.Hierarchy(['root',['top'],['bot']])
        g = hierarchy.Hierarchy(['forgot',['one']], h['top'])

    def test_missing_root(self):
        h = hierarchy.Hierarchy([['implicit'],['children']])

        self.assertEqual((h.name,
                          h['implicit'].name,
                          len(h._daughters),
                          h['implicit'].parent.name,
                          h['children'].origin.name),

                         ('root',
                          'implicit',
                          2,
                          'root',
                          'root'))

    def test_empty_list(self):
        h = hierarchy.Hierarchy([])

        self.assertEqual((h.name,
                         len(h._daughters),
                         len(h),
                         h.parent),

                         ('root',
                          0,
                          1,
                          None))

    def test_nested_empty_lists(self):
        h = hierarchy.Hierarchy([[],[[],[]]])

        self.assertEqual((h.name,
                          len(h),
                          len(h._daughters),
                          h._daughters[0].name,
                          len(h['Child #2 of root']._daughters),
                          h._daughters[1]._daughters[1].name,
                          h._daughters[1]._daughters[1].origin.name),

                         ('root',
                          5,
                          2,
                          'Child #1 of root',
                          2,
                          'Child #2 of Child #2 of root',
                          'root'))

    def test_assignment(self):
        h = hierarchy.Hierarchy(['root',['child']])
        h['child'] = hierarchy.Hierarchy(['child2',['grand-child']])

        self.assertEqual((h.name,
                          len(h),
                          len(h._daughters),
                          h['child2'].name,
                          h['child2'].parent.name,
                          h['grand-child'].origin.name),

                         ('root',
                         3,
                         1,
                         'child2',
                         'root',
                         'root'))

    def test_same_names(self):
        """Same name children are ok.  They must have different id's."""
        h = hierarchy.Hierarchy(['root',['child'],['child']])

        self.assertEqual((len(h),
                          len(h._daughters),
                          h._daughters[0].name,
                          h._daughters[1].name,
                          h['child'].name,
                          h['child'].parent.name),

                         (3,
                          2,
                          'child',
                          'child',
                          'child',
                          'root'))

    def test_simple_insert_method(self):
        h = hierarchy.Hierarchy(['root',['child']])
        g = hierarchy.Hierarchy('grand-child')
        h['child'].insert(g)

        self.assertEqual((len(h),
                         len(g),
                         len(h['child']),
                         g.name,
                         g.parent.name,
                         g.origin.name,
                         h['child'].daughters[0].name),

                         (3,
                          1,
                          2,
                          'grand-child',
                          'child',
                          'root',
                          'grand-child'))

    def test_coercive_insert(self):
        h = hierarchy.Hierarchy(['root', ['child']])
        h.insert(['child 2'])
        h['child'].insert('grand-child')

        self.assertEqual((len(h),
                          len(h['child']),
                          h['child 2'].parent.name,
                          h['grand-child'].origin.name),

                         (4,
                          2,
                          'root',
                          'root'))

    def test_simple_copying(self):
        h = hierarchy.Hierarchy(['root',['child',['grand-child']]])
        g = h.copy()
        g['root'].name = 'root2'
        g['child'].name = 'child2'
        g['grand-child'].name = 'grand-child2'
        g.insert('child3')

        self.assertEqual((g==h,
                          len(h),
                          len(g),
                          g['grand-child2'].origin.name),

                         (False,
                          3,
                          4,
                          'root2'))

    def test_self_referential_copying(self):
        h = hierarchy.Hierarchy(['root',['child',['grand-child']]])
        h.insert(h.copy())
        h.insert(h.copy())

        self.assertEqual((len(h),
                          len(h.daughters)),

                         (12,
                          3))
        

class SimpleFailures(unittest.TestCase):
    
    def test_internal_assignment(self):
        """Assignment within a hierarchy is not allowed.  There are designated
methods for rearranging parts of a hierarchy instead."""
        h = hierarchy.Hierarchy(['root',['child',['grand-child']]])
        with self.assertRaises(hierarchy.HierarchyError):
            h['child'] = h['grand-child']


    def test_parent_to_child_assignment(self):
        """Cannot assign a child element to self's parent attribute."""
        h = hierarchy.Hierarchy(['root',['child',['grand-child']]])
        with self.assertRaises(hierarchy.HierarchyError):
            h.parent = h['child']

    def test_consecutive_indeces(self):
        """self.__getitem__ returns ONLY DESCENDANTS of self.  Therefore,
the following consecutive index idiom should always fail when a parent index
follows a child index.

NOTE: This behavior might change."""

        h = hierarchy.Hierarchy(['root',['child']])
        with self.assertRaises(ValueError):
            h['child']['root']



#h = Hierarchy(['Deep Ancestry',['Grandma',['Liz',['Robert'],['Brittney',['Josef']],['Richard'], ['Jenny',['Eryn']],['Wulf']],['Jennifer',['Willie'],['Emerald']]]])
#h = Hierarchy([['1'],[['2'],['3'],[['4'],['5']]],['6'],[['7']]])
if __name__=="__main__":
    unittest.main()
