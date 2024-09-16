from setuptools import setup, find_packages

requires = [
    'Flask',
    'flask-cors',
    'uWSGI',
    'pandas',
    'psycopg2',
    'pybtex',
    'pylatexenc',
    'pyicu',
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
    license="MIT",
    packages=find_packages(),
    install_requires=requires,
    extras_require=dict(
       testing=tests_require,
    ),
    entry_points={
        'console_scripts': [
            'import_cheshire_json=clic.migrate.cheshire_json:script_import_cheshire_json',
            'import_corpora_repo=clic.migrate.corpora_repo:script_import_corpora_repo',
            'region_export=clic.migrate.corpora_repo:script_region_export',
            'region_preview=clic.migrate.region_preview:script_region_preview',
        ],
    },
)
