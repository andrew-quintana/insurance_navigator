/**
 * Shared date formatting utilities for edge functions
 */

/**
 * Formats a date to YYYYMMDDHHMMSS format
 */
function formatDateToYYYYMMDDHHMMSS(date: Date): string {
  return date.getUTCFullYear().toString() +
    (date.getUTCMonth() + 1).toString().padStart(2, '0') +
    date.getUTCDate().toString().padStart(2, '0') +
    date.getUTCHours().toString().padStart(2, '0') +
    date.getUTCMinutes().toString().padStart(2, '0') +
    date.getUTCSeconds().toString().padStart(2, '0');
}

/**
 * Formats a date to YYYYMMDDHHMMSS±HHMM format
 * Used for consistent file naming across the pipeline
 */
export function formatDateToYYYYMMDDHHMMSS_TZ(date: Date): string {
  const timestamp = formatDateToYYYYMMDDHHMMSS(date);
  // Always use UTC (+0000) for consistency in edge functions
  return `${timestamp}+0000`;
}

/**
 * Generates a consistent filename format for pipeline stages
 * Format: {timestamp}-{filename}
 * @param uploadedAt - ISO string or Date object representing the upload time
 * @param originalFilename - Original filename to append to timestamp
 * @returns Formatted filename with timestamp prefix
 */
export function getPipelineFilename(uploadedAt: string | Date, originalFilename: string): string {
  const date = typeof uploadedAt === 'string' ? new Date(uploadedAt) : uploadedAt;
  const timestamp = formatDateToYYYYMMDDHHMMSS_TZ(date);
  return `${timestamp}-${originalFilename}`;
} 