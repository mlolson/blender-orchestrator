"""Poly Haven API client for free CC0 assets.

Poly Haven provides free HDRIs, textures, and 3D models.
All assets are CC0 licensed (public domain).

API: https://api.polyhaven.com
"""

import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

import httpx


class AssetType(Enum):
    """Poly Haven asset types."""
    HDRI = "hdris"
    TEXTURE = "textures"
    MODEL = "models"


@dataclass
class PolyHavenAsset:
    """Information about a Poly Haven asset."""
    id: str
    name: str
    asset_type: AssetType
    categories: List[str]
    tags: List[str]
    thumbnail_url: str
    download_count: int
    max_resolution: tuple


@dataclass
class DownloadResult:
    """Result of downloading an asset."""
    asset_id: str
    asset_type: str
    local_path: str
    file_format: str
    resolution: str


class PolyHavenClient:
    """Client for the Poly Haven API.
    
    No API key required - all assets are free CC0.
    """

    BASE_URL = "https://api.polyhaven.com"
    CDN_URL = "https://dl.polyhaven.org/file/ph-assets"

    def __init__(self, timeout: int = 60):
        """Initialize the client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    async def list_assets(
        self,
        asset_type: Optional[AssetType] = None,
        categories: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 20,
    ) -> List[PolyHavenAsset]:
        """List available assets with optional filtering.
        
        Args:
            asset_type: Filter by type (HDRI, TEXTURE, MODEL)
            categories: Filter by categories (e.g., ["outdoor", "nature"])
            search: Search term for name/tags
            limit: Maximum results to return
            
        Returns:
            List of matching assets
        """
        params = {}
        if asset_type:
            params["type"] = asset_type.value
            
        if categories:
            params["categories"] = ",".join(categories)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.BASE_URL}/assets",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        # Convert to asset objects
        assets = []
        for asset_id, info in data.items():
            # Determine asset type from API response
            type_map = {0: AssetType.HDRI, 1: AssetType.TEXTURE, 2: AssetType.MODEL}
            a_type = type_map.get(info.get("type", 1), AssetType.TEXTURE)
            
            # Skip if filtering by type and doesn't match
            if asset_type and a_type != asset_type:
                continue
                
            # Search filter
            if search:
                search_lower = search.lower()
                name_match = search_lower in info.get("name", "").lower()
                tag_match = any(search_lower in t.lower() for t in info.get("tags", []))
                cat_match = any(search_lower in c.lower() for c in info.get("categories", []))
                if not (name_match or tag_match or cat_match):
                    continue

            asset = PolyHavenAsset(
                id=asset_id,
                name=info.get("name", asset_id),
                asset_type=a_type,
                categories=info.get("categories", []),
                tags=info.get("tags", []),
                thumbnail_url=info.get("thumbnail_url", ""),
                download_count=info.get("download_count", 0),
                max_resolution=tuple(info.get("max_resolution", [1024, 1024])),
            )
            assets.append(asset)
            
            if len(assets) >= limit:
                break

        # Sort by download count (popularity)
        assets.sort(key=lambda x: x.download_count, reverse=True)
        return assets[:limit]

    async def get_categories(
        self,
        asset_type: AssetType,
    ) -> Dict[str, int]:
        """Get available categories for an asset type.
        
        Args:
            asset_type: Type of assets
            
        Returns:
            Dict mapping category name to asset count
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.BASE_URL}/categories/{asset_type.value}",
            )
            response.raise_for_status()
            return response.json()

    async def get_asset_files(
        self,
        asset_id: str,
    ) -> Dict[str, Any]:
        """Get available files for an asset.
        
        Args:
            asset_id: The asset ID/slug
            
        Returns:
            File tree with download URLs
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.BASE_URL}/files/{asset_id}",
            )
            response.raise_for_status()
            return response.json()

    async def download_hdri(
        self,
        asset_id: str,
        resolution: str = "2k",
        file_format: str = "hdr",
        output_dir: Optional[str] = None,
    ) -> DownloadResult:
        """Download an HDRI asset.
        
        Args:
            asset_id: The asset ID
            resolution: Resolution (1k, 2k, 4k, 8k)
            file_format: Format (hdr, exr)
            output_dir: Directory to save to (uses temp if None)
            
        Returns:
            DownloadResult with local path
        """
        files = await self.get_asset_files(asset_id)
        
        # Navigate to the file URL
        hdri_data = files.get("hdri", {})
        res_data = hdri_data.get(resolution, {})
        format_data = res_data.get(file_format, {})
        
        url = format_data.get("url")
        if not url:
            # Fallback: try to construct URL
            url = f"{self.CDN_URL}/HDRIs/{asset_id}/{asset_id}_{resolution}.{file_format}"

        return await self._download_file(
            url=url,
            asset_id=asset_id,
            asset_type="hdri",
            file_format=file_format,
            resolution=resolution,
            output_dir=output_dir,
        )

    async def download_texture(
        self,
        asset_id: str,
        resolution: str = "2k",
        texture_type: str = "diffuse",
        file_format: str = "jpg",
        output_dir: Optional[str] = None,
    ) -> DownloadResult:
        """Download a texture asset.
        
        Args:
            asset_id: The asset ID
            resolution: Resolution (1k, 2k, 4k, 8k)
            texture_type: Map type (diffuse, nor_gl, rough, disp, arm)
            file_format: Format (jpg, png, exr)
            output_dir: Directory to save to
            
        Returns:
            DownloadResult with local path
        """
        # Map common names to Poly Haven names
        type_map = {
            "diffuse": "diffuse",
            "diff": "diffuse",
            "color": "diffuse",
            "albedo": "diffuse",
            "normal": "nor_gl",
            "nor": "nor_gl",
            "roughness": "rough",
            "rough": "rough",
            "displacement": "disp",
            "disp": "disp",
            "height": "disp",
            "arm": "arm",  # AO/Rough/Metal packed
        }
        ph_type = type_map.get(texture_type.lower(), texture_type)

        files = await self.get_asset_files(asset_id)
        
        # Navigate to the file
        tex_data = files.get(ph_type, {})
        res_data = tex_data.get(resolution, {})
        format_data = res_data.get(file_format, {})
        
        url = format_data.get("url")
        if not url:
            # Fallback: construct URL
            url = f"{self.CDN_URL}/Textures/{asset_id}/{resolution}/{asset_id}_{ph_type}_{resolution}.{file_format}"

        return await self._download_file(
            url=url,
            asset_id=asset_id,
            asset_type="texture",
            file_format=file_format,
            resolution=resolution,
            output_dir=output_dir,
        )

    async def download_model(
        self,
        asset_id: str,
        file_format: str = "gltf",
        resolution: str = "2k",
        output_dir: Optional[str] = None,
    ) -> DownloadResult:
        """Download a 3D model asset.
        
        Args:
            asset_id: The asset ID
            file_format: Format (gltf, fbx, blend)
            resolution: Texture resolution for the model
            output_dir: Directory to save to
            
        Returns:
            DownloadResult with local path
        """
        files = await self.get_asset_files(asset_id)
        
        # Navigate to model files
        format_data = files.get(file_format, {})
        res_data = format_data.get(resolution, {})
        
        url = res_data.get("url")
        if not url and file_format in format_data:
            # Some models have the URL directly
            url = format_data[file_format].get("url")

        if not url:
            # Fallback
            ext = "glb" if file_format == "gltf" else file_format
            url = f"{self.CDN_URL}/Models/{asset_id}/{file_format}/{asset_id}_{resolution}.{ext}"

        return await self._download_file(
            url=url,
            asset_id=asset_id,
            asset_type="model",
            file_format=file_format,
            resolution=resolution,
            output_dir=output_dir,
        )

    async def download_pbr_textures(
        self,
        asset_id: str,
        resolution: str = "2k",
        output_dir: Optional[str] = None,
    ) -> Dict[str, DownloadResult]:
        """Download all PBR texture maps for an asset.
        
        Args:
            asset_id: The asset ID
            resolution: Resolution for all maps
            output_dir: Directory to save to
            
        Returns:
            Dict mapping texture type to DownloadResult
        """
        texture_types = ["diffuse", "normal", "roughness", "displacement"]
        results = {}
        
        for tex_type in texture_types:
            try:
                result = await self.download_texture(
                    asset_id=asset_id,
                    resolution=resolution,
                    texture_type=tex_type,
                    output_dir=output_dir,
                )
                results[tex_type] = result
            except Exception:
                # Not all textures have all map types
                pass

        return results

    async def _download_file(
        self,
        url: str,
        asset_id: str,
        asset_type: str,
        file_format: str,
        resolution: str,
        output_dir: Optional[str] = None,
    ) -> DownloadResult:
        """Download a file to local storage.
        
        Args:
            url: Download URL
            asset_id: Asset identifier
            asset_type: Type of asset
            file_format: File format/extension
            resolution: Resolution string
            output_dir: Output directory
            
        Returns:
            DownloadResult with local path
        """
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            local_path = str(Path(output_dir) / f"{asset_id}_{resolution}.{file_format}")
        else:
            local_path = tempfile.mktemp(
                suffix=f".{file_format}",
                prefix=f"polyhaven_{asset_id}_",
            )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            with open(local_path, "wb") as f:
                f.write(response.content)

        return DownloadResult(
            asset_id=asset_id,
            asset_type=asset_type,
            local_path=local_path,
            file_format=file_format,
            resolution=resolution,
        )
