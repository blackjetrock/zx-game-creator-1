from setuptools import setup, find_packages

setup(
    name="zxcreator",
    version="1.0.0",
    description="ZX Spectrum Game Creator Tool - Outputs Z80 Assembly and TAP Machine Code for All Game Genres",
    author="Google DeepMind Team / Antigravity",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "zxcreator.web": ["static/*"],
    },
    entry_points={
        "console_scripts": [
            "zxcreator=zxcreator.cli:main",
        ],
    },
    python_requires=">=3.8",
)
