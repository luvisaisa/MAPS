"""
MAPS: Medical Annotation Processing Suite

A comprehensive Python package for parsing, analyzing, and exporting 
radiology XML data from various medical imaging systems.
"""

# Import from the main parser module (lazy to avoid tkinter dependency)
def _lazy_import_parser():
    """Lazy import parser functions to avoid tkinter dependency in API context"""
    from .parser import (
        parse_radiology_sample,
        parse_multiple,
        export_excel,
        convert_parsed_data_to_maps_format,
        open_file_cross_platform,
        detect_parse_case,
        get_expected_attributes_for_case
    )
    return (parse_radiology_sample, parse_multiple, export_excel,
            convert_parsed_data_to_maps_format, open_file_cross_platform,
            detect_parse_case, get_expected_attributes_for_case)

# Try to import parser functions, but don't fail if tkinter unavailable
try:
    from .parser import (
        parse_radiology_sample,
        parse_multiple,
        export_excel,
        convert_parsed_data_to_maps_format,
        open_file_cross_platform,
        detect_parse_case,
        get_expected_attributes_for_case
    )
except ImportError as e:
    # If tkinter not available, set placeholders
    if "tkinter" in str(e):
        parse_radiology_sample = None
        parse_multiple = None
        export_excel = None
        convert_parsed_data_to_maps_format = None
        open_file_cross_platform = None
        detect_parse_case = None
        get_expected_attributes_for_case = None
    else:
        raise

# Import GUI from separate module
try:
    from .gui import MAPSGuiApp
except (ImportError, AttributeError):
    # GUI might be commented out or unavailable
    MAPSGuiApp = None

# Import database functionality
try:
    from .database import RadiologyDatabase
except ImportError:
    # Database might not be available in all environments
    RadiologyDatabase = None

# Import structure detection and batch processing
try:
    from .structure_detector import XMLStructureDetector, batch_detect_parse_cases
    from .batch_processor import BatchProcessor, analyze_batch_structure, create_optimized_processing_plan
except ImportError:
    # Structure detection might not be available in all environments
    XMLStructureDetector = None
    BatchProcessor = None
    batch_detect_parse_cases = None
    analyze_batch_structure = None
    create_optimized_processing_plan = None

__version__ = "1.0.0"
__author__ = "MAPS Team"

# Define public API
__all__ = [
    'parse_radiology_sample',
    'parse_multiple', 
    'export_excel',
    'convert_parsed_data_to_maps_format',
    'MAPSGuiApp',
    'RadiologyDatabase',
    'open_file_cross_platform',
    'detect_parse_case',
    'get_expected_attributes_for_case',
    'XMLStructureDetector',
    'BatchProcessor',
    'batch_detect_parse_cases',
    'analyze_batch_structure',
    'create_optimized_processing_plan'
]
