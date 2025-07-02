# Coding Agent Rules for Environment Variable Management

## Core Agent Responsibilities

1. **Never Directly Modify .env Files**
   - NEVER attempt to directly read, write, or modify actual `.env` files
   - NEVER display or log actual environment variable values in chat
   - ALWAYS work with `.env.template` or `.env.example` for structural changes

2. **Template-First Approach**
   - When new environment variables are needed, ALWAYS update `.env.template` first
   - Use descriptive placeholder values like `YOUR_API_KEY` or `DATABASE_PASSWORD_HERE`
   - Document the purpose of each new variable in the template

## Communication Protocol

1. **Requesting Environment Variable Updates**
   ```markdown
   Please update your .env file with the following new variable:
   
   Variable: NEW_API_KEY
   Description: API key for the payment processing service
   Format: 32-character alphanumeric string
   Required: Yes
   
   I'll wait for your confirmation before proceeding.
   ```

2. **Handling Sensitive Values**
   - NEVER ask users to paste sensitive values in chat
   - ALWAYS instruct users to update their `.env` file directly
   - Use phrases like "Once you've updated the .env file, please let me know"

3. **Validation Requests**
   ```markdown
   Please confirm that you have:
   1. Added NEW_API_KEY to your .env file
   2. The value matches the required format (32-char alphanumeric)
   
   You don't need to share the actual value - just confirm it's set.
   ```

## Environment Variable Requirements

1. **Adding New Variables**
   - MUST provide clear purpose and usage
   - MUST specify if variable is required or optional
   - MUST describe expected format or constraints
   - MUST update documentation when adding variables

2. **Modifying Existing Variables**
   - MUST explain why modification is needed
   - MUST provide migration steps if format changes
   - MUST update all relevant templates and documentation

## Error Handling Protocol

1. **Missing Variables**
   ```markdown
   The operation requires the following environment variables:
   - REQUIRED_VAR_1 (missing)
   - REQUIRED_VAR_2 (missing)

   Please add these to your .env file. I can provide format requirements if needed.
   ```

2. **Invalid Values**
   ```markdown
   The value format for DATABASE_URL appears to be incorrect.
   Expected format: postgresql://user:password@host:port/dbname
   Please update the value in your .env file and let me know once done.
   ```

## Security Protocol

1. **When Secrets Are Accidentally Shared**
   ```markdown
   ⚠️ I notice you shared a sensitive value in chat. For security:
   1. Please rotate/regenerate this secret immediately
   2. Update your .env file with the new value
   3. Delete your message containing the sensitive value
   ```

2. **Preventing Exposure**
   - ALWAYS warn users if they attempt to share sensitive values
   - NEVER log or store sensitive values
   - NEVER include actual secrets in code examples

## Template Management

1. **Template Updates**
   ```markdown
   I'm updating .env.template with the new configuration:

   ```plaintext
   # Payment Processing (Required)
   PAYMENT_API_KEY=your_32char_api_key_here
   PAYMENT_SECRET=your_payment_secret_here

   # Cache Configuration (Optional)
   CACHE_TTL=3600  # Time in seconds
   ```

2. **Documentation Requirements**
   - Group related variables with comments
   - Include format examples for complex values
   - Mark required vs optional variables
   - Add descriptions for non-obvious variables

## Implementation Guidance

1. **Requesting Configuration**
   ```markdown
   To implement this feature, you'll need to configure:
   1. DATABASE_URL - Your database connection string
   2. API_KEY - Your API key for the service

   Would you like me to:
   a) Update .env.template with these new variables
   b) Provide format requirements for each variable
   c) Both of the above
   ```

2. **Confirming Changes**
   ```markdown
   Before proceeding, please confirm:
   1. You've added the new variables to your .env
   2. The values match the required formats
   3. You've backed up any previous configuration

   Just reply with "confirmed" when ready.
   ```

## Change Management

1. **Breaking Changes**
   - MUST notify users of any breaking format changes
   - MUST provide migration instructions
   - MUST update all templates and documentation
   - MUST allow for backwards compatibility when possible

2. **Deprecation Process**
   ```markdown
   The LEGACY_API_KEY variable is being deprecated.
   1. Add NEW_API_KEY to your .env
   2. Once configured, let me know to proceed with migration
   3. After migration, I'll help you remove the legacy variable
   ``` 