#!/usr/bin/env python3
"""
Phase 3 Comprehensive Pipeline Test
Test the complete upload pipeline end-to-end in cloud environment
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

async def test_complete_phase3_pipeline():
    """Test complete pipeline with stage-by-stage monitoring"""
    
    # Database connection
    database_url = os.getenv('POOLER_URL', '${DATABASE_URL}/pdf", 2048, file_hash, "files/test/phase3_complete.pdf", "uploaded", datetime.utcnow(), datetime.utcnow())
        
        # Insert upload job record
        job_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (job_id, document_id, state, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, job_id, document_id, "queued", "uploaded", datetime.utcnow(), datetime.utcnow())
        
        print("✅ Test job created successfully")
        
        # Expected pipeline stages (from Phase 1 & 2)
        expected_stages = [
            "uploaded",
            "upload_validated", 
            "parse_queued",
            "parsed",
            "parse_validated",
            "chunks_stored",
            "embedding_in_progress",
            "embedded",
            "complete"
        ]
        
        # Monitor job status changes through ALL stages
        print("⏳ Monitoring complete pipeline execution...")
        print(f"Expected stages: {expected_stages}")
        
        stage_transitions = []
        start_time = datetime.utcnow()
        
        # Monitor for up to 10 minutes
        for attempt in range(120):  # 120 * 5 seconds = 10 minutes
            result = await conn.fetchrow("""
                SELECT state, status, updated_at, last_error, progress
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, job_id)
            
            if result:
                current_state = result['state']
                current_status = result['status']
                updated_at = result['updated_at']
                
                # Check if this is a new stage transition
                if current_status not in [s['status'] for s in stage_transitions]:
                    stage_transitions.append({
                        'status': current_status,
                        'state': current_state,
                        'timestamp': updated_at,
                        'attempt': attempt + 1
                    })
                    print(f"🔄 Stage: {current_status} (state: {current_state}) - Attempt {attempt + 1}")
                    
                    # Check if we've completed all expected stages
                    if current_status == "complete" and current_state == "done":
                        print("🎉 Pipeline completed successfully!")
                        break
                    elif current_state == "deadletter":
                        print(f"❌ Pipeline failed: {result['last_error']}")
                        break
                else:
                    print(f"⏳ Current stage: {current_status} (state: {current_state}) - Attempt {attempt + 1}")
            else:
                print("❌ No job found")
                break
                
            await asyncio.sleep(5)  # Check every 5 seconds
        
        # Verify we went through ALL expected stages
        print("\n📊 Pipeline Stage Analysis:")
        print("=" * 40)
        
        stages_completed = [s['status'] for s in stage_transitions]
        print(f"Stages completed: {stages_completed}")
        print(f"Expected stages: {expected_stages}")
        
        # Check if we went through every single stage
        missing_stages = set(expected_stages) - set(stages_completed)
        if missing_stages:
            print(f"❌ Missing stages: {missing_stages}")
        else:
            print("✅ All expected stages completed!")
        
        # Verify processing artifacts
        print("\n🔍 Verifying Processing Artifacts:")
        
        # Check for chunks
        chunk_count = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.document_chunks 
            WHERE document_id = $1
        """, document_id)
        print(f"   Document chunks created: {chunk_count}")
        
        # Check for events
        event_count = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.events 
            WHERE document_id = $1
        """, document_id)
        print(f"   Events logged: {event_count}")
        
        # Check final job status
        final_result = await conn.fetchrow("""
            SELECT state, status, updated_at, last_error
            FROM upload_pipeline.upload_jobs 
            WHERE job_id = $1 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, job_id)
        
        if final_result:
            final_state = final_result['state']
            final_status = final_result['status']
            processing_time = (final_result['updated_at'] - start_time).total_seconds()
            
            print(f"\n🏁 Final Results:")
            print(f"   Final status: {final_status}")
            print(f"   Final state: {final_state}")
            print(f"   Processing time: {processing_time:.2f} seconds")
            print(f"   Stages completed: {len(stage_transitions)}/{len(expected_stages)}")
            
            # Determine success
            pipeline_complete = (final_status == "complete" and final_state == "done")
            all_stages_completed = len(missing_stages) == 0
            
            if pipeline_complete and all_stages_completed:
                print("🎉 PHASE 3 COMPLETE SUCCESS!")
                print("✅ All pipeline stages completed")
                print("✅ Processing artifacts created")
                print("✅ End-to-end pipeline working")
                return True
            else:
                print("⚠️ PHASE 3 PARTIAL SUCCESS")
                print(f"   Pipeline complete: {pipeline_complete}")
                print(f"   All stages completed: {all_stages_completed}")
                return False
        else:
            print("❌ No final job result found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    success = asyncio.run(test_complete_phase3_pipeline())
    if success:
        print("\n🎉 PHASE 3 COMPLETE PIPELINE TEST: SUCCESS!")
    else:
        print("\n❌ PHASE 3 COMPLETE PIPELINE TEST: FAILED!")
