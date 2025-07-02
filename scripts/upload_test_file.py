"""Script to upload test file to storage bucket."""
import os
from db.services.db_pool import get_db_pool

def main():
    """Upload test file to storage bucket."""
    # Get Supabase client
    db = get_db_pool()
    if not db:
        print("Failed to connect to Supabase")
        return
    
    # Upload test file
    with open('tests/data/test.pdf', 'rb') as f:
        response = db.storage.from_('documents').upload(
            'test.pdf',
            f,
            file_options={
                'content-type': 'application/pdf',
                'x-upsert': 'true'
            }
        )
        print(f"Uploaded test file: {response}")

if __name__ == '__main__':
    main() 