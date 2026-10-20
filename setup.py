from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="git-changelog-craft",
    version="0.1.0",
    author="slopggobblercobbler81",
    author_email="slopggobblercobbler81@users.noreply.github.com",
    description="Fast CLI analyzing conventional git commits, tags, and PRs to generate changelogs, release notes, and version bumps.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/slopggobblercobbler81/git-changelog-craft",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Software Development :: Build Tools",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "git-changelog-craft=git_changelog_craft.cli:main",
        ],
    },
)
