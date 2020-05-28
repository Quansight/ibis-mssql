from setuptools import setup

setup(
    name='ibis-mssql',
    url='https://github.com/quansight/ibis-mssql',
    version='0.1.0',
    python_requires='>=3.6',
    description="Ibis backend for MSSQL",
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
    install_requires=["ibis", "pyodbc"],
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
        ]
    },
)
