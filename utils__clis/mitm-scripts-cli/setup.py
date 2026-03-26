from setuptools import setup, find_packages

setup(
    name='mitm-scripts',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['mgraph-ai-service-cache-client'],
    entry_points={
        'console_scripts': [
            'mitm-scripts=mitm_scripts.cli:main',
        ],
    },
)
