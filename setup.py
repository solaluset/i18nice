import re

from setuptools import setup


GITHUB_URL = "https://github.com/Krutyi-4el/i18nice"
long_description = open("README.md").read()
# links on PyPI should have absolute URLs
long_description = re.sub(
    r"(\[[^\]]+\]\()((?!https?:)[^\)]+\))",
    f"\\1{GITHUB_URL}/blob/master/\\2",
    long_description,
)

setup(
    name='i18nice',
    version="0.11.0",
    description='Translation library for Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Daniel Perez',
    author_email='tuvistavie@gmail.com',
    maintainer="Krutyi 4el",
    url=GITHUB_URL,
    download_url=GITHUB_URL + "/archive/master.zip",
    license='MIT',
    packages=['i18n', 'i18n.loaders'],
    package_data={
        "": ["py.typed"],
    },
    zip_safe=True,
    test_suite='i18n.tests',
    extras_require={
        'YAML': ["pyyaml>=3.10"],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Internationalization',
    ],
)
