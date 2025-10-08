# FM-027 Reproduction Harness
.PHONY: repro-fm027 clean-fm027

# Environment variables for FM-027 reproduction
# These should be set in your environment or .env file
export SUPABASE_URL := $(or $(SUPABASE_URL),https://your-staging-project.supabase.co)
export ANON_KEY := $(or $(SUPABASE_ANON_KEY),$(ANON_KEY))
export SUPABASE_SERVICE_ROLE_KEY := $(or $(SUPABASE_SERVICE_ROLE_KEY),$(SERVICE_ROLE_KEY))

# FM-027 reproduction target
repro-fm027:
	@echo "🚀 Running FM-027 reproduction harness..."
	@echo "Environment: Staging Supabase"
	@echo "Date: $(shell date -u +%Y-%m-%dT%H:%M:%SZ)"
	@echo ""
	@echo "1️⃣ Validating StorageManager fix..."
	@python test_storage_manager_debug.py
	@echo ""
	@echo "2️⃣ Testing complete flow simulation..."
	@python test_complete_flow_simulation.py
	@echo ""
	@echo "3️⃣ Checking actual file access..."
	@python test_actual_file_access.py
	@echo ""
	@echo "4️⃣ Listing storage files..."
	@python test_list_storage_files.py
	@echo ""
	@echo "✅ FM-027 reproduction complete"
	@echo "📊 Results saved to artifacts/fm_027/$(shell date +%Y%m%d_%H%M%S)/"

# Clean FM-027 artifacts
clean-fm027:
	@echo "🧹 Cleaning FM-027 artifacts..."
	@rm -rf artifacts/fm_027/
	@rm -f storage_files_list_*.json
	@rm -f storage_manager_test_*.json
	@echo "✅ Cleanup complete"

# Help target
help:
	@echo "Available targets:"
	@echo "  repro-fm027    - Run FM-027 reproduction harness"
	@echo "  clean-fm027    - Clean FM-027 artifacts"
	@echo "  help          - Show this help message"

