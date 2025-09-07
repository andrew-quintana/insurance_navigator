#!/usr/bin/env python3
"""
Frontend Upload Monitor - Test script to monitor uploads after frontend UI testing.
This script will monitor the database for new uploads and track their processing status.
"""

import asyncio
import asyncpg
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

class FrontendUploadMonitor:
    def __init__(self):
        self.conn = None
        self.monitoring = False
        self.initial_jobs = set()
        
    async def connect(self):
        """Connect to production database."""
        self.conn = await asyncpg.connect(
            'postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require',
            statement_cache_size=0
        )
        print("✅ Connected to production database")
        
    async def disconnect(self):
        """Disconnect from database."""
        if self.conn:
            await self.conn.close()
            print("✅ Disconnected from database")
            
    async def get_initial_state(self):
        """Get initial state of upload jobs to detect new ones."""
        result = await self.conn.fetch('''
            SELECT uj.job_id, uj.document_id, uj.status, uj.created_at, d.filename
            FROM upload_pipeline.upload_jobs uj
            JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
            ORDER BY uj.created_at DESC
        ''')
        
        self.initial_jobs = {row['job_id'] for row in result}
        print(f"📊 Initial state: {len(self.initial_jobs)} existing jobs")
        
        if result:
            print("📋 Recent jobs:")
            for row in result[:5]:  # Show last 5 jobs
                print(f"  - {str(row['job_id'])[:8]}...: {row['filename']} ({row['status']})")
        
    async def check_new_uploads(self):
        """Check for new upload jobs since monitoring started."""
        result = await self.conn.fetch('''
            SELECT uj.job_id, uj.document_id, uj.status, uj.created_at, d.filename, d.bytes_len
            FROM upload_pipeline.upload_jobs uj
            JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
            WHERE uj.job_id NOT IN (SELECT unnest($1::uuid[]))
            ORDER BY uj.created_at DESC
        ''', list(self.initial_jobs))
        
        return result
        
    async def monitor_job_progress(self, job_id, filename):
        """Monitor a specific job's progress through the pipeline."""
        print(f"\n🔍 Monitoring job: {job_id[:8]}... ({filename})")
        
        stages = ['uploaded', 'parse_queued', 'parsed', 'parse_validated', 'chunks_stored', 'embeddings_stored', 'complete', 'duplicate']
        last_stage = None
        start_time = time.time()
        
        while self.monitoring:
            try:
                # Get current job status
                result = await self.conn.fetchrow('''
                    SELECT status, state, updated_at, error_message
                    FROM upload_pipeline.upload_jobs
                    WHERE job_id = $1
                ''', job_id)
                
                if not result:
                    print(f"❌ Job {job_id[:8]}... not found")
                    break
                    
                current_stage = result['status']
                current_state = result['state']
                updated_at = result['updated_at']
                error_message = result['error_message']
                
                # Check if stage changed
                if current_stage != last_stage:
                    elapsed = time.time() - start_time
                    print(f"🔄 Stage: {current_stage} (state: {current_state}) - {elapsed:.1f}s")
                    last_stage = current_stage
                    
                    # Check for errors
                    if error_message:
                        print(f"❌ Error: {error_message}")
                        
                # Check if job is complete
                if current_state == 'done':
                    elapsed = time.time() - start_time
                    print(f"✅ Job completed: {current_stage} - Total time: {elapsed:.1f}s")
                    
                    # Get final statistics
                    chunks_result = await self.conn.fetchrow('''
                        SELECT COUNT(*) as chunk_count
                        FROM upload_pipeline.document_chunks
                        WHERE document_id = (
                            SELECT document_id FROM upload_pipeline.upload_jobs
                            WHERE job_id = $1
                        )
                    ''', job_id)
                    
                    if chunks_result:
                        print(f"📊 Document chunks created: {chunks_result['chunk_count']}")
                    
                    break
                    
                # Check for timeout (5 minutes)
                if time.time() - start_time > 300:
                    print(f"⏰ Job timeout after 5 minutes - Current stage: {current_stage}")
                    break
                    
            except Exception as e:
                print(f"❌ Error monitoring job: {e}")
                break
                
            await asyncio.sleep(2)  # Check every 2 seconds
            
    async def start_monitoring(self):
        """Start monitoring for new uploads."""
        print("🚀 Starting Frontend Upload Monitor")
        print("=" * 50)
        print("📝 Instructions:")
        print("1. Go to your Vercel frontend UI")
        print("2. Upload a document (scan_classic_hmo.pdf or simulated_insurance_document.pdf)")
        print("3. Watch this monitor for real-time processing updates")
        print("4. Press Ctrl+C to stop monitoring")
        print("=" * 50)
        
        await self.connect()
        await self.get_initial_state()
        
        self.monitoring = True
        print(f"\n⏳ Monitoring for new uploads... (Started at {datetime.now().strftime('%H:%M:%S')})")
        
        try:
            while self.monitoring:
                # Check for new uploads
                new_uploads = await self.check_new_uploads()
                
                if new_uploads:
                    print(f"\n🎉 Found {len(new_uploads)} new upload(s)!")
                    
                    for upload in new_uploads:
                        print(f"📄 New upload: {upload['filename']} ({upload['bytes_len']} bytes)")
                        print(f"   Job ID: {upload['job_id']}")
                        print(f"   Document ID: {upload['document_id']}")
                        print(f"   Status: {upload['status']}")
                        print(f"   Created: {upload['created_at']}")
                        
                        # Start monitoring this job
                        await self.monitor_job_progress(upload['job_id'], upload['filename'])
                        
                        # Update initial jobs set to avoid re-detecting
                        self.initial_jobs.add(upload['job_id'])
                
                await asyncio.sleep(3)  # Check every 3 seconds
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Error during monitoring: {e}")
        finally:
            self.monitoring = False
            await self.disconnect()

async def main():
    """Main function."""
    monitor = FrontendUploadMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
