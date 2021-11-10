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
        "argon2_cffi",
        "boto3",
        "fastapi",
        "passlib",
        "psycopg2-binary",
        "pydantic",
        "python-multipart",
        "sendgrid",
        "sqlalchemy",
        "stripe",
        "uvicorn",
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
