from setuptools import setup

setup(
    name='python-i18n',
    version='0.6.0',
    description='Translation library for Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Daniel Perez',
    author_email='tuvistavie@gmail.com',
    url='https://github.com/Krutyi-4el/python-i18n',
    download_url='https://github.com/Krutyi-4el/python-i18n/archive/master.zip',
    license='MIT',
    packages=['i18n', 'i18n.loaders', 'i18n.tests'],
    include_package_data=True,
    zip_safe=True,
    test_suite='i18n.tests',
    extras_require={
        'YAML': ["pyyaml>=3.10"],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ],
)
