"""
Export radiologist annotations with flattened columns.
Provides easy access to individual characteristics (subtlety, malignancy, etc.)
"""

import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from supabase import create_client, Client


class RadiologistExporter:
    """Export radiologist annotations with separate columns for each characteristic."""
    
    def __init__(self):
        """Initialize Supabase client."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY environment variables."
            )
        
        self.supabase: Client = create_client(url, key)
    
    def get_flattened_annotations(self) -> List[Dict[str, Any]]:
        """
        Get radiologist annotations with each characteristic in its own column.
        
        Returns:
            List of dictionaries with flattened annotation data
        """
        response = self.supabase.table('radiologist_annotations_flat').select('*').execute()
        return response.data
    
    def get_export_ready_data(self) -> List[Dict[str, Any]]:
        """
        Get export-ready data with human-readable column names.
        
        Returns:
            List of dictionaries ready for export
        """
        response = self.supabase.table('export_radiologist_data').select('*').execute()
        return response.data
    
    def filter_by_malignancy(self, min_score: int = 1, max_score: int = 5) -> List[Dict[str, Any]]:
        """
        Filter annotations by malignancy score range.
        
        Args:
            min_score: Minimum malignancy score (1-5)
            max_score: Maximum malignancy score (1-5)
        
        Returns:
            Filtered annotation data
        """
        response = (
            self.supabase
            .table('radiologist_annotations_flat')
            .select('*')
            .gte('malignancy', min_score)
            .lte('malignancy', max_score)
            .execute()
        )
        return response.data
    
    def filter_by_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Get all annotations for a specific patient.
        
        Args:
            patient_id: Patient identifier (e.g., 'LIDC-IDRI-0297')
        
        Returns:
            All annotations for the specified patient
        """
        response = (
            self.supabase
            .table('radiologist_annotations_flat')
            .select('*')
            .ilike('file_name', f'%{patient_id}%')
            .execute()
        )
        return response.data
    
    def get_high_risk_annotations(self) -> List[Dict[str, Any]]:
        """
        Get annotations with high malignancy scores (4-5) and suspicious characteristics.
        
        Returns:
            High-risk annotation data
        """
        response = (
            self.supabase
            .table('radiologist_annotations_flat')
            .select('*')
            .gte('malignancy', 4)
            .execute()
        )
        return response.data
    
    def refresh_export_table(self):
        """Refresh the materialized export view with latest data."""
        self.supabase.rpc('refresh_radiologist_export', {}).execute()
    
    def export_to_csv(
        self, 
        data: List[Dict[str, Any]], 
        output_path: str = './exports/radiologist_annotations.csv'
    ):
        """
        Export data to CSV file.
        
        Args:
            data: List of annotation dictionaries
            output_path: Path where CSV will be saved
        """
        if not data:
            print("No data to export")
            return
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with output_file.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"✅ Exported {len(data)} rows to {output_path}")
    
    def export_to_json(
        self,
        data: List[Dict[str, Any]],
        output_path: str = './exports/radiologist_annotations.json'
    ):
        """
        Export data to JSON file.
        
        Args:
            data: List of annotation dictionaries
            output_path: Path where JSON will be saved
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with output_file.open('w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"✅ Exported {len(data)} rows to {output_path}")
    
    def export_by_patient(self, output_dir: str = './exports/by_patient'):
        """
        Export separate CSV files for each patient.
        
        Args:
            output_dir: Directory where patient files will be saved
        """
        data = self.get_export_ready_data()
        
        if not data:
            print("No data to export")
            return
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Group by patient
        patients = {}
        for row in data:
            patient_id = row.get('patient_id', 'unknown')
            if patient_id not in patients:
                patients[patient_id] = []
            patients[patient_id].append(row)
        
        # Export each patient
        for patient_id, patient_data in patients.items():
            filename = f"{patient_id}.csv"
            filepath = output_path / filename
            
            with filepath.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=patient_data[0].keys())
                writer.writeheader()
                writer.writerows(patient_data)
            
            print(f"✅ Exported {len(patient_data)} annotations for {patient_id}")
    
    def print_summary(self):
        """Print summary statistics of radiologist annotations."""
        data = self.get_flattened_annotations()
        
        if not data:
            print("No data available")
            return
        
        print("\n" + "="*70)
        print("RADIOLOGIST ANNOTATION SUMMARY")
        print("="*70)
        
        print(f"\nTotal Annotations: {len(data)}")
        
        # Count unique patients
        patients = set(row.get('file_name') for row in data)
        print(f"Unique Patients: {len(patients)}")
        
        # Malignancy distribution
        malignancy_scores = [row.get('malignancy') for row in data if row.get('malignancy')]
        if malignancy_scores:
            print(f"\nMalignancy Score Distribution:")
            for score in range(1, 6):
                count = malignancy_scores.count(score)
                percentage = (count / len(malignancy_scores)) * 100
                print(f"  Score {score}: {count} ({percentage:.1f}%)")
        
        # Average scores
        if malignancy_scores:
            avg_malignancy = sum(malignancy_scores) / len(malignancy_scores)
            print(f"\nAverage Malignancy Score: {avg_malignancy:.2f}")
        
        print("="*70 + "\n")


def main():
    """Demo usage of RadiologistExporter."""
    exporter = RadiologistExporter()
    
    # Print summary
    exporter.print_summary()
    
    # Get all flattened annotations
    print("1. Getting flattened annotations...")
    annotations = exporter.get_flattened_annotations()
    print(f"   Found {len(annotations)} annotations")
    
    # Show sample
    if annotations:
        print("\n   Sample annotation:")
        sample = annotations[0]
        print(f"   Patient: {sample.get('file_name')}")
        print(f"   Radiologist #: {sample.get('annotation_number')}")
        print(f"   Subtlety: {sample.get('subtlety')}")
        print(f"   Malignancy: {sample.get('malignancy')}")
        print(f"   Spiculation: {sample.get('spiculation')}")
    
    # Export all data
    print("\n2. Exporting all annotations to CSV...")
    export_data = exporter.get_export_ready_data()
    exporter.export_to_csv(export_data, './exports/all_radiologist_annotations.csv')
    
    # Export high-risk annotations
    print("\n3. Exporting high-risk annotations (malignancy ≥ 4)...")
    high_risk = exporter.get_high_risk_annotations()
    print(f"   Found {len(high_risk)} high-risk annotations")
    if high_risk:
        exporter.export_to_csv(high_risk, './exports/high_risk_annotations.csv')
    
    # Export by patient
    print("\n4. Exporting separate files per patient...")
    exporter.export_by_patient()
    
    print("\n✅ Export complete!")


if __name__ == '__main__':
    main()
