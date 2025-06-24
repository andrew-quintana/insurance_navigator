@app.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get document processing status."""
    try:
        # Get services
        services = await get_services()
        
        # Get document record
        pool = await get_db_pool()
        async with pool.get_connection() as conn:
            doc = await conn.fetchrow("""
                SELECT * FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
            
            if not doc:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Get latest job status
            latest_job = await conn.fetchrow("""
                SELECT * FROM processing_jobs
                WHERE payload->>'document_id' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, document_id)
        
            # Combine status information
            return {
                "document_id": str(doc["id"]),
                "filename": doc["original_filename"],
                "status": doc["status"],
                "progress_percentage": doc["progress_percentage"],
                "created_at": doc["created_at"].isoformat(),
                "updated_at": doc["updated_at"].isoformat(),
                "job_status": latest_job["status"] if latest_job else None,
                "job_error": latest_job["error"] if latest_job else None,
                "processing_complete": doc["status"] in ["completed", "ready"]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        ) 