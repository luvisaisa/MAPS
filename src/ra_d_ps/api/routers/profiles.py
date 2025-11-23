"""
Profiles Router

Endpoints for profile management with ProfileManager integration.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging

from ...profile_manager import ProfileManager, get_profile_manager
from ...schemas.profile import Profile, profile_to_dict
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class ProfileCreateRequest(BaseModel):
    """Request model for profile creation"""
    profile_name: str
    file_type: str
    description: Optional[str] = None
    mappings: List[dict]
    validation_rules: Optional[dict] = None
    transformations: Optional[dict] = None


class ProfileUpdateRequest(BaseModel):
    """Request model for profile updates"""
    description: Optional[str] = None
    mappings: Optional[List[dict]] = None
    validation_rules: Optional[dict] = None
    transformations: Optional[dict] = None


@router.get("")
async def list_profiles(
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> List[dict]:
    """
    List all available profiles.

    Returns:
        List of profile dictionaries with metadata
    """
    try:
        profiles = profile_manager.list_profiles()
        return [profile_to_dict(p) for p in profiles]
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list profiles: {str(e)}")


@router.get("/{name}")
async def get_profile(
    name: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> dict:
    """
    Get specific profile by name.

    Args:
        name: Profile name

    Returns:
        Profile dictionary

    Raises:
        404: Profile not found
    """
    try:
        profile = profile_manager.load_profile(name)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
        return profile_to_dict(profile)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.post("")
async def create_profile(
    request: ProfileCreateRequest,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> dict:
    """
    Create a new profile.

    Args:
        request: Profile creation request

    Returns:
        Created profile dictionary

    Raises:
        400: Invalid profile data
        409: Profile already exists
    """
    try:
        # Check if profile already exists
        existing = profile_manager.load_profile(request.profile_name)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Profile '{request.profile_name}' already exists"
            )

        # Create profile dictionary
        profile_data = {
            "profile_name": request.profile_name,
            "file_type": request.file_type,
            "description": request.description or "",
            "mappings": request.mappings,
            "validation_rules": request.validation_rules or {"required_fields": []},
            "transformations": request.transformations or {}
        }

        # Validate and save
        is_valid, errors = profile_manager.validate_profile_dict(profile_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid profile: {'; '.join(errors)}"
            )

        # Save profile
        success = profile_manager.save_profile_dict(profile_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save profile")

        # Return saved profile
        saved_profile = profile_manager.load_profile(request.profile_name)
        return profile_to_dict(saved_profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {str(e)}")


@router.put("/{name}")
async def update_profile(
    name: str,
    request: ProfileUpdateRequest,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> dict:
    """
    Update an existing profile.

    Args:
        name: Profile name
        request: Profile update request

    Returns:
        Updated profile dictionary

    Raises:
        404: Profile not found
        400: Invalid profile data
    """
    try:
        # Load existing profile
        existing = profile_manager.load_profile(name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")

        # Convert to dict and update
        profile_data = profile_to_dict(existing)

        if request.description is not None:
            profile_data["description"] = request.description
        if request.mappings is not None:
            profile_data["mappings"] = request.mappings
        if request.validation_rules is not None:
            profile_data["validation_rules"] = request.validation_rules
        if request.transformations is not None:
            profile_data["transformations"] = request.transformations

        # Validate
        is_valid, errors = profile_manager.validate_profile_dict(profile_data)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid profile: {'; '.join(errors)}"
            )

        # Save
        success = profile_manager.save_profile_dict(profile_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save profile")

        # Return updated profile
        updated_profile = profile_manager.load_profile(name)
        return profile_to_dict(updated_profile)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update profile '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.delete("/{name}")
async def delete_profile(
    name: str,
    profile_manager: ProfileManager = Depends(get_profile_manager)
) -> dict:
    """
    Delete a profile.

    Args:
        name: Profile name

    Returns:
        Success message

    Raises:
        404: Profile not found
    """
    try:
        # Check if profile exists
        existing = profile_manager.load_profile(name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")

        # Delete profile
        success = profile_manager.delete_profile(name)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete profile")

        return {"status": "success", "message": f"Profile '{name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile '{name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")
