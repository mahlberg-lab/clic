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

for algo_type, algos in fc.algorithms_by_type().items():
    for a in algos:
        print("\n\n==== %s:%s" % (algo_type, a['label']))
        print("\n".join(fc.algorithm_render_html(algo_name=a['name'], index=0)))
