#!/bin/bash
# Upload Test Runner with Timeouts
# Prevents hanging in terminal interface

set -e

echo "🚀 Starting Upload Test with Timeouts"
echo "======================================"

# Timeout configuration (in seconds)
API_TIMEOUT=30      # API calls should complete in 5-10s, timeout at 30s
UPLOAD_TIMEOUT=120  # File uploads should complete in 30-60s, timeout at 120s
TOTAL_TIMEOUT=300   # Total test should complete in 2-3 minutes, timeout at 5 minutes

echo "⏱️  Timeouts: API=${API_TIMEOUT}s, Upload=${UPLOAD_TIMEOUT}s, Total=${TOTAL_TIMEOUT}s"

# Function to run with timeout
run_with_timeout() {
    local timeout=$1
    local command="$2"
    
    echo "⏰ Running: $command (timeout: ${timeout}s)"
    
    # Use perl for timeout on macOS
    perl -e '
        use POSIX;
        my $timeout = shift;
        my $command = shift;
        
        my $pid = fork();
        if ($pid == 0) {
            # Child process
            exec(@ARGV);
            exit(1);
        } else {
            # Parent process
            my $start = time();
            while (1) {
                my $kid = waitpid($pid, WNOHANG);
                if ($kid == $pid) {
                    my $exit_code = $? >> 8;
                    exit($exit_code);
                }
                
                if (time() - $start > $timeout) {
                    print "⏰ Timeout after ${timeout}s, killing process\n";
                    kill(9, $pid);
                    waitpid($pid, 0);
                    exit(124);  # Timeout exit code
                }
                
                sleep(1);
            }
        }
    ' "$timeout" "$command"
}

# Check if test files exist
if [ ! -f "./examples/simulated_insurance_document.pdf" ]; then
    echo "❌ Error: simulated_insurance_document.pdf not found"
    exit 1
fi

if [ ! -f "./examples/scan_classic_hmo_parsed.pdf" ]; then
    echo "❌ Error: scan_classic_hmo_parsed.pdf not found"
    exit 1
fi

echo "✅ Test files found"

# Run the Python script with total timeout
echo "🐍 Running Python upload test script..."
run_with_timeout "$TOTAL_TIMEOUT" "python scripts/testing/complete_upload_test.py"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ Test timed out after ${TOTAL_TIMEOUT}s"
    exit 1
elif [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Upload test completed successfully"
    exit 0
else
    echo "❌ Upload test failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi
