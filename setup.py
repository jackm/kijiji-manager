from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='kijiji-manager',
    version='0.1.8',
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

    python_requires='>=3.6',
    install_requires=[
        'Flask~=2.0.0',
        'Flask-WTF~=0.15.0',
        'Flask-Login',
        'Flask-Executor',
        'WTForms~=2.3.0',
        'httpx~=0.19.0',
        'xmltodict~=0.11',
        'is-safe-url',
        'phonenumbers',
    ],
    entry_points={
        'console_scripts': ['kijiji-manager=kijiji_manager.__main__:main']
    },
    include_package_data=True,
    zip_safe=False,
)
