"""
Integration Smoke Test — Live Copernicus Data Space STAC Endpoint
Marked as external/optional. Tests live discovery over Central India if internet is available.
"""

import pytest
import requests
from exploration.stac_provider import STACProvider
from exploration.schemas import ExploreSearchRequest


@pytest.mark.external
def test_live_copernicus_stac_discovery():
    try:
        resp = requests.get("https://stac.dataspace.copernicus.eu/v1", timeout=4.0)
        if resp.status_code != 200:
            pytest.skip("Copernicus STAC endpoint returned non-200 status")
    except Exception as e:
        pytest.skip(f"Internet or Copernicus STAC unreachable: {e}")

    provider = STACProvider()
    req = ExploreSearchRequest(
        bbox=[78.5, 20.5, 79.5, 21.5],  # Nagpur / Vidarbha region
        datetime_start="2026-06-01T00:00:00Z",
        datetime_end="2026-09-01T23:59:59Z",
        limit=3,
    )
    items = provider.search(req)
    assert isinstance(items, list)
    print(f"\n[Live STAC] Discovered {len(items)} items over Central India.")
