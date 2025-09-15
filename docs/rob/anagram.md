rob.anagram — Word Anagram Finder

Summary

Generates anagrams from a word with optional wildcards.

CLI

```bash
python -m rob.anagram --help | cat
```

Python

```python
from rob.anagram import anagram

print(anagram("listen"))
print(anagram("listen", wilds=1))
```

