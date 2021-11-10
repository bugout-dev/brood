from setuptools import find_packages, setup

from brood.version import BROOD_VERSION

long_description = ""
with open("README.md") as ifp:
    long_description = ifp.read()

setup(
    name="brood",
    version=BROOD_VERSION,
    packages=find_packages(),
    install_requires=[
        "argon2_cffi~=21.1.0",
        "boto3~=1.20.2",
        "fastapi~=0.70.0",
        "passlib~=1.7.4",
        "psycopg2-binary~=2.9.1",
        "pydantic~=1.8.2",
        "python-multipart~=0.0.5",
        "sendgrid~=6.9.0",
        "sqlalchemy~=1.4.26",
        "stripe~=2.61.0",
        "uvicorn~=0.15.0",
    ],
    extras_require={
        "dev": ["alembic", "black", "isort", "mypy"],
        "distribute": ["setuptools", "twine", "wheel"],
    },
    description="Brood: Bugout authentication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Neeraj Kashyap",
    author_email="neeraj@simiotics.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python",
    ],
    url="https://github.com/simiotics/brood",
    entry_points={
        "console_scripts": [
            "brood=brood.cli:main",
            "resources=brood.resources.cli:main",
        ]
    },
)
