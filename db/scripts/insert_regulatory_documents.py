import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from datetime import date, datetime
import json

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'insurance_navigator')
}

documents = [
    {
        'original_filename': 'Social Security Act (Title XVIII)',
        'storage_path': 'https://www.ssa.gov/OP_Home/ssact/title18/1800.htm',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': date(1965, 7, 30),
        'expiration_date': None,
        'source_url': 'https://www.ssa.gov/OP_Home/ssact/title18/1800.htm',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 5000,
            'extraction_method': 'web_scraper',
            'summary': 'The foundational law for the Medicare program.'
        },
        'tags': ['statute', 'coverage', 'compliance'],
        'status': 'completed'
    },
    {
        'original_filename': 'Code of Federal Regulations (CFR), Title 42',
        'storage_path': 'https://www.ecfr.gov/current/title-42',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.ecfr.gov/current/title-42',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Federal rules for Medicare administration.'
        },
        'tags': ['regulation', 'compliance'],
        'status': 'completed'
    },
    {
        'original_filename': 'CMS National Coverage Determinations (NCDs)',
        'storage_path': 'https://www.cms.gov/medicare-coverage-database/',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/medicare-coverage-database/',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 7500,
            'extraction_method': 'web_scraper',
            'summary': 'National policies specifying Medicare coverage for items and services.'
        },
        'tags': ['coverage', 'policy'],
        'status': 'completed'
    },
    {
        'original_filename': 'Local Coverage Determinations (LCDs)',
        'storage_path': 'https://www.cms.gov/medicare-coverage-database/',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/medicare-coverage-database/',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 5000,
            'extraction_method': 'web_scraper',
            'summary': 'Regional policies by Medicare Administrative Contractors for services not covered by NCDs.'
        },
        'tags': ['coverage', 'policy', 'local'],
        'status': 'completed'
    },
    {
        'original_filename': 'Billing & Coding Articles (e.g., A55426)',
        'storage_path': 'https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleid=55426',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleid=55426',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 3000,
            'extraction_method': 'web_scraper',
            'summary': 'Articles providing coding, billing, and documentation guidance for claims.'
        },
        'tags': ['billing', 'coding', 'documentation'],
        'status': 'completed'
    },
    {
        'original_filename': 'Medicare Claims Processing Manual',
        'storage_path': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/clm104c01.pdf',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/clm104c01.pdf',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Detailed instructions for processing Medicare claims.'
        },
        'tags': ['manual', 'claims', 'processing'],
        'status': 'completed'
    },
    {
        'original_filename': 'Medicare Benefit Policy Manual',
        'storage_path': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/bp102c01.pdf',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/bp102c01.pdf',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Policy guidance on Medicare benefits.'
        },
        'tags': ['manual', 'benefits', 'policy'],
        'status': 'completed'
    },
    {
        'original_filename': 'Medicare Program Integrity Manual',
        'storage_path': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/pim83c01.pdf',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/pim83c01.pdf',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Instructions for ensuring program integrity and preventing fraud.'
        },
        'tags': ['manual', 'integrity', 'fraud'],
        'status': 'completed'
    },
    {
        'original_filename': 'Change Requests (CRs) & Transmittals',
        'storage_path': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Transmittals',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Transmittals',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Official CMS communications on policy and system changes.'
        },
        'tags': ['guidance', 'policy', 'transmittal'],
        'status': 'completed'
    },
    {
        'original_filename': 'Medicare Physician Fee Schedule',
        'storage_path': 'https://www.cms.gov/medicare/physician-fee-schedule/search',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/medicare/physician-fee-schedule/search',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Reimbursement rates and payment rules for physicians.'
        },
        'tags': ['fee_schedule', 'payment', 'reimbursement'],
        'status': 'completed'
    },
    {
        'original_filename': 'DMEPOS Fee Schedule',
        'storage_path': 'https://www.cms.gov/medicaremedicare-fee-service-paymentdmeposfeescheddmepos-fee-schedule',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/medicaremedicare-fee-service-paymentdmeposfeescheddmepos-fee-schedule',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Reimbursement rates for durable medical equipment, prosthetics, orthotics, and supplies.'
        },
        'tags': ['fee_schedule', 'DMEPOS', 'payment'],
        'status': 'completed'
    },
    {
        'original_filename': 'Self-Administered Drug (SAD) Exclusion Lists',
        'storage_path': 'https://www.cms.gov/medicare-coverage-database/reports/sad-exclusion-list-report.aspx',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/medicare-coverage-database/reports/sad-exclusion-list-report.aspx',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'List of drugs excluded from coverage because they are usually self-administered.'
        },
        'tags': ['exclusion_list', 'drugs', 'coverage'],
        'status': 'completed'
    },
    {
        'original_filename': 'CMS Regulations & Guidance Portal',
        'storage_path': 'https://www.cms.gov/marketplace/resources/regulations-guidance',
        'document_type': 'regulatory',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'effective_date': None,
        'expiration_date': None,
        'source_url': 'https://www.cms.gov/marketplace/resources/regulations-guidance',
        'source_last_checked': datetime.now(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'regulatory_processor',
            'content_length': 10000,
            'extraction_method': 'web_scraper',
            'summary': 'Central resource for CMS regulations, manuals, transmittals, and guidance.'
        },
        'tags': ['portal', 'regulations', 'guidance'],
        'status': 'completed'
    }
]

INSERT_SQL = '''
INSERT INTO documents (
    original_filename, storage_path, document_type, jurisdiction, program,
    effective_date, expiration_date, source_url, source_last_checked,
    priority_score, metadata, tags, status, created_at, updated_at
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
) RETURNING id, original_filename;
'''

async def insert_documents():
    """Insert test regulatory documents into the database."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        
        print("🔄 Inserting regulatory documents...")
        
        for doc in documents:
            result = await conn.fetchrow(
                INSERT_SQL,
                doc['original_filename'],
                doc['storage_path'],
                doc['document_type'],
                doc['jurisdiction'],
                doc['program'],
                doc['effective_date'],
                doc['expiration_date'],
                doc['source_url'],
                doc['source_last_checked'],
                doc['priority_score'],
                json.dumps(doc['metadata']),
                doc['tags'],
                doc['status'],
                datetime.now(),
                datetime.now()
            )
            
            print(f"✅ Inserted document {result['id']}: {result['original_filename']}")
        
        print("\n✨ All documents inserted successfully!")
        
    except Exception as e:
        print(f"❌ Error inserting documents: {str(e)}")
        raise
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(insert_documents()) 