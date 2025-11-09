# Phase 2 Technical Notes - Translation Edge Function

**Phase**: Phase 2 - Translation Edge Function Unit Tests  
**Date**: 2025-10-29  
**Component**: Translation Edge Function

---

## Technical Implementation Details

### Hugging Face Integration Architecture

The implementation uses Hugging Face Inference API for translation. Initially attempted NLLB-200 but switched to Helsinki-NLP models due to availability.

#### Model Selection Logic

```typescript
// Language pair to model mapping
if (sourceLang === 'eng_Latn' && targetLang === 'spa_Latn') {
  modelId = 'Helsinki-NLP/opus-mt-en-es';
} else if (sourceLang === 'spa_Latn' && targetLang === 'eng_Latn') {
  modelId = 'Helsinki-NLP/opus-mt-es-en';
}
// ... additional mappings
```

**Decision**: Use Helsinki-NLP over NLLB-200
- **Reason**: NLLB-200 not available via Inference API
- **Trade-off**: Slightly less multilingual but more reliable
- **Future**: Can add NLLB-200 support if API becomes available

### Language Code Mapping

Created mapping from ISO codes to NLLB-200 format codes:

```typescript
private mapToNLLBCode(langCode: string): string {
  const mapping: Record<string, string> = {
    'en': 'eng_Latn',
    'es': 'spa_Latn',
    'zh': 'zho_Hans',
    'ar': 'arb_Arab',
    'vi': 'vie_Latn',
    // ... more mappings
  };
  return mapping[langCode] || langCode;
}
```

Even though using Helsinki-NLP, kept NLLB-200 code mapping for future compatibility.

---

## Testing Approach

### Test Organization

All tests organized under `/tests/agents/patient_navigator/vercel_edge_functions/translation/` as specified in project structure.

### Environment Variable Loading

Jest configuration loads `.env.development` from project root:
- Path calculation: 5 directory levels up from test file
- Parsing: Manual env file parsing in jest.env.js
- Defaults: Graceful fallback when .env files missing
- Security: Tokens masked in logs

### Console Debugging

Disabled console mocking to see real output:
```javascript
// jest.setup.js
// Don't mock console for now - we need to see debug output
```

This was critical for debugging API calls.

---

## API Integration Details

### Request Format

```typescript
const body = {
  inputs: request.text,  // Direct text for Helsinki-NLP
};
```

### Response Format

```typescript
[
  {
    "translation_text": "translated text"
  }
]
```

### Error Handling

- Graceful fallback to original text on error
- Error returned in response.error field
- success: false indicates error
- Original text returned for user continuity

---

## Performance Observations

### Model Loading Effect

**Finding**: First translation to any language pair is significantly slower
- Spanish outbound (first call): 4269ms
- Spanish inbound (subsequent): 345ms
- Arabic inbound (first call): 9207ms
- Arabic outbound (subsequent): 1710ms

**Reason**: Hugging Face loads model on first use
**Impact**: First user may experience slower response
**Mitigation**: Could warm up models or accept first-call latency

### Typical Performance

Most translations (after model loaded):
- ✅ Spanish inbound: 345ms
- ✅ Cantonese: 262ms
- ✅ Tagalog: 353ms
- ✅ Vietnamese inbound: 481ms

Some languages consistently slower:
- ⚠️ Vietnamese outbound: 4326ms
- ⚠️ Mandarin outbound: 4114ms

### Performance Targets

From prompt_2.md:
- **Target**: Translation < 500ms performance tests
- **Actual**: Most translations meet this when model is warmed up
- **First call**: Can take 4-9 seconds (model loading)

---

## Technical Decisions

### Decision 1: Mock vs Real API

**Choice**: Support both mock and real modes
**Implementation**: Environment variable toggle
```typescript
process.env.USE_MOCK_TRANSLATION = 'true'  // Mock mode
process.env.USE_MOCK_TRANSLATION = 'false' // Real API
```

**Rationale**:
- Faster tests in mock mode
- Real API validation when needed
- Easy to switch for testing

### Decision 2: Jest over Vitest

**Choice**: Use Jest
**Rationale**:
- Already configured in project
- Better TypeScript support
- Standard Node.js environment
- Consistent with existing test infrastructure

### Decision 3: Test Location

**Choice**: `/tests/agents/patient_navigator/vercel_edge_functions/translation/`
**Rationale**:
- Separates tests from implementation
- Matches project conventions
- Easier to find and maintain
- Consistent with Python test patterns

### Decision 4: Environment Loading

**Choice**: Load from project root `.env.development`
**Rationale**:
- Centralized configuration
- Supports multiple environments (dev, staging, prod)
- Easy to override with TEST_ENV
- Defaults gracefully when missing

---

## Code Quality

### Type Safety

- Full TypeScript implementation
- Strong typing for all interfaces
- Type validation in tests
- No `any` types used

### Error Handling

- Comprehensive error catching
- Graceful degradation
- User-friendly error messages
- Debug logging for troubleshooting

### Code Organization

- Single responsibility per function
- Clear naming conventions
- Comprehensive comments
- Follows existing patterns

---

## Integration Points

### With Environment

- Loads from `.env.development`
- Supports environment-specific configs
- Token-based authentication

### With Vercel

- Edge runtime compatible
- Web API usage only
- No Node.js-specific features
- Stateless service design

### With Testing

- Jest integration working
- Environment variable loading
- Real API testing capability
- Mock mode for fast tests

---

## Future Enhancements

1. **Model Improvements**
   - Add NLLB-200 support when API becomes available
   - Support more language pairs
   - Better model selection logic

2. **Performance Optimizations**
   - Model warming for common languages
   - Caching frequently translated phrases
   - Connection pooling

3. **Testing Improvements**
   - Coverage reporting working
   - Add integration tests
   - Add end-to-end tests

4. **Language Support**
   - Add remaining languages from supported list
   - Dynamic model selection
   - Language detection

---

**Document Status**: Final  
**Last Updated**: 2025-10-29  
**Component**: Translation Edge Function

