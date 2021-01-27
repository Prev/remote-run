import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='remote-run',
    version='0.1.0',
    author='Youngsoo Lee',
    author_email='prevdev@gmail.com',
    description='CLI tool for running tasks in a remote worker using only SSH',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "remote-run = remote_run.cli:main",
        ],
    },
    install_requires=[
        'paramiko',
        'fire',
        'gitignore_parser',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.5',
)
