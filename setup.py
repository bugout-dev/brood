from setuptools import find_packages, setup

from brood.version import BROOD_VERSION

long_description = ""
with open("README.md") as ifp:
    long_description = ifp.read()

setup(
    name="bugout-brood",
    version=BROOD_VERSION,
    packages=find_packages(),
    install_requires=[
        "argon2_cffi",
        "boto3>=1.20.2",
        "fastapi>=0.70.0",
        "passlib",
        "psycopg2-binary",
        "pydantic",
        "python-multipart",
        "sendgrid",
        "sqlalchemy>=1.4.26",
        "stripe>=2.61.0",
        "uvicorn>=0.15.0",
    ],
    extras_require={
        "dev": ["alembic>=1.7.4", "black", "isort", "mypy"],
        "distribute": ["setuptools", "twine", "wheel"],
    },
    description="Brood: Bugout authentication",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Bugout.dev",
    author_email="engineering@bugout.dev",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Software Development :: Libraries",
    ],
    url="https://github.com/simiotics/brood",
    entry_points={
        "console_scripts": [
            "brood=brood.cli:main",
            "resources=brood.resources.cli:main",
        ]
    },
)
