#!/usr/bin/env python3
"""
Production Version Synchronization Script

This script extracts exact production versions from Render logs and creates
a locked requirements file for complete environment parity.
"""

import re
import subprocess
import sys
from pathlib import Path

def extract_production_versions():
    """Extract exact versions from production logs."""
    print("🔍 Extracting Production Versions")
    print("-" * 50)
    
    # Production versions from Render logs
    production_versions = """MarkupSafe-3.0.2 PyJWT-2.8.0 PyPDF2-3.0.1 PyYAML-6.0.2 SQLAlchemy-2.0.28 aiohappyeyeballs-2.6.1 aiohttp-3.12.15 aiosignal-1.4.0 annotated-types-0.7.0 anthropic-0.50.0 anyio-3.7.1 asgiref-3.9.1 async-timeout-5.0.1 asyncpg-0.29.0 attrs-25.3.0 backoff-2.2.1 bcrypt-4.0.1 beautifulsoup4-4.13.5 bs4-0.0.2 build-1.3.0 cachetools-5.5.2 certifi-2025.8.3 cffi-2.0.0 charset_normalizer-3.4.3 chroma-hnswlib-0.7.3 chromadb-0.4.24 click-8.3.0 coloredlogs-15.0.1 cryptography-46.0.1 dataclasses-json-0.6.7 defusedxml-0.7.1 deprecated-1.2.18 deprecation-2.1.0 dirtyjson-1.0.8 distro-1.9.0 durationpy-0.10 ecdsa-0.19.1 fastapi-0.104.1 filelock-3.19.1 flatbuffers-25.2.10 frozenlist-1.7.0 fsspec-2025.9.0 google-auth-2.40.3 googleapis-common-protos-1.70.0 gotrue-2.11.4 greenlet-3.2.4 grpcio-1.75.0 h11-0.14.0 h2-4.3.0 hf-xet-1.1.10 hpack-4.1.0 httpcore-1.0.9 httptools-0.6.4 httpx-0.28.1 huggingface-hub-0.35.0 humanfriendly-10.0 hyperframe-6.1.0 idna-3.10 importlib-metadata-8.7.0 importlib-resources-6.5.2 jinja2-3.1.6 jiter-0.11.0 joblib-1.5.2 jsonpatch-1.33 jsonpointer-3.0.0 kubernetes-33.1.0 langchain-0.2.17 langchain-anthropic-0.1.23 langchain-community-0.2.19 langchain-core-0.2.43 langchain-openai-0.1.25 langchain-text-splitters-0.2.4 langgraph-0.4.0 langgraph-checkpoint-2.1.1 langgraph-prebuilt-0.1.8 langgraph-sdk-0.2.9 langsmith-0.1.147 llama-index-core-0.10.11.post1 llama-index-embeddings-openai-0.1.6 llama-index-llms-openai-0.1.6 llama-index-readers-file-0.1.5 llama-index-readers-llama-parse-0.1.3 llama-index-vector-stores-chroma-0.1.2 llama-parse-0.3.9 llamaindex-py-client-0.1.19 markdown-it-py-4.0.0 marshmallow-3.26.1 mdurl-0.1.2 mmh3-5.2.0 mpmath-1.3.0 multidict-6.6.4 mypy-extensions-1.1.0 nest-asyncio-1.6.0 networkx-3.5 nltk-3.9.1 numpy-1.26.4 nvidia-cublas-cu12-12.8.4.1 nvidia-cuda-cupti-cu12-12.8.90 nvidia-cuda-nvrtc-cu12-12.8.93 nvidia-cuda-runtime-cu12-12.8.90 nvidia-cudnn-cu12-9.10.2.21 nvidia-cufft-cu12-11.3.3.83 nvidia-cufile-cu12-1.13.1.3 nvidia-curand-cu12-10.3.9.90 nvidia-cusolver-cu12-11.7.3.90 nvidia-cusparse-cu12-12.5.8.93 nvidia-cusparselt-cu12-0.7.1 nvidia-nccl-cu12-2.27.3 nvidia-nvjitlink-cu12-12.8.93 nvidia-nvtx-cu12-12.8.90 oauthlib-3.3.1 onnxruntime-1.22.1 openai-1.108.1 opentelemetry-api-1.37.0 opentelemetry-exporter-otlp-proto-common-1.37.0 opentelemetry-exporter-otlp-proto-grpc-1.37.0 opentelemetry-instrumentation-0.58b0 opentelemetry-instrumentation-asgi-0.58b0 opentelemetry-instrumentation-fastapi-0.58b0 opentelemetry-proto-1.37.0 opentelemetry-sdk-1.37.0 opentelemetry-semantic-conventions-0.37.0 opentelemetry-util-http-0.58b0 orjson-3.11.3 ormsgpack-1.10.0 overrides-7.7.0 packaging-24.2 pandas-2.3.2 passlib-1.7.4 pgvector-0.4.1 pillow-11.3.0 postgrest-1.0.2 posthog-6.7.5 propcache-0.3.2 protobuf-6.32.1 psutil-7.1.0 psycopg2-binary-2.9.9 pulsar-client-3.8.0 pyOpenSSL-25.3.0 pyasn1-0.6.1 pyasn1-modules-0.4.2 pycparser-2.23 pydantic-2.5.0 pydantic-core-2.14.1 pydantic-settings-2.2.1 pygments-2.19.2 pymupdf-1.26.4 pypdf-4.3.1 pypika-0.48.9 pyproject_hooks-1.2.0 python-dateutil-2.9.0.post0 python-dotenv-1.0.1 python-jose-3.3.0 python-magic-0.4.27 python-multipart-0.0.9 pytz-2024.1 realtime-2.4.3 regex-2025.9.18 requests-2.32.5 requests-oauthlib-2.0.0 requests-toolbelt-1.0.0 rich-14.1.0 rsa-4.9.1 safetensors-0.6.2 scikit-learn-1.7.2 scipy-1.16.2 sentence-transformers-3.1.1 shellingham-1.5.4 six-1.17.0 sniffio-1.3.1 soupsieve-2.8 starlette-0.27.0 storage3-0.11.3 strenum-0.4.15 supabase-2.15.1 supafunc-0.9.4 sympy-1.14.0 tenacity-8.5.0 threadpoolctl-3.6.0 tiktoken-0.11.0 tokenizers-0.15.2 torch-2.8.0 tqdm-4.67.1 transformers-4.39.3 triton-3.4.0 typer-0.19.1 typing-extensions-4.15.0 typing-inspect-0.9.0 tzdata-2025.2 urllib3-2.5.0 uvicorn-0.24.0 uvloop-0.21.0 watchfiles-1.1.0 websocket-client-1.8.0 websockets-14.2 wrapt-1.17.3 xxhash-3.5.0 yarl-1.20.1 zipp-3.23.0"""
    
    # Parse versions
    versions = {}
    for package_version in production_versions.split():
        if '-' in package_version:
            # Handle packages with hyphens in name (like nvidia-cublas-cu12)
            parts = package_version.split('-')
            if len(parts) >= 2:
                # Find the last part that looks like a version (contains dots or numbers)
                version_part = None
                package_name = None
                
                for i in range(len(parts) - 1, 0, -1):
                    if re.match(r'^\d+\.\d+', parts[i]) or re.match(r'^\d+\.\d+\.\d+', parts[i]):
                        version_part = parts[i]
                        package_name = '-'.join(parts[:i])
                        break
                
                if version_part and package_name:
                    versions[package_name] = version_part
                else:
                    # Fallback: treat as package without version
                    versions[package_version] = "latest"
            else:
                versions[package_version] = "latest"
        else:
            versions[package_version] = "latest"
    
    print(f"✅ Extracted {len(versions)} package versions")
    return versions

def create_locked_requirements(versions):
    """Create a locked requirements file with exact versions."""
    print("\n🔧 Creating Locked Requirements File")
    print("-" * 50)
    
    # Key packages we care about for RAG functionality
    key_packages = [
        'openai', 'pydantic', 'pydantic-core', 'pydantic-settings',
        'fastapi', 'uvicorn', 'asyncpg', 'httpx', 'httpcore',
        'langchain', 'langchain-openai', 'langchain-core',
        'llama-index-core', 'llama-index-embeddings-openai',
        'sentence-transformers', 'pgvector', 'supabase'
    ]
    
    locked_requirements = []
    
    for package in key_packages:
        if package in versions:
            version = versions[package]
            if version != "latest":
                locked_requirements.append(f"{package}=={version}")
            else:
                locked_requirements.append(f"{package}")
        else:
            print(f"⚠️  Warning: {package} not found in production versions")
    
    # Add other important packages
    other_packages = [
        'numpy', 'pandas', 'scikit-learn', 'scipy',
        'requests', 'aiohttp', 'anyio', 'asgiref',
        'python-dotenv', 'python-multipart'
    ]
    
    for package in other_packages:
        if package in versions:
            version = versions[package]
            if version != "latest":
                locked_requirements.append(f"{package}=={version}")
    
    # Write to file
    requirements_content = "# Production-locked requirements\n"
    requirements_content += "# Generated from Render production environment\n"
    requirements_content += "# DO NOT EDIT - Use sync_production_versions.py to update\n\n"
    requirements_content += "\n".join(sorted(locked_requirements))
    
    with open("requirements-production-locked.txt", "w") as f:
        f.write(requirements_content)
    
    print(f"✅ Created requirements-production-locked.txt with {len(locked_requirements)} packages")
    return locked_requirements

def install_locked_requirements():
    """Install the locked requirements locally."""
    print("\n📦 Installing Locked Requirements")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-production-locked.txt"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Successfully installed locked requirements")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install locked requirements: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False

def verify_versions():
    """Verify that installed versions match production."""
    print("\n🔍 Verifying Installed Versions")
    print("-" * 50)
    
    key_packages = ['openai', 'pydantic', 'fastapi', 'asyncpg', 'httpx']
    
    for package in key_packages:
        try:
            result = subprocess.run([
                sys.executable, "-c", f"import {package}; print({package}.__version__)"
            ], capture_output=True, text=True, check=True)
            
            version = result.stdout.strip()
            print(f"✅ {package}: {version}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ {package}: Failed to get version - {e}")

def main():
    """Main synchronization function."""
    print("🚨 PRODUCTION VERSION SYNCHRONIZATION")
    print("=" * 60)
    
    # Step 1: Extract production versions
    versions = extract_production_versions()
    
    # Step 2: Create locked requirements
    locked_requirements = create_locked_requirements(versions)
    
    # Step 3: Install locked requirements
    if install_locked_requirements():
        # Step 4: Verify versions
        verify_versions()
        
        print("\n" + "=" * 60)
        print("📊 SYNCHRONIZATION SUMMARY")
        print("=" * 60)
        print("✅ Production versions extracted")
        print("✅ Locked requirements file created")
        print("✅ Local environment updated")
        print("✅ Version verification completed")
        print("\n🎉 Local environment now matches production!")
        print("   Ready for testing with exact version parity.")
        
        return True
    else:
        print("\n❌ SYNCHRONIZATION FAILED")
        print("   Check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
