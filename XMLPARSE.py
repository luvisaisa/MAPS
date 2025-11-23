"""
Compatibility shim for legacy tests.

This module re-exports functions from the new ra_d_ps package structure
to maintain backward compatibility with old test files that import from XMLPARSE.

New code should import directly from ra_d_ps instead:
    from ra_d_ps import parse_radiology_sample, export_excel, etc.
"""

# Re-export all legacy functions from the new package structure
from src.ra_d_ps import (
    parse_radiology_sample,
    parse_multiple,
    export_excel,
    convert_parsed_data_to_ra_d_ps_format,
    detect_parse_case,
    get_expected_attributes_for_case,
    open_file_cross_platform
)

__all__ = [
    'parse_radiology_sample',
    'parse_multiple',
    'export_excel',
    'convert_parsed_data_to_ra_d_ps_format',
    'detect_parse_case',
    'get_expected_attributes_for_case',
    'open_file_cross_platform'
]
