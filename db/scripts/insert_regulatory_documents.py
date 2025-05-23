import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from datetime import date
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
        # RCA: raw_document_path is required (NOT NULL) by the schema, but no real path is available for these regulatory documents.
        # To comply, we use an empty string as a placeholder. This avoids NOT NULL violations and is a common practice for required fields with no data.
        'raw_document_path': '',
        'title': 'Social Security Act (Title XVIII)',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'statute',
        'effective_date': date(1965, 7, 30),
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'The foundational law for the Medicare program.'},
        'source_url': 'https://www.ssa.gov/OP_Home/ssact/title18/1800.htm',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['statute', 'coverage', 'compliance'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Code of Federal Regulations (CFR), Title 42',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'regulation',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Federal rules for Medicare administration.'},
        'source_url': 'https://www.ecfr.gov/current/title-42',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['regulation', 'compliance'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'CMS National Coverage Determinations (NCDs)',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'policy',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'National policies specifying Medicare coverage for items and services.'},
        'source_url': 'https://www.cms.gov/medicare-coverage-database/',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['coverage', 'policy'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Local Coverage Determinations (LCDs)',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'policy',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Regional policies by Medicare Administrative Contractors for services not covered by NCDs.'},
        'source_url': 'https://www.cms.gov/medicare-coverage-database/',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['coverage', 'policy', 'local'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Billing & Coding Articles (e.g., A55426)',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'guidance',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Articles providing coding, billing, and documentation guidance for claims.'},
        'source_url': 'https://www.cms.gov/medicare-coverage-database/view/article.aspx?articleid=55426',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['billing', 'coding', 'documentation'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Medicare Claims Processing Manual',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'manual',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Detailed instructions for processing Medicare claims.'},
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/clm104c01.pdf',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['manual', 'claims', 'processing'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Medicare Benefit Policy Manual',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'manual',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Policy guidance on Medicare benefits.'},
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/bp102c01.pdf',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['manual', 'benefits', 'policy'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Medicare Program Integrity Manual',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'manual',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Instructions for ensuring program integrity and preventing fraud.'},
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/pim83c01.pdf',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['manual', 'integrity', 'fraud'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Change Requests (CRs) & Transmittals',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'guidance',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Official CMS communications on policy and system changes.'},
        'source_url': 'https://www.cms.gov/Regulations-and-Guidance/Guidance/Transmittals',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['guidance', 'policy', 'transmittal'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Medicare Physician Fee Schedule',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'fee_schedule',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Reimbursement rates and payment rules for physicians.'},
        'source_url': 'https://www.cms.gov/medicare/physician-fee-schedule/search',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['fee_schedule', 'payment', 'reimbursement'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'DMEPOS Fee Schedule',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'fee_schedule',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Reimbursement rates for durable medical equipment, prosthetics, orthotics, and supplies.'},
        'source_url': 'https://www.cms.gov/medicaremedicare-fee-service-paymentdmeposfeescheddmepos-fee-schedule',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['fee_schedule', 'DMEPOS', 'payment'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'Self-Administered Drug (SAD) Exclusion Lists',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'exclusion_list',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'List of drugs excluded from coverage because they are usually self-administered.'},
        'source_url': 'https://www.cms.gov/medicare-coverage-database/reports/sad-exclusion-list-report.aspx',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['exclusion_list', 'drugs', 'coverage'],
        'version': 1
    },
    {
        'raw_document_path': '',
        'title': 'CMS Regulations & Guidance Portal',
        'jurisdiction': 'federal',
        'program': ['Medicare'],
        'document_type': 'portal',
        'effective_date': None,
        'expiration_date': None,
        'structured_contents': None,
        'summary': {'text': 'Central resource for CMS regulations, manuals, transmittals, and guidance.'},
        'source_url': 'https://www.cms.gov/marketplace/resources/regulations-guidance',
        'encrypted_restrictions': None,
        'encryption_key_id': None,
        'tags': ['portal', 'regulations', 'guidance'],
        'version': 1
    }
]

INSERT_SQL = '''
INSERT INTO regulatory_documents (
    raw_document_path, title, jurisdiction, program, document_type, effective_date, expiration_date,
    structured_contents, summary, source_url, encrypted_restrictions, encryption_key_id, tags, version
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
) RETURNING document_id, title;
'''

async def insert_documents():
    conn = await asyncpg.connect(**DB_CONFIG)
    for idx, doc in enumerate(documents, 1):
        values = [
            doc['raw_document_path'],
            doc['title'],
            doc['jurisdiction'],
            doc['program'],
            doc['document_type'],
            doc['effective_date'],
            doc['expiration_date'],
            json.dumps(doc['structured_contents']) if doc['structured_contents'] is not None else None,
            json.dumps(doc['summary']) if doc['summary'] is not None else None,
            doc['source_url'],
            json.dumps(doc['encrypted_restrictions']) if doc['encrypted_restrictions'] is not None else None,
            doc['encryption_key_id'],
            doc['tags'],
            doc['version']
        ]
        result = await conn.fetchrow(INSERT_SQL, *values)
        print(f"[{idx}/{len(documents)}] Inserted: {result['title']} (ID: {result['document_id']})", flush=True)
    await conn.close()

if __name__ == '__main__':
    asyncio.run(insert_documents()) 