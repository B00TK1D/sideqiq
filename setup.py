from setuptools import setup

def read_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()

setup(
    name='sideqiq',
    version='0.2',
    py_modules=['qiq'],
    entry_points={
        'console_scripts': [
            'qiq=qiq:main',
        ],
    },
    author='B00TK1D',
    author_email='B00TK1D@proton.me',
    description='A terminal chat powered by GPT-4o, requiring only a copilot subscription, with a few nice terminal features',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/B00TK1D/sideqiq',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache 2.0 License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=read_requirements(),
)
