from setuptools import setup, find_packages

setup(
    name='gentle-python-pptx',
    version='0.1.0',

    description='Processes pptx presentations, optimized for repetitive processing large ones',
    long_description=open('README.md').read(),
    url='https://github.com/ktsstudio/gentle-python-pptx',
    author='KTS Studio',
    author_email='o.morozenkov@ktsstudio.ru',
    license='MIT',
    packages=find_packages(),

    install_requires=['lxml>=4.2.5,<4.3']
)
