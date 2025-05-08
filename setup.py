from setuptools import setup, find_packages

setup(
    name="insurance_navigator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langgraph>=0.0.15",
        "langchain-anthropic>=0.0.1",
        "langchain-community>=0.0.10",
        "python-dotenv>=1.0.0",
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.2",
        "pgvector>=0.2.3",
        "psycopg2-binary>=2.9.9",
        "llama-parse>=0.0.15",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "duckduckgo-search>=4.1.1",
        "wikipedia>=1.4.0",
        "supabase>=2.3.0"
    ],
    python_requires=">=3.9",
) 