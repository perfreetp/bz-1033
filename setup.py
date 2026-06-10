from setuptools import setup, find_packages

setup(
    name="aicommunity",
    version="1.0.0",
    description="AI交流社区命令行工具 - 终端重度用户的社区内容管理助手",
    author="AI Community",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
        "PyYAML>=6.0.1",
        "python-dateutil>=2.8.2",
        "tabulate>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "aicomm=aicommunity.cli:cli",
        ],
    },
    python_requires=">=3.8",
)
