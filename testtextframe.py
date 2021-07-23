import textframe as t
import unittest
import pickle
import random

#---- Constants -------------------------------------------

ALPHABET = "abcdefghijklmnopqrstuvwxyz"

TEXTS = ["Simple Line of Text",
          "Two lines\nof Text",
          "One really, really, really long line of text that just keeps going and going and going and going and it will eventually stop but not now or now or now or now.  Or now.  Or now.  Or now.",
          "Supercalifragilisticexpialidocious1Supercalifragilisticexpialidocious2Supercalifragilisticexpialidocious3Supercalifragilisticexpialidocious4Supercalifragilisticexpialidocious5",
          """  This is a poem
used as input to test my
 computer program.""",
          """



testing blank lines



""",
"""   STOP,
  DROP,
 And...
ROLL!"""]

ARGS =[{},
             {"width": 15},
             {"width": 10, "height": 10},
             {"padding": 1},
             {"padding": 1, "width": 10},
             {"padding": -1},
             {"padding": -1, "width": 10, "topFrame": True},
             {"width": 50, "height": 10, "hJust": 'right'},
             {"width": 50, "height": 10, "hJust": 'center'},
             {"width": 50, "height": 10, "vJust": 'middle'},
             {"width": 50, "height": 10, "vJust": 'bot'},
             {"width": 50, "height": 10, "hJust": 'center', "vJust": 'middle'}]

#^^^^ Constants ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
#---- Test Cases ---------------------------------------------

class FramingCases(unittest.TestCase):
    def test_verified_output(self):
        """Tests that output matches that which was cached.
Cached output is assumed to be correct.
Cached output is generated by a top level function 'create_pickled_output()'
Human readable contents of the cache is produced by another top level function.
"""
        with open("text test calls.pkl","r") as f:
            verified = pickle.load(f)
            
        result = []
        for text in TEXTS:
            for args in ARGS:
                result.append(t.frame(text,**args))

        self.assertEqual("".join(verified),"".join(result))
        

class SimpleFramingCases(unittest.TestCase):
    def test_leading_whitespace(self):
        """Leading white-space should be preserved."""
        self.assertEqual(t.frame("ac\n c"),'+--+\n|ac|\n| c|\n+--+')

    def test_narrow_width(self):
        self.assertEqual((t.frame("1", padding=-1,width=1),
                          t.frame("1", padding=-1,width=2),
                          t.frame("11", padding=-1,width=1),
                          t.frame("11", padding=-1,width=2),
                          t.frame("1\n1\n1", padding=-1,width=1),
                          t.frame("1\n1\n1", padding=-1,width=2),
                          t.frame("11\n11\n11", padding=-1,width=1),
                          t.frame("11\n11\n11", padding=-1,width=2),
                          t.frame("1",width=1)),
                          ("1",
                           "1 ",
                           "1",
                           "11",
                           "1\n1\n1",
                           "1 \n1 \n1 ",
                           "1\n1\n1",
                           "11\n11\n11",
                           "+\n|\n+"))
                         

class ParallelizeCases(unittest.TestCase):
    def test_basic_input(self):
        self.assertEqual(t.parallelize(['1','2\n2','3\n3\n3']),
                         '123\n 23\n  3')

    def test_gibberish(self):
        words = ["".join(random.sample(ALPHABET, random.randint(0,10))) for n in range(10)]
        self.assertEqual(t.parallelize(words), "".join(words))

    def test_more_gibberish(self):
        #words contains 3 paragraphs of text, each one line longer than the last
        #the check method only works b/c the words are all 5 chars long
        words = ["\n".join(["".join(random.sample(ALPHABET, 5)) for n in range(1,j+1)]) for j in range(1,4)]
        plized = t.parallelize(words)
        words[0]+=("\n     ")
        words[0]+=("\n     ")
        words[1]+=("\n     ")
        words = [elem.split("\n") for elem in words]
        check = [words[0][0]+words[1][0]+words[2][0],
                 words[0][1]+words[1][1]+words[2][1],
                 words[0][2]+words[1][2]+words[2][2]]
        self.assertEqual(plized, "\n".join(check))

    def test_white_space(self):
        words = [".\n\n...\n\n.....","\n....\n\n..\n"]
        self.assertEqual(t.parallelize(words), ".        \n     ....\n...      \n     ..  \n.....    ")

    def test_widths(self):
        words = ['12345', 'abcde', '09876', 'zyxwv']
        self.assertEqual(t.parallelize(words,[4,3,2,1]),"1234abc09z")
    
class TableCases(unittest.TestCase):
    pass

class ColumnizeCases(unittest.TestCase):
    def test_basic_input(self):
        self.assertEqual(t.columnize(['a','b']),'+-+\n|a|\n+-+\n|b|\n+-+')

    def test_frameless_via_frames(self):
        lines = ["".join(random.sample(ALPHABET, 8)) for n in range(5)]
        self.assertEqual(t.columnize(lines, frames = False),"\n".join(lines))

    def test_fixed_width(self):
        lines = ["".join(random.sample(ALPHABET, 10)) for n in range(5)]
        cnized  = t.columnize(lines, 15, frames = False)
        lines = ["{:<15}".format(elem) for elem in lines]
        self.assertEqual(cnized, "\n".join(lines))

class PanelCases(unittest.TestCase):
    pass

#^^^^ Test Cases ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
#---- Utilities -----------------------------------------

def create_human_readable_output():
    with open("text tests (human readable).txt", "w") as f:
         for args in ARGS:
            for text in TEXTS:
                result = t.frame(text, **args)
                f.write("""Calling 't.frame("{}", **{})':\n{}\n"""\
                      .format(text, args, result))

def create_pickled_output():
    result = []
    for text in TEXTS:
        for args in ARGS:
            result.append(t.frame(text, **args))
    with open("text test calls.pkl","w") as f:
        pickle.dump(result, f)

def find_difference():
    with open("text test calls.pkl.", "r") as f:
        verified = pickle.load(f)
    result = []
    for text in TEXTS:
        for args in ARGS:
            result.append(t.frame(text, **args))

    differences = []
    
    for v_elem, r_elem in zip(verified, result):
        if v_elem != r_elem:
            differences.append((v_elem, r_elem))

    return differences

#^^^^ Utilities ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

if __name__=="__main__":
    create_pickled_output()
    unittest.main()
