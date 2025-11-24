"""
Parse Case Schemas and Expected Attributes

Defines expected attributes for each parse case to enable
detailed detection analysis and match percentage calculations.
"""

from typing import Dict, List, TypedDict


class AttributeDefinition(TypedDict):
    """
    Definition of an expected attribute for a parse case
    """
    name: str                # Attribute name
    xpath: str              # XPath location in XML
    data_type: str          # Data type (string, int, float, date)
    required: bool          # Whether attribute is mandatory
    description: str        # Human-readable description


# Parse Case Schema Definitions
# Each parse case defines its expected attributes with XPath locations

COMPLETE_ATTRIBUTES_SCHEMA: Dict[str, List[AttributeDefinition]] = {
    "expected_attributes": [
        {
            "name": "study_instance_uid",
            "xpath": "/ResponseHeader/StudyInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Study Instance UID"
        },
        {
            "name": "series_instance_uid",
            "xpath": "/ResponseHeader/SeriesInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Series Instance UID"
        },
        {
            "name": "radiologist_1_name",
            "xpath": "/ResponseHeader/readingSessionInfo/servicingRadiologistID",
            "data_type": "string",
            "required": True,
            "description": "Primary radiologist identifier"
        },
        {
            "name": "radiologist_1_time",
            "xpath": "/ResponseHeader/readingSessionInfo/annotationVersion",
            "data_type": "string",
            "required": True,
            "description": "Primary radiologist reading time"
        },
        {
            "name": "nodule_count",
            "xpath": "count(//unblindedReadNodule)",
            "data_type": "int",
            "required": True,
            "description": "Number of nodules annotated"
        },
        {
            "name": "nodule_id",
            "xpath": "//unblindedReadNodule/noduleID",
            "data_type": "string",
            "required": True,
            "description": "Nodule identifier"
        },
        {
            "name": "characteristics_subtlety",
            "xpath": "//characteristics/subtlety",
            "data_type": "int",
            "required": True,
            "description": "Nodule subtlety rating (1-5)"
        },
        {
            "name": "characteristics_internalStructure",
            "xpath": "//characteristics/internalStructure",
            "data_type": "int",
            "required": True,
            "description": "Nodule internal structure rating"
        },
        {
            "name": "characteristics_calcification",
            "xpath": "//characteristics/calcification",
            "data_type": "int",
            "required": True,
            "description": "Nodule calcification rating"
        },
        {
            "name": "characteristics_malignancy",
            "xpath": "//characteristics/malignancy",
            "data_type": "int",
            "required": True,
            "description": "Nodule malignancy rating (1-5)"
        }
    ]
}

LIDC_SINGLE_SESSION_SCHEMA: Dict[str, List[AttributeDefinition]] = {
    "expected_attributes": [
        {
            "name": "study_instance_uid",
            "xpath": "/ResponseHeader/StudyInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Study Instance UID"
        },
        {
            "name": "series_instance_uid",
            "xpath": "/ResponseHeader/SeriesInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Series Instance UID"
        },
        {
            "name": "reading_session",
            "xpath": "/ResponseHeader/readingSessionInfo",
            "data_type": "string",
            "required": True,
            "description": "Single reading session information"
        },
        {
            "name": "radiologist_id",
            "xpath": "/ResponseHeader/readingSessionInfo/servicingRadiologistID",
            "data_type": "string",
            "required": True,
            "description": "Radiologist identifier"
        },
        {
            "name": "nodule_count",
            "xpath": "count(//unblindedReadNodule)",
            "data_type": "int",
            "required": True,
            "description": "Number of nodules"
        },
        {
            "name": "nodule_id",
            "xpath": "//unblindedReadNodule/noduleID",
            "data_type": "string",
            "required": True,
            "description": "Nodule ID"
        },
        {
            "name": "roi_count",
            "xpath": "count(//roi)",
            "data_type": "int",
            "required": True,
            "description": "Number of ROIs"
        },
        {
            "name": "characteristics",
            "xpath": "//characteristics",
            "data_type": "element",
            "required": True,
            "description": "Nodule characteristics"
        }
    ]
}

LIDC_MULTI_SESSION_2_SCHEMA: Dict[str, List[AttributeDefinition]] = {
    "expected_attributes": [
        {
            "name": "study_instance_uid",
            "xpath": "/ResponseHeader/StudyInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Study Instance UID"
        },
        {
            "name": "series_instance_uid",
            "xpath": "/ResponseHeader/SeriesInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Series Instance UID"
        },
        {
            "name": "reading_session_count",
            "xpath": "count(/ResponseHeader/readingSessionInfo)",
            "data_type": "int",
            "required": True,
            "description": "Number of reading sessions (should be 2)"
        },
        {
            "name": "radiologist_1_id",
            "xpath": "(/ResponseHeader/readingSessionInfo/servicingRadiologistID)[1]",
            "data_type": "string",
            "required": True,
            "description": "First radiologist ID"
        },
        {
            "name": "radiologist_2_id",
            "xpath": "(/ResponseHeader/readingSessionInfo/servicingRadiologistID)[2]",
            "data_type": "string",
            "required": True,
            "description": "Second radiologist ID"
        },
        {
            "name": "nodule_count_radiologist_1",
            "xpath": "count((/ResponseHeader/readingSessionInfo)[1]//unblindedReadNodule)",
            "data_type": "int",
            "required": True,
            "description": "Nodules from radiologist 1"
        },
        {
            "name": "nodule_count_radiologist_2",
            "xpath": "count((/ResponseHeader/readingSessionInfo)[2]//unblindedReadNodule)",
            "data_type": "int",
            "required": True,
            "description": "Nodules from radiologist 2"
        },
        {
            "name": "nodule_id_radiologist_1",
            "xpath": "(/ResponseHeader/readingSessionInfo)[1]//unblindedReadNodule/noduleID",
            "data_type": "string",
            "required": True,
            "description": "Nodule IDs from radiologist 1"
        },
        {
            "name": "nodule_id_radiologist_2",
            "xpath": "(/ResponseHeader/readingSessionInfo)[2]//unblindedReadNodule/noduleID",
            "data_type": "string",
            "required": True,
            "description": "Nodule IDs from radiologist 2"
        },
        {
            "name": "characteristics_radiologist_1",
            "xpath": "(/ResponseHeader/readingSessionInfo)[1]//characteristics",
            "data_type": "element",
            "required": True,
            "description": "Characteristics from radiologist 1"
        },
        {
            "name": "characteristics_radiologist_2",
            "xpath": "(/ResponseHeader/readingSessionInfo)[2]//characteristics",
            "data_type": "element",
            "required": True,
            "description": "Characteristics from radiologist 2"
        },
        {
            "name": "roi_count_total",
            "xpath": "count(//roi)",
            "data_type": "int",
            "required": True,
            "description": "Total ROI count across all sessions"
        }
    ]
}

WITH_REASON_PARTIAL_SCHEMA: Dict[str, List[AttributeDefinition]] = {
    "expected_attributes": [
        {
            "name": "study_instance_uid",
            "xpath": "/ResponseHeader/StudyInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Study Instance UID"
        },
        {
            "name": "series_instance_uid",
            "xpath": "/ResponseHeader/SeriesInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Series Instance UID"
        },
        {
            "name": "radiologist_id",
            "xpath": "/ResponseHeader/readingSessionInfo/servicingRadiologistID",
            "data_type": "string",
            "required": True,
            "description": "Radiologist identifier"
        },
        {
            "name": "nodule_count",
            "xpath": "count(//unblindedReadNodule)",
            "data_type": "int",
            "required": True,
            "description": "Number of nodules"
        },
        {
            "name": "nodule_id",
            "xpath": "//unblindedReadNodule/noduleID",
            "data_type": "string",
            "required": True,
            "description": "Nodule identifier"
        },
        {
            "name": "characteristics_subtlety",
            "xpath": "//characteristics/subtlety",
            "data_type": "int",
            "required": False,
            "description": "Nodule subtlety rating (may be missing)"
        },
        {
            "name": "reason_for_missing",
            "xpath": "//reasonForMissing",
            "data_type": "string",
            "required": True,
            "description": "Explanation for missing characteristics"
        }
    ]
}

CORE_ATTRIBUTES_ONLY_SCHEMA: Dict[str, List[AttributeDefinition]] = {
    "expected_attributes": [
        {
            "name": "study_instance_uid",
            "xpath": "/ResponseHeader/StudyInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Study Instance UID"
        },
        {
            "name": "series_instance_uid",
            "xpath": "/ResponseHeader/SeriesInstanceUID",
            "data_type": "string",
            "required": True,
            "description": "DICOM Series Instance UID"
        },
        {
            "name": "radiologist_id",
            "xpath": "/ResponseHeader/readingSessionInfo/servicingRadiologistID",
            "data_type": "string",
            "required": True,
            "description": "Radiologist identifier"
        },
        {
            "name": "nodule_count",
            "xpath": "count(//unblindedReadNodule)",
            "data_type": "int",
            "required": True,
            "description": "Number of nodules"
        },
        {
            "name": "nodule_id",
            "xpath": "//unblindedReadNodule/noduleID",
            "data_type": "string",
            "required": True,
            "description": "Nodule identifier"
        }
    ]
}


# Parse Case Schema Registry
PARSE_CASE_SCHEMAS: Dict[str, Dict[str, List[AttributeDefinition]]] = {
    "Complete_Attributes": COMPLETE_ATTRIBUTES_SCHEMA,
    "LIDC_Single_Session": LIDC_SINGLE_SESSION_SCHEMA,
    "LIDC_Multi_Session_2": LIDC_MULTI_SESSION_2_SCHEMA,
    "LIDC_Multi_Session_3": LIDC_MULTI_SESSION_2_SCHEMA,  # Similar structure
    "LIDC_Multi_Session_4": LIDC_MULTI_SESSION_2_SCHEMA,  # Similar structure
    "With_Reason_Partial": WITH_REASON_PARTIAL_SCHEMA,
    "Core_Attributes_Only": CORE_ATTRIBUTES_ONLY_SCHEMA,
}


def get_expected_attributes(parse_case: str) -> List[AttributeDefinition]:
    """
    Get expected attributes for a parse case

    Args:
        parse_case: Parse case name (e.g., 'Complete_Attributes')

    Returns:
        List of attribute definitions

    Raises:
        KeyError: If parse case is not recognized
    """
    schema = PARSE_CASE_SCHEMAS.get(parse_case)
    if not schema:
        raise KeyError(f"Parse case '{parse_case}' not found in registry")

    return schema["expected_attributes"]


def get_all_parse_cases() -> List[str]:
    """
    Get list of all registered parse case names

    Returns:
        List of parse case names
    """
    return list(PARSE_CASE_SCHEMAS.keys())


def validate_parse_case(parse_case: str) -> bool:
    """
    Check if parse case is registered

    Args:
        parse_case: Parse case name

    Returns:
        True if parse case exists, False otherwise
    """
    return parse_case in PARSE_CASE_SCHEMAS


def get_parse_case_summary(parse_case: str) -> Dict[str, any]:
    """
    Get summary information about a parse case

    Args:
        parse_case: Parse case name

    Returns:
        Dictionary with summary info (total attributes, required count, etc.)
    """
    if not validate_parse_case(parse_case):
        return {"error": f"Parse case '{parse_case}' not found"}

    attributes = get_expected_attributes(parse_case)
    required_count = sum(1 for attr in attributes if attr["required"])

    return {
        "parse_case": parse_case,
        "total_attributes": len(attributes),
        "required_attributes": required_count,
        "optional_attributes": len(attributes) - required_count,
        "attribute_names": [attr["name"] for attr in attributes],
        "required_attribute_names": [attr["name"] for attr in attributes if attr["required"]]
    }
