"""
Analysis and Export Utilities for Case Identifier System

Provides easy-to-use functions for:
- Filtering and exporting data to CSV, Excel, JSON
- Generating analysis reports
- Refreshing materialized views
- Common query patterns
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
import os


class AnalysisExporter:
    """Handle data export and analysis from case identifier system"""
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize with Supabase credentials
        
        Args:
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase anon key (defaults to SUPABASE_KEY env var)
        """
        self.supabase: Client = create_client(
            supabase_url or os.getenv('SUPABASE_URL'),
            supabase_key or os.getenv('SUPABASE_KEY')
        )
    
    def get_master_table(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Get data from master_analysis_table with optional filters
        
        Args:
            filters: Dict of column: value pairs for filtering
            
        Returns:
            List of dictionaries with analysis data
            
        Example:
            exporter.get_master_table({
                'segment_type': 'qualitative',
                'file_type': 'xml'
            })
        """
        query = self.supabase.table('master_analysis_table').select('*')
        
        if filters:
            for column, value in filters.items():
                query = query.eq(column, value)
        
        response = query.execute()
        return response.data
    
    def get_export_table(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get pre-computed export_ready_table (fast)
        
        Args:
            limit: Maximum rows to return (None = all)
            
        Returns:
            List of export-ready dictionaries
        """
        query = self.supabase.table('export_ready_table').select('*')
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data
    
    def filter_by_criteria(
        self,
        file_types: Optional[List[str]] = None,
        segment_types: Optional[List[str]] = None,
        min_keyword_count: int = 0,
        has_case_patterns: Optional[bool] = None,
        date_from: Optional[str] = None,  # ISO format: '2024-01-01'
        date_to: Optional[str] = None,
        keyword_search: Optional[str] = None
    ) -> List[Dict]:
        """
        Use filter_analysis_table PostgreSQL function for complex filtering
        
        Args:
            file_types: List of extensions (e.g., ['xml', 'pdf'])
            segment_types: List of types (['quantitative', 'qualitative', 'mixed'])
            min_keyword_count: Minimum keywords required
            has_case_patterns: True = only with patterns, False = only without
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            keyword_search: Search term in keywords
            
        Returns:
            Filtered results as list of dictionaries
        """
        params = {
            'p_file_types': file_types,
            'p_segment_types': segment_types,
            'p_min_keyword_count': min_keyword_count,
            'p_has_case_patterns': has_case_patterns,
            'p_date_from': date_from,
            'p_date_to': date_to,
            'p_keyword_search': keyword_search
        }
        
        response = self.supabase.rpc('filter_analysis_table', params).execute()
        return response.data
    
    def refresh_export_table(self) -> Dict:
        """
        Refresh materialized export_ready_table for latest data
        
        Returns:
            Dict with refresh stats (total_rows, refresh_duration, timestamp)
        """
        response = self.supabase.rpc('refresh_export_table', {}).execute()
        return response.data[0] if response.data else {}
    
    def export_to_csv(
        self,
        output_path: str,
        data: Optional[List[Dict]] = None,
        use_export_table: bool = True,
        filters: Optional[Dict] = None
    ) -> Path:
        """
        Export data to CSV file
        
        Args:
            output_path: Path for output CSV file
            data: Pre-fetched data (if None, fetches from DB)
            use_export_table: Use fast export_ready_table (True) or master (False)
            filters: Optional filters if fetching from DB
            
        Returns:
            Path object of created file
        """
        if data is None:
            if use_export_table:
                data = self.get_export_table()
            else:
                data = self.get_master_table(filters)
        
        if not data:
            print(f"⚠️  No data to export")
            return None
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with output_file.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ Exported {len(data)} rows to {output_file}")
        return output_file
    
    def export_to_json(
        self,
        output_path: str,
        data: Optional[List[Dict]] = None,
        use_export_table: bool = True,
        filters: Optional[Dict] = None,
        pretty: bool = True
    ) -> Path:
        """
        Export data to JSON file
        
        Args:
            output_path: Path for output JSON file
            data: Pre-fetched data (if None, fetches from DB)
            use_export_table: Use fast export_ready_table (True) or master (False)
            filters: Optional filters if fetching from DB
            pretty: Pretty-print JSON (True) or compact (False)
            
        Returns:
            Path object of created file
        """
        if data is None:
            if use_export_table:
                data = self.get_export_table()
            else:
                data = self.get_master_table(filters)
        
        if not data:
            print(f"⚠️  No data to export")
            return None
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with output_file.open('w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, default=str)
            else:
                json.dump(data, f, default=str)
        
        print(f"✅ Exported {len(data)} rows to {output_file}")
        return output_file
    
    def get_summary_stats(self) -> Dict:
        """
        Get high-level statistics about the dataset
        
        Returns:
            Dict with counts and distributions
        """
        stats = {}
        
        # File counts
        files = self.supabase.table('file_imports').select('extension, processing_status').execute()
        stats['total_files'] = len(files.data)
        stats['files_by_type'] = {}
        stats['files_by_status'] = {}
        
        for file in files.data:
            ext = file['extension']
            status = file['processing_status']
            stats['files_by_type'][ext] = stats['files_by_type'].get(ext, 0) + 1
            stats['files_by_status'][status] = stats['files_by_status'].get(status, 0) + 1
        
        # Segment counts
        segments = self.supabase.table('unified_segments').select('segment_type').execute()
        stats['total_segments'] = len(segments.data)
        stats['segments_by_type'] = {}
        
        for seg in segments.data:
            seg_type = seg['segment_type']
            stats['segments_by_type'][seg_type] = stats['segments_by_type'].get(seg_type, 0) + 1
        
        # Keyword counts
        keywords = self.supabase.table('extracted_keywords').select('keyword_id, document_frequency').execute()
        stats['total_keywords'] = len(keywords.data)
        
        if keywords.data:
            doc_freqs = [k['document_frequency'] for k in keywords.data]
            stats['avg_document_frequency'] = sum(doc_freqs) / len(doc_freqs)
        
        # Case pattern counts
        patterns = self.supabase.table('case_patterns').select('case_id, cross_type_validated').execute()
        stats['total_case_patterns'] = len(patterns.data)
        stats['cross_validated_patterns'] = sum(1 for p in patterns.data if p.get('cross_type_validated'))
        
        return stats
    
    def print_summary(self):
        """Print formatted summary statistics"""
        stats = self.get_summary_stats()
        
        print("\n" + "="*60)
        print("CASE IDENTIFIER SYSTEM - SUMMARY STATISTICS")
        print("="*60)
        
        print(f"\n📁 FILES: {stats['total_files']}")
        for file_type, count in stats.get('files_by_type', {}).items():
            print(f"   {file_type}: {count}")
        
        print(f"\n📊 PROCESSING STATUS:")
        for status, count in stats.get('files_by_status', {}).items():
            print(f"   {status}: {count}")
        
        print(f"\n📄 SEGMENTS: {stats['total_segments']}")
        for seg_type, count in stats.get('segments_by_type', {}).items():
            print(f"   {seg_type}: {count}")
        
        print(f"\n🔑 KEYWORDS: {stats['total_keywords']}")
        if 'avg_document_frequency' in stats:
            print(f"   Average doc frequency: {stats['avg_document_frequency']:.2f}")
        
        print(f"\n🔍 CASE PATTERNS: {stats['total_case_patterns']}")
        print(f"   Cross-validated: {stats.get('cross_validated_patterns', 0)}")
        
        print("\n" + "="*60 + "\n")
    
    def export_by_file_type(self, file_type: str, output_dir: str = "./exports"):
        """
        Export all data for a specific file type
        
        Args:
            file_type: Extension (e.g., 'xml', 'pdf')
            output_dir: Output directory path
        """
        print(f"\n🔄 Exporting all {file_type} data...")
        
        data = self.filter_by_criteria(file_types=[file_type])
        
        if not data:
            print(f"⚠️  No data found for file type: {file_type}")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_path = f"{output_dir}/{file_type}_export_{timestamp}.csv"
        json_path = f"{output_dir}/{file_type}_export_{timestamp}.json"
        
        self.export_to_csv(csv_path, data=data)
        self.export_to_json(json_path, data=data)
        
        print(f"✅ Exported {len(data)} {file_type} segments")
    
    def export_high_relevance_keywords(self, min_relevance: float = 5.0, output_dir: str = "./exports"):
        """
        Export high-relevance keywords with their contexts
        
        Args:
            min_relevance: Minimum relevance score threshold
            output_dir: Output directory path
        """
        print(f"\n🔄 Exporting keywords with relevance ≥ {min_relevance}...")
        
        query = self.supabase.table('extracted_keywords').select('*').gte('relevance_score', min_relevance)
        response = query.execute()
        
        if not response.data:
            print(f"⚠️  No keywords found with relevance ≥ {min_relevance}")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"{output_dir}/high_relevance_keywords_{timestamp}.json"
        
        self.export_to_json(output_path, data=response.data)
        print(f"✅ Exported {len(response.data)} high-relevance keywords")


# Convenience functions
def quick_export(output_path: str, format: str = 'csv', filters: Optional[Dict] = None):
    """
    Quick export without creating exporter instance
    
    Args:
        output_path: Output file path
        format: 'csv' or 'json'
        filters: Optional filters
    """
    exporter = AnalysisExporter()
    
    if format.lower() == 'csv':
        return exporter.export_to_csv(output_path, filters=filters)
    elif format.lower() == 'json':
        return exporter.export_to_json(output_path, filters=filters)
    else:
        raise ValueError(f"Unsupported format: {format}")


def print_stats():
    """Quick summary statistics"""
    exporter = AnalysisExporter()
    exporter.print_summary()


if __name__ == '__main__':
    # Example usage
    exporter = AnalysisExporter()
    
    print("Running example exports...")
    
    # Print summary
    exporter.print_summary()
    
    # Export all data
    exporter.export_to_csv('./exports/all_data.csv')
    
    # Export filtered data
    qualitative_data = exporter.filter_by_criteria(
        segment_types=['qualitative'],
        min_keyword_count=3
    )
    exporter.export_to_json('./exports/qualitative_with_keywords.json', data=qualitative_data)
    
    print("\n✅ Example exports complete!")
