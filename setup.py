from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='ibis-mssql',
    url='https://github.com/quansight/ibis-mssql',
    version='0.1.3',
    python_requires='>=3.6',
    description="Ibis backend for MSSQL",
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering',
    ],
    license='Apache License, Version 2.0',
    maintainer="Quansight",
    maintainer_email="costrouchov@quansight.com",
    packages=find_packages(),
    install_requires=["ibis-framework", "sqlalchemy", "pyodbc"],
    extras_require={
        'develop': [
            'black',
            'click',
            'pydocstyle==4.0.1',
            'flake8',
            'isort',
            'mypy',
            'pre-commit',
            'pygit2',
            'pytest>=4.5',
            'plumbum',
            'toolz',
            'pandas',
        ]
    },
)
