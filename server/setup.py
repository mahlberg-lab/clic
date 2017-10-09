from setuptools import setup

setup(
  name="clic",
  packages=['clic'],
  entry_points={
        'console_scripts': [
            'recreate_rdb=clic.clicdb:recreate_rdb',
            'store_documents=clic.clicdb:store_documents',
        ],
    },
)
