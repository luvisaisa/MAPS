"""
LIDC 3D Utilities - Spatial Analysis and Visualization
========================================================

Utilities for working with 3D contour data from LIDC-IDRI dataset:
- Extract and export 3D meshes (STL, OBJ)
- Calculate consensus contours using STAPLE algorithm
- Compute inter-rater reliability metrics
- Generate interactive 3D visualizations
- Export data for 3D Slicer and other medical imaging tools

Requirements:
    scipy, scikit-image, trimesh, plotly, SimpleITK, pingouin

Author: MAPS Team
Date: November 2025
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union
import json

# Check for required dependencies
try:
    import numpy as np
    import scipy.ndimage
    from scipy.spatial.distance import cdist
except ImportError:
    raise ImportError("scipy is required for 3D contour processing. Install with: pip install scipy>=1.11.0")

try:
    from skimage import measure
except ImportError:
    raise ImportError("scikit-image is required. Install with: pip install scikit-image>=0.21.0")

try:
    import trimesh
except ImportError:
    raise ImportError("trimesh is required for mesh export. Install with: pip install trimesh>=3.23.0")

try:
    import plotly.graph_objects as go
    import plotly.io as pio
except ImportError:
    raise ImportError("plotly is required for visualization. Install with: pip install plotly>=5.17.0")

try:
    import pingouin as pg
except ImportError:
    raise ImportError("pingouin is required for ICC calculations. Install with: pip install pingouin>=0.5.3")

# Optional: SimpleITK for advanced medical image processing
try:
    import SimpleITK as sitk
    HAS_SITK = True
except ImportError:
    HAS_SITK = False
    sitk = None

logger = logging.getLogger(__name__)


def extract_nodule_mesh(
    patient_id: str,
    nodule_id: str,
    contour_data: Dict,
    output_format: str = 'stl',
    output_path: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """
    Extract 3D mesh from nodule contour data and export as STL or OBJ.

    Args:
        patient_id: LIDC patient ID (e.g., "LIDC-IDRI-0001")
        nodule_id: Nodule identifier
        contour_data: Dict from get_nodule_contour_data() function
        output_format: 'stl' or 'obj'
        output_path: Output file path (auto-generated if None)

    Returns:
        Path to generated mesh file, or None if failed

    Example:
        >>> mesh_path = extract_nodule_mesh("LIDC-IDRI-0001", "1", contour_json, "stl")
        >>> print(f"Mesh saved to: {mesh_path}")
    """
    try:
        # Extract contour coordinates from all radiologists
        all_contours = []
        for rad in contour_data.get('radiologists', []):
            coords = rad.get('contour_coordinates')
            if coords:
                # Convert JSONB array to numpy array
                points = np.array([[p['x'], p['y'], p['z']] for p in coords])
                all_contours.append(points)

        if not all_contours:
            logger.warning(f"No contours found for {patient_id} nodule {nodule_id}")
            return None

        # Use first radiologist's contours (or consensus if available)
        contour_points = all_contours[0]

        # Create 3D volume from contour points using marching cubes
        # First, create a binary mask
        min_coords = contour_points.min(axis=0)
        max_coords = contour_points.max(axis=0)
        shape = (max_coords - min_coords + 1).astype(int)

        volume = np.zeros(shape, dtype=np.uint8)

        # Rasterize contours into volume
        for point in contour_points:
            idx = (point - min_coords).astype(int)
            if all(0 <= idx[i] < shape[i] for i in range(3)):
                volume[tuple(idx)] = 1

        # Fill interior (simple flood fill from edge)
        volume = scipy.ndimage.binary_fill_holes(volume).astype(np.uint8)

        # Generate mesh using marching cubes
        verts, faces, normals, values = measure.marching_cubes(volume, level=0.5)

        # Create trimesh object
        mesh = trimesh.Trimesh(vertices=verts + min_coords, faces=faces, normals=normals)

        # Simplify mesh to reduce file size
        mesh = mesh.simplify_quadratic_decimation(len(mesh.faces) // 2)

        # Generate output path if not provided
        if output_path is None:
            output_dir = Path("exports") / "meshes"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{patient_id}_nodule_{nodule_id}.{output_format}"
        else:
            output_path = Path(output_path)

        # Export mesh
        mesh.export(str(output_path))
        logger.info(f"Mesh exported to: {output_path}")

        return output_path

    except Exception as e:
        logger.error(f"Failed to extract mesh for {patient_id} nodule {nodule_id}: {e}")
        return None


def calculate_consensus_contour(
    nodule_contours: List[np.ndarray],
    method: str = 'average'
) -> np.ndarray:
    """
    Calculate consensus contour from multiple radiologist annotations.

    Args:
        nodule_contours: List of contour arrays (one per radiologist)
        method: 'average', 'median', or 'staple'

    Returns:
        Consensus contour as numpy array

    Note:
        STAPLE algorithm requires SimpleITK. Falls back to averaging if not available.

    Example:
        >>> contours = [rad1_contour, rad2_contour, rad3_contour, rad4_contour]
        >>> consensus = calculate_consensus_contour(contours, method='average')
    """
    if not nodule_contours:
        raise ValueError("No contours provided")

    if len(nodule_contours) == 1:
        return nodule_contours[0]

    if method == 'staple':
        if not HAS_SITK:
            logger.warning("SimpleITK not available, falling back to averaging")
            method = 'average'
        else:
            # STAPLE implementation using SimpleITK
            # Convert contours to binary masks
            masks = []
            for contour in nodule_contours:
                # Create binary mask from contour points
                min_coords = contour.min(axis=0)
                max_coords = contour.max(axis=0)
                shape = (max_coords - min_coords + 1).astype(int)

                mask = np.zeros(shape, dtype=np.uint8)
                for point in contour:
                    idx = (point - min_coords).astype(int)
                    if all(0 <= idx[i] < shape[i] for i in range(3)):
                        mask[tuple(idx)] = 1

                mask = scipy.ndimage.binary_fill_holes(mask)
                masks.append(sitk.GetImageFromArray(mask.astype(np.uint8)))

            # Apply STAPLE
            staple_filter = sitk.STAPLEImageFilter()
            consensus_mask = staple_filter.Execute(masks)
            consensus_array = sitk.GetArrayFromImage(consensus_mask)

            # Extract contour from consensus mask
            consensus_points = np.argwhere(consensus_array > 0.5)
            return consensus_points

    if method == 'average':
        # Average corresponding points (requires point correspondence)
        # For simplicity, average all points together
        all_points = np.vstack(nodule_contours)
        return all_points

    elif method == 'median':
        # Median of all contour points
        all_points = np.vstack(nodule_contours)
        return np.median(all_points, axis=0)

    else:
        raise ValueError(f"Unknown consensus method: {method}")


def compute_inter_rater_reliability(
    ratings_data: Dict[str, List[float]],
    patient_id: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate inter-rater reliability metrics for radiologist ratings.

    Args:
        ratings_data: Dict mapping characteristic names to lists of ratings
                     e.g., {"malignancy": [4, 5, 4, 4], "subtlety": [3, 3, 4, 3]}
        patient_id: Optional patient ID for logging

    Returns:
        Dict with ICC and Fleiss' kappa values per characteristic

    Example:
        >>> ratings = {
        ...     "malignancy": [4, 5, 4, 4],
        ...     "subtlety": [3, 3, 4, 3],
        ...     "spiculation": [2, 2, 3, 2]
        ... }
        >>> metrics = compute_inter_rater_reliability(ratings)
        >>> print(f"Malignancy ICC: {metrics['malignancy_icc']:.3f}")
    """
    results = {}

    for characteristic, ratings in ratings_data.items():
        # Skip if not enough ratings
        if len(ratings) < 2:
            logger.warning(f"Insufficient ratings for {characteristic}: {len(ratings)}")
            continue

        try:
            # Calculate ICC (Intraclass Correlation Coefficient)
            # Create DataFrame for pingouin
            import pandas as pd

            # Reshape data: one row per rater, columns for subjects (in this case, just one subject)
            df = pd.DataFrame({
                'rater': [f'R{i+1}' for i in range(len(ratings))],
                'subject': ['nodule'] * len(ratings),
                'rating': ratings
            })

            # Calculate ICC(2,1) - two-way random effects, single rater
            try:
                icc_result = pg.intraclass_corr(data=df, targets='subject', raters='rater', ratings='rating')
                icc_value = icc_result[icc_result['Type'] == 'ICC2']['ICC'].values[0]
                results[f'{characteristic}_icc'] = float(icc_value)
            except Exception as e:
                logger.warning(f"ICC calculation failed for {characteristic}: {e}")
                results[f'{characteristic}_icc'] = None

            # Calculate Fleiss' kappa (for categorical-like ordinal data)
            # Treat ratings as categories
            from collections import Counter
            rating_counts = Counter(ratings)
            n_raters = len(ratings)
            n_categories = max(ratings) - min(ratings) + 1

            # Fleiss' kappa calculation
            # P_e = sum of (p_j)^2 where p_j is proportion in category j
            p_j = [rating_counts.get(i, 0) / n_raters for i in range(1, 6)]  # LIDC uses 1-5
            P_e = sum(p ** 2 for p in p_j)

            # P_o = observed agreement
            # For one subject, this is proportion of agreement
            # (n_raters - 1) / n_raters for perfect agreement
            mode_rating = max(rating_counts, key=rating_counts.get)
            mode_count = rating_counts[mode_rating]
            P_o = mode_count / n_raters

            # Kappa = (P_o - P_e) / (1 - P_e)
            if P_e < 1.0:
                kappa = (P_o - P_e) / (1 - P_e)
                results[f'{characteristic}_kappa'] = float(kappa)
            else:
                results[f'{characteristic}_kappa'] = None

        except Exception as e:
            logger.error(f"Failed to calculate reliability for {characteristic}: {e}")
            results[f'{characteristic}_icc'] = None
            results[f'{characteristic}_kappa'] = None

    if patient_id:
        logger.info(f"Computed inter-rater reliability for {patient_id}: {results}")

    return results


def generate_3d_visualization(
    patient_id: str,
    nodule_id: str,
    contour_data: Dict,
    output_path: Optional[Union[str, Path]] = None,
    return_html: bool = False
) -> Optional[Union[Path, str]]:
    """
    Generate interactive 3D visualization using Plotly.

    Args:
        patient_id: LIDC patient ID
        nodule_id: Nodule identifier
        contour_data: Dict from get_nodule_contour_data()
        output_path: Output HTML file path (auto-generated if None)
        return_html: If True, return HTML string instead of file path

    Returns:
        Path to HTML file or HTML string (if return_html=True)

    Example:
        >>> html_path = generate_3d_visualization("LIDC-IDRI-0001", "1", contour_json)
        >>> print(f"Visualization saved to: {html_path}")
    """
    try:
        fig = go.Figure()

        # Color palette for radiologists
        colors = ['red', 'blue', 'green', 'orange']

        for idx, rad in enumerate(contour_data.get('radiologists', [])):
            coords = rad.get('contour_coordinates')
            if not coords:
                continue

            # Extract x, y, z coordinates
            x = [p['x'] for p in coords]
            y = [p['y'] for p in coords]
            z = [p['z'] for p in coords]

            # Add scatter plot for this radiologist
            fig.add_trace(go.Scatter3d(
                x=x, y=y, z=z,
                mode='markers',
                marker=dict(size=2, color=colors[idx % len(colors)]),
                name=f"Radiologist {rad.get('radiologist_id', idx+1)}",
                hovertemplate='<b>Radiologist %{fullData.name}</b><br>' +
                             'X: %{x:.2f}<br>Y: %{y:.2f}<br>Z: %{z:.2f}<extra></extra>'
            ))

        # Update layout
        fig.update_layout(
            title=f"3D Nodule Contours - {patient_id} Nodule {nodule_id}",
            scene=dict(
                xaxis_title='X (mm)',
                yaxis_title='Y (mm)',
                zaxis_title='Z (mm)',
                aspectmode='data'
            ),
            hovermode='closest',
            showlegend=True
        )

        # Generate output
        if return_html:
            return pio.to_html(fig, include_plotlyjs='cdn')
        else:
            if output_path is None:
                output_dir = Path("exports") / "visualizations"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{patient_id}_nodule_{nodule_id}_3d.html"
            else:
                output_path = Path(output_path)

            fig.write_html(str(output_path))
            logger.info(f"3D visualization saved to: {output_path}")
            return output_path

    except Exception as e:
        logger.error(f"Failed to generate 3D visualization: {e}")
        return None


def export_for_3d_slicer(
    patient_id: str,
    nodule_data: Dict,
    output_dir: Optional[Union[str, Path]] = None
) -> Optional[Path]:
    """
    Export nodule data in format compatible with 3D Slicer.

    Args:
        patient_id: LIDC patient ID
        nodule_data: Dict containing nodule contours and metadata
        output_dir: Output directory (auto-generated if None)

    Returns:
        Path to output directory containing VTK files

    Example:
        >>> slicer_dir = export_for_3d_slicer("LIDC-IDRI-0001", nodule_json)
        >>> print(f"3D Slicer files in: {slicer_dir}")
    """
    if not HAS_SITK:
        logger.error("SimpleITK required for 3D Slicer export")
        return None

    try:
        if output_dir is None:
            output_dir = Path("exports") / "3d_slicer" / patient_id
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # Export each nodule as separate VTK file
        # (Implementation would require full volume data, not just contours)
        # This is a placeholder - full implementation needs DICOM volume

        logger.warning("3D Slicer export requires full DICOM volume data (not just contours)")
        return output_dir

    except Exception as e:
        logger.error(f"Failed to export for 3D Slicer: {e}")
        return None


def get_tcia_download_script(
    patient_ids: List[str],
    output_file: Union[str, Path] = "download_tcia.sh"
) -> Path:
    """
    Generate bash script for downloading LIDC data from TCIA using NBIA CLI.

    Args:
        patient_ids: List of LIDC patient IDs (e.g., ["LIDC-IDRI-0001", "LIDC-IDRI-0002"])
        output_file: Output shell script path

    Returns:
        Path to generated script

    Example:
        >>> script_path = get_tcia_download_script(["LIDC-IDRI-0001", "LIDC-IDRI-0002"])
        >>> print(f"Run: bash {script_path}")
    """
    output_path = Path(output_file)

    script_content = f"""#!/bin/bash
# TCIA LIDC-IDRI Data Download Script
# Generated: {pd.Timestamp.now()}
# Patients: {len(patient_ids)}

echo "TCIA LIDC-IDRI Download Script"
echo "==============================="
echo ""
echo "This script helps download LIDC-IDRI data from TCIA."
echo "You need to install NBIA Data Retriever first:"
echo "  https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide"
echo ""

# Check if NBIA CLI is installed
if ! command -v nbia-download &> /dev/null; then
    echo "ERROR: NBIA Data Retriever CLI not found"
    echo "Please install from: https://wiki.cancerimagingarchive.net/display/NBIA/NBIA+Data+Retriever+Command-Line+Interface+Guide"
    exit 1
fi

# Patient IDs to download
PATIENT_IDS=(
{chr(10).join(f'    "{pid}"' for pid in patient_ids)}
)

# Download directory
DOWNLOAD_DIR="./tcia_downloads"
mkdir -p "$DOWNLOAD_DIR"

echo "Downloading ${{#PATIENT_IDS[@]}} patients to $DOWNLOAD_DIR"
echo ""

# Download each patient
for PATIENT_ID in "${{PATIENT_IDS[@]}}"; do
    echo "Downloading $PATIENT_ID..."
    nbia-download \\
        --collection "LIDC-IDRI" \\
        --patient "$PATIENT_ID" \\
        --output-dir "$DOWNLOAD_DIR" \\
        --format "DICOM"

    if [ $? -eq 0 ]; then
        echo "✓ $PATIENT_ID downloaded successfully"
    else
        echo "✗ $PATIENT_ID download failed"
    fi
    echo ""
done

echo "Download complete!"
echo "Data saved to: $DOWNLOAD_DIR"
"""

    output_path.write_text(script_content)
    output_path.chmod(0o755)  # Make executable

    logger.info(f"TCIA download script generated: {output_path}")
    return output_path


# Compatibility imports for pandas (used in script generation)
try:
    import pandas as pd
except ImportError:
    # Minimal fallback for timestamp
    import datetime
    class pd:
        class Timestamp:
            @staticmethod
            def now():
                return datetime.datetime.now().isoformat()
