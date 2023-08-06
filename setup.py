from setuptools import setup

setup(
    name='i18nice',
    version='0.8.0',
    description='Translation library for Python',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Daniel Perez',
    author_email='tuvistavie@gmail.com',
    maintainer="Krutyi 4el",
    url='https://github.com/Krutyi-4el/i18nice',
    download_url='https://github.com/Krutyi-4el/i18nice/archive/master.zip',
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
