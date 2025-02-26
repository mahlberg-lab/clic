'''
    ./bin/python tests/exerciser.py
'''
from flexiclic import FlexiClic

fc = FlexiClic(api_root="https://clic.bham.ac.uk")

for x in fc.compute_path(dict(
    corpora="BH",
    subset="all",
    q="hoarding",
    contextsize=10,
    #metadata=["book_titles", "chapter_start"],
), []):
    print(x)
