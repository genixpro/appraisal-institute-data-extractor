import os

from setuptools import setup, find_packages
''
here = os.path.abspath(os.path.dirname(__file__))

requires = [
    "selenium",
    "commonregex",
    "uszipcode"
]

tests_require = [

]

setup(
    name='appraisal-institute-data-extractor',
    version='0.0',
    description='appraisal-institute-data-extractor',
    long_description="",
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='',
    author_email='',
    url='',
    keywords='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    package_data={
        'appraisal-institute-data-extractor': [

        ]
    },
    install_requires=requires,
    entry_points={
        'console_scripts': [

        ]
    },
)
