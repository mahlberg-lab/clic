'''
    ./bin/python tests/exerciser.py
'''
import asyncio
from flexiclic import FlexiClic

fc = FlexiClic(api_root="https://clic.bham.ac.uk")

async def main():
    async for x in fc.compute_path(dict(
        corpora="BH",
        subset="all",
        q="hoarding",
        contextsize=10,
        #metadata=["book_titles", "chapter_start"],
    ), [], []):
        print(x)

asyncio.run(main())
