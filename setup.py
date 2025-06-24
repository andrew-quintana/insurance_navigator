from setuptools import setup, find_packages

setup(
    name="insurance_navigator",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "supabase",
        "pytest",
        "bcrypt",
        "python-dotenv",
    ],
    python_requires=">=3.8",
) 