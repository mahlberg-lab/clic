'''
    ./bin/python tests/exerciser.py
'''
from flexiclic import FlexiClic

fc = FlexiClic(api_root="https://clic.bham.ac.uk")

fc.set_source_data(
    corpora="BH",
    subset="all",
    q="hoarding",
    contextsize=10,
    #metadata=["book_titles", "chapter_start"],
)

for x in fc.data_at(1, 0):
    print(x)

print(fc.algorithms_by_type())
