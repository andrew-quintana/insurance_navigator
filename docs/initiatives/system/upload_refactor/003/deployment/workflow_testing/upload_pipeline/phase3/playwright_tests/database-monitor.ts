import { promises as fs } from 'fs';
import { load } from 'dotenv';

// Load environment variables
load({ path: '.env.production' });

export interface UploadJob {
  job_id: string;
  document_id: string;
  status: string;
  state: string;
  created_at: Date;
  updated_at: Date;
  error_message?: string;
}

export interface Document {
  document_id: string;
  filename: string;
  bytes_len: number;
  created_at: Date;
}

export class DatabaseMonitor {
  private apiBaseUrl: string;
  private testUserEmail: string;

  constructor(apiBaseUrl: string, testUserEmail: string) {
    this.apiBaseUrl = apiBaseUrl;
    this.testUserEmail = testUserEmail;
  }

  async getUploadJobs(): Promise<UploadJob[]> {
    try {
      // This would normally connect to the database directly
      // For now, we'll use the API to get job status
      const response = await fetch(`${this.apiBaseUrl}/api/v1/status`);
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching upload jobs:', error);
      return [];
    }
  }

  async waitForJobCompletion(jobId: string, timeoutMs: number = 120000): Promise<boolean> {
    const startTime = Date.now();
    const pollInterval = 2000; // 2 seconds

    while (Date.now() - startTime < timeoutMs) {
      try {
        const jobs = await this.getUploadJobs();
        const job = jobs.find(j => j.job_id === jobId);
        
        if (job) {
          console.log(`📊 Job ${jobId.substring(0, 8)}... status: ${job.status} (${job.state})`);
          
          if (job.state === 'done') {
            console.log(`✅ Job completed: ${job.status}`);
            return true;
          }
          
          if (job.error_message) {
            console.log(`❌ Job failed: ${job.error_message}`);
            return false;
          }
        }
        
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.error('Error monitoring job:', error);
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
    }
    
    console.log(`⏰ Job monitoring timeout after ${timeoutMs}ms`);
    return false;
  }

  async getJobStatistics(jobId: string): Promise<{ chunks: number; processingTime: number }> {
    try {
      // This would normally query the database for chunk count
      // For now, return mock data
      return {
        chunks: 2, // Mock value
        processingTime: 30 // Mock value in seconds
      };
    } catch (error) {
      console.error('Error getting job statistics:', error);
      return { chunks: 0, processingTime: 0 };
    }
  }
}
