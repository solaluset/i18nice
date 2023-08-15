import re
from urllib.parse import urljoin

from setuptools import setup


GITHUB_URL = "https://github.com/Krutyi-4el/i18nice"
long_description = open("README.md").read()
# links on PyPI should have absolute URLs
long_description = re.sub(
    r"(\[[^\]]+\]\()((?!https?:)[^\)]+)(\))",
    lambda m: m.group(1) + urljoin(GITHUB_URL, "blob/master/" + m.group(2)) + m.group(3),
    long_description,
)

setup(
    name='i18nice',
    version='0.8.1',
    description='Translation library for Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Daniel Perez',
    author_email='tuvistavie@gmail.com',
    maintainer="Krutyi 4el",
    url=GITHUB_URL,
    download_url=urljoin(GITHUB_URL, "archive/master.zip"),
    license='MIT',
    packages=['i18n', 'i18n.loaders'],
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
