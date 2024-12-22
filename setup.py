from setuptools import setup, find_packages

setup(
    name="dev-team-manager",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "redis",
        "prometheus_client",
    ],
)
