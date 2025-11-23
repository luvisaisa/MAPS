"""
Extract keywords from imported LIDC data and detect patterns
"""

import sys
sys.path.insert(0, 'src')

import re
from collections import Counter
from ra_d_ps.supabase import supabase

# Medical/radiological terms to look for
MEDICAL_KEYWORDS = {
    'malignancy', 'malignant', 'benign',
    'spiculation', 'spiculated',
    'calcification', 'calcified',
    'sphericity', 'spherical',
    'margin', 'margins',
    'lobulation', 'lobulated',
    'texture', 'textured',
    'subtlety', 'subtle',
    'nodule', 'nodules',
    'internal structure', 'structure',
    'radiologist', 'annotation'
}

def extract_keywords_from_text(text):
    """Extract relevant keywords from text"""
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in MEDICAL_KEYWORDS:
        if keyword in text_lower:
            # Count occurrences
            count = text_lower.count(keyword)
            found_keywords.append({
                'term': keyword,
                'count': count
            })
    
    return found_keywords

def calculate_relevance(term, total_freq, doc_freq, total_docs):
    """Simple TF-IDF style relevance"""
    import math
    if doc_freq == 0 or total_docs == 0:
        return 0.0
    
    tf = total_freq
    idf = math.log(total_docs / doc_freq) if doc_freq > 0 else 0
    return tf * idf

def main():
    print("="*70)
    print("KEYWORD EXTRACTION FROM LIDC DATA")
    print("="*70)
    
    # Get all qualitative segments (text annotations)
    print("\n1. Loading qualitative segments...")
    qual_segments = supabase.table('qualitative_segments').select('*').execute()
    print(f"   Found {len(qual_segments.data)} qualitative segments")
    
    # Extract keywords from each segment
    print("\n2. Extracting keywords...")
    all_keywords = Counter()
    keyword_docs = Counter()
    keyword_occurrences = []
    
    for segment in qual_segments.data:
        text = segment['text_content']
        segment_id = segment['segment_id']
        file_id = segment['file_id']
        
        keywords = extract_keywords_from_text(text)
        doc_keywords = set()
        
        for kw in keywords:
            term = kw['term']
            count = kw['count']
            
            all_keywords[term] += count
            doc_keywords.add(term)
            
            keyword_occurrences.append({
                'term': term,
                'segment_id': segment_id,
                'file_id': file_id,
                'count': count,
                'context': text[:200]  # First 200 chars
            })
        
        # Count docs containing each keyword
        for term in doc_keywords:
            keyword_docs[term] += 1
    
    print(f"   Extracted {len(all_keywords)} unique keywords")
    print(f"   Total {sum(all_keywords.values())} keyword occurrences")
    
    # Insert into extracted_keywords table
    print("\n3. Inserting keywords into database...")
    total_docs = len(qual_segments.data)
    inserted = 0
    
    for term, total_freq in all_keywords.items():
        doc_freq = keyword_docs[term]
        relevance = calculate_relevance(term, total_freq, doc_freq, total_docs)
        
        keyword_data = {
            'term': term,
            'normalized_term': term.lower().strip(),
            'is_phrase': ' ' in term,
            'total_frequency': total_freq,
            'document_frequency': doc_freq,
            'relevance_score': round(relevance, 6)
        }
        
        try:
            result = supabase.table('extracted_keywords').upsert(
                keyword_data,
                on_conflict='normalized_term'
            ).execute()
            inserted += 1
        except Exception as e:
            print(f"   ⚠️  Failed to insert '{term}': {e}")
    
    print(f"   ✅ Inserted {inserted} keywords")
    
    # Insert keyword occurrences
    print("\n4. Inserting keyword occurrences...")
    
    # First, get keyword_ids
    keywords_lookup = {}
    all_kw = supabase.table('extracted_keywords').select('keyword_id, normalized_term').execute()
    for kw in all_kw.data:
        keywords_lookup[kw['normalized_term']] = kw['keyword_id']
    
    occurrence_count = 0
    for occ in keyword_occurrences:
        term_normalized = occ['term'].lower().strip()
        keyword_id = keywords_lookup.get(term_normalized)
        
        if keyword_id:
            occ_data = {
                'keyword_id': keyword_id,
                'segment_id': occ['segment_id'],
                'segment_type': 'qualitative',
                'file_id': occ['file_id'],
                'surrounding_context': occ['context']
            }
            
            try:
                supabase.table('keyword_occurrences').insert(occ_data).execute()
                occurrence_count += 1
            except Exception as e:
                pass  # May fail on duplicates
    
    print(f"   ✅ Inserted {occurrence_count} keyword occurrences")
    
    # Show top keywords
    print("\n5. Top Keywords by Relevance:")
    top_keywords = supabase.table('extracted_keywords')\
        .select('term, relevance_score, total_frequency, document_frequency')\
        .order('relevance_score', desc=True)\
        .limit(15)\
        .execute()
    
    for i, kw in enumerate(top_keywords.data, 1):
        print(f"   {i:2}. {kw['term']:20} - relevance: {kw['relevance_score']:6.2f}, "
              f"total: {kw['total_frequency']:3}, docs: {kw['document_frequency']}")
    
    # Detect simple patterns (keywords appearing together)
    print("\n6. Detecting case patterns...")
    
    # Group by file_id to find co-occurring keywords
    files = supabase.table('file_imports').select('file_id, filename').execute()
    
    pattern_count = 0
    for file in files.data[:5]:  # First 5 files
        file_id = file['file_id']
        
        # Get all keywords in this file
        file_keywords = supabase.table('keyword_occurrences')\
            .select('keyword_id, segment_id')\
            .eq('file_id', file_id)\
            .execute()
        
        if len(file_keywords.data) >= 3:  # At least 3 keywords
            # Get unique keywords
            unique_keywords = list(set(kw['keyword_id'] for kw in file_keywords.data))
            unique_segments = list(set(kw['segment_id'] for kw in file_keywords.data))
            
            # Calculate confidence (simple: keyword count / segment count)
            confidence = len(unique_keywords) / max(len(unique_segments), 1)
            
            # Create pattern signature
            import hashlib
            pattern_sig = hashlib.sha256(
                ''.join(sorted(str(k) for k in unique_keywords)).encode()
            ).hexdigest()
            
            # Get keyword details
            kw_details = supabase.table('extracted_keywords')\
                .select('keyword_id, term')\
                .in_('keyword_id', unique_keywords)\
                .execute()
            
            pattern_data = {
                'pattern_signature': pattern_sig,
                'keywords': [{'keyword_id': str(kw['keyword_id']), 'term': kw['term']} 
                            for kw in kw_details.data],
                'source_segments': [{'segment_id': str(seg), 'segment_type': 'qualitative', 'file_id': str(file_id)} 
                                   for seg in unique_segments],
                'confidence_score': round(confidence, 6),
                'cross_type_validated': False,  # Only qualitative for now
                'keyword_count': len(unique_keywords),
                'segment_count': len(unique_segments),
                'file_count': 1
            }
            
            try:
                supabase.table('case_patterns').upsert(
                    pattern_data,
                    on_conflict='pattern_signature'
                ).execute()
                pattern_count += 1
            except Exception as e:
                pass
    
    print(f"   ✅ Detected {pattern_count} case patterns")
    
    # Final summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    stats = supabase.table('file_imports').select('*').execute()
    segments = supabase.table('unified_segments').select('segment_type').execute()
    keywords = supabase.table('extracted_keywords').select('*').execute()
    patterns = supabase.table('case_patterns').select('*').execute()
    
    print(f"📁 Files: {len(stats.data)}")
    print(f"📄 Segments: {len(segments.data)}")
    print(f"   - Qualitative: {sum(1 for s in segments.data if s['segment_type'] == 'qualitative')}")
    print(f"   - Quantitative: {sum(1 for s in segments.data if s['segment_type'] == 'quantitative')}")
    print(f"🔑 Keywords: {len(keywords.data)}")
    print(f"🔍 Case Patterns: {len(patterns.data)}")
    
    print("\n✅ Keyword extraction complete!")
    print("\nNext: Deploy analysis views (003_analysis_views.sql) for advanced filtering")
    print("="*70)

if __name__ == '__main__':
    main()
