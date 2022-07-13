from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

version = {}
with open('kijiji_manager/version.py', encoding='utf-8') as f:
    exec(f.read(), version)

setup(
    name='kijiji-manager',
    version=version['__version__'],
    author='jackm',
    author_email='jackm@ehelion.com',
    description='App for viewing, posting, reposting, and deleting your Kijiji ads',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/jackm/kijiji-manager',
    keywords='kijiji, ad, manager, reposter, automation, bot, flask',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    license='MIT',
    packages=find_packages(),

    python_requires='>=3.7',
    install_requires=[
        'Flask~=2.1.0',
        'Flask-WTF>=1.0.1',
        'Flask-Login>=0.6.0',
        'Flask-Executor',
        'WTForms>=3.0.0',
        'httpx~=0.23.0',
        'xmltodict>=0.11',
        'is-safe-url',
        'phonenumbers',
        'pgeocode',
    ],
    entry_points={
        'console_scripts': ['kijiji-manager=kijiji_manager.__main__:main']
    },
    include_package_data=True,
    zip_safe=False,
)
