# Case Identifier Installation

## Prerequisites

- Node.js 18+ and npm
- TypeScript 5.x
- Supabase account and project

## Installation Steps

### 1. Install Node.js Dependencies

```bash
cd src/case_identifier
npm install
```

This will install:
- `@supabase/supabase-js` - Supabase client
- `xml2js` - XML parsing
- `pdf-parse` - PDF text extraction
- `mammoth` - DOCX parsing
- `xlsx` - Excel file parsing
- `@types/node` - Node.js type definitions
- TypeScript and other dev dependencies

### 2. Set Up Database

Run the schema migration in your Supabase SQL editor:

```bash
# Copy the contents of migrations/002_unified_case_identifier_schema.sql
# Paste into Supabase SQL Editor and execute
```

Or if you have `psql` access:

```bash
psql -U postgres -d your_database -f ../../migrations/002_unified_case_identifier_schema.sql
```

### 3. Configure Environment

Create a `.env` file in `src/case_identifier/`:

```bash
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your_anon_key_here
```

### 4. Compile TypeScript

```bash
npm run build
```

This creates compiled JavaScript files in the `dist/` directory.

## Verify Installation

Run a quick test:

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_KEY!
);

// Test connection
const { data, error } = await supabase.from('file_imports').select('count');
console.log('Connection test:', error ? 'Failed' : 'Success');
```

## Missing Dependencies?

If you see errors about missing modules:

```bash
# Install all required type definitions
npm install --save-dev @types/node @types/xml2js @types/pdf-parse

# Install runtime dependencies
npm install @supabase/supabase-js xml2js pdf-parse mammoth xlsx
```

## TypeScript Configuration

The `tsconfig.json` is already configured with:
- Node.js types enabled
- ES2020 target
- CommonJS modules
- Strict mode with implicit any disabled for flexibility

## Next Steps

After installation:
1. Review `examples.ts` for usage patterns
2. Read `docs/CASE_IDENTIFIER_QUICKSTART.md` for quick start
3. See `docs/CASE_IDENTIFIER_README.md` for full documentation

## Troubleshooting

**Error: Cannot find module 'crypto'**  
Solution: Make sure `@types/node` is installed: `npm install --save-dev @types/node`

**Error: Cannot find module '@supabase/supabase-js'**  
Solution: Install Supabase client: `npm install @supabase/supabase-js`

**TypeScript errors about 'any' types**  
Solution: These are warnings, not errors. The code will compile. To see only errors: `tsc --noEmit`

**Runtime errors with file parsing**  
Solution: Make sure all parser libraries are installed:
```bash
npm install xml2js pdf-parse mammoth xlsx
```
