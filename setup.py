########################################

import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

########################################

setup(
    name="muaradata",
    version="0.1.0",
    author="Redian Barqy M",
    author_email="rbm.eki@gmail.com",
    description="Pustaka Python untuk koneksi multi-database dengan fitur auto-retry dan SSH tunneling.",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    
    packages=find_packages(),
    
    install_requires=[
        "pandas",
        "numpy",
        "psycopg2-binary",
        "clickhouse-driver",
        "clickhouse-connect",
        "mysql-connector-python",
        "sshtunnel",
        "tqdm",
        "rich",
        "tabulate",
        "cryptography",
        "platformdirs",
    ],
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    
    url="https://github.com/rbarqm/muaradata",
    
    python_requires='>=3.7',
    
    entry_points={
        "console_scripts": [
            "muaradb = muaradata.credentials.app:main",
        ],
    },
)
