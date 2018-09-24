from setuptools import setup, find_packages

requires = [
    'Flask',
    'uWSGI',
    'pandas',
    'unidecode',
]

tests_require = [
    'pytest',
    'pytest-cov',
    'testing.postgresql',
]

setup(
    name="clic",
    description='CLiC web API',
    author='Jamie Lentin',
    author_email='jamie.lentin@shuttlethread.com',
    url='https://github.com/birmingham-ccr/clic',
    packages=find_packages(),
    install_requires=requires,
    extras_require=dict(
       testing=tests_require,
    ),
    entry_points={
        'console_scripts': [
            'recreate_rdb=clic.clicdb:recreate_rdb',
            'store_documents=clic.clicdb:store_documents',
        ],
    },
)
