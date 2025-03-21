from setuptools import setup, find_packages

setup(
    name="proxy-manager",
    version="0.1.0",
    description="Efficient proxy management package with automatic collection and validation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Coub Team",
    author_email="support@coub.com",
    url="https://github.com/coub/proxy-manager",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "appdirs>=1.4.4",
        "beautifulsoup4>=4.9.3",
        "requests>=2.25.1",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: Proxy Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    keywords="proxy, proxy-manager, proxy-checker, proxy-collector",
)
