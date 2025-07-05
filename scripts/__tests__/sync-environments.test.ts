import { promises as fs } from 'fs';
import path from 'path';
import { syncEnvironments } from '../sync-environments';

jest.mock('fs', () => ({
  promises: {
    readFile: jest.fn(),
    writeFile: jest.fn(),
    access: jest.fn()
  }
}));

describe('Environment Sync Script', () => {
  const mockEnvContent = `
ENV_LEVEL=test
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=mock.jwt.key
TEST_USER_ID=00000000-0000-4000-a000-000000000000
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=test-password
  `.trim();

  beforeEach(() => {
    jest.clearAllMocks();
    (fs.readFile as jest.Mock).mockResolvedValue(mockEnvContent);
    (fs.access as jest.Mock).mockResolvedValue(undefined);
  });

  it('should read environment file and sync to target locations', async () => {
    await syncEnvironments('test');

    // Check if source file was read
    expect(fs.readFile).toHaveBeenCalledWith(
      expect.stringContaining('.env.test'),
      'utf8'
    );

    // Check if target files were written
    const expectedTargets = [
      'config/environment',
      'supabase/functions',
      'tests'
    ];

    expectedTargets.forEach(dir => {
      expect(fs.writeFile).toHaveBeenCalledWith(
        expect.stringContaining(path.join(dir, '.env.test')),
        mockEnvContent,
        'utf8'
      );
    });
  });

  it('should handle missing environment file', async () => {
    (fs.access as jest.Mock).mockRejectedValue(new Error('File not found'));

    await expect(syncEnvironments('missing')).rejects.toThrow(
      'Environment file .env.missing not found'
    );
  });

  it('should validate environment variables', async () => {
    const invalidEnvContent = 'INVALID_ENV=value';
    (fs.readFile as jest.Mock).mockResolvedValue(invalidEnvContent);

    await expect(syncEnvironments('test')).rejects.toThrow(
      'Required environment variables missing'
    );
  });
}); 