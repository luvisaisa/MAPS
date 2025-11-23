# Web Dashboard Setup

Simple web interface for non-technical users to view and export LIDC-IDRI data.

## Setup Steps

### 1. Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Click **Settings** → **API**
3. Copy:
   - `Project URL` (looks like: https://xxxxx.supabase.co)
   - `anon public` key (long string starting with "eyJ...")

### 2. Configure Dashboard

Edit `index.html` and replace:

```javascript
const SUPABASE_URL = 'YOUR_SUPABASE_URL'
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY'
```

### 3. Enable Row Level Security (RLS)

In Supabase SQL Editor, run:

```sql
-- Allow anonymous read access to analysis views
ALTER TABLE master_analysis_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous read access"
ON master_analysis_table
FOR SELECT
TO anon
USING (true);

-- Same for export table
ALTER TABLE export_ready_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow anonymous read access"
ON export_ready_table
FOR SELECT
TO anon
USING (true);
```

### 4. Deploy Dashboard

**Option A: Local Testing**
- Just open `index.html` in a web browser
- No server needed

**Option B: Deploy to Vercel (Free)**
1. Create account at https://vercel.com
2. Drag and drop the `web_dashboard` folder
3. Share the generated URL

**Option C: Deploy to Netlify (Free)**
1. Create account at https://netlify.com
2. Drag and drop the `web_dashboard` folder
3. Share the generated URL

**Option D: Host on Supabase Storage**
1. Go to Supabase → Storage → Create bucket "public"
2. Upload `index.html`
3. Make bucket public
4. Share the file URL

## Features

✅ **View all data** - Browse analysis table with pagination  
✅ **Filter data** - By segment type, file type, content search  
✅ **Live stats** - Total records, files, qualitative/quantitative counts  
✅ **Export** - Download filtered data as CSV or JSON  
✅ **No coding** - Point-and-click interface  
✅ **Real-time** - Always shows latest data from database

## Security Notes

- Uses anonymous read-only access (no login required)
- Only SELECT queries allowed (no modifications)
- RLS policies protect data
- ANON key is safe to expose publicly (read-only)

## Troubleshooting

**Can't see data?**
- Check RLS policies are created
- Verify credentials in index.html
- Check browser console for errors

**Filters not working?**
- Clear filters and refresh
- Check column names match database

**Export not working?**
- Try smaller dataset first
- Check browser allows downloads
