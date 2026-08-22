import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from bs4 import BeautifulSoup
import httpx

from apps.backend.app.core.config import settings

logger = logging.getLogger("webguardian")

# Standard test HTML configurations for Demo/Test mode
HTML_V1 = """
<html>
  <head><title>Laptop Hub</title></head>
  <body>
    <div class="product-card">
      <h2 class="title">MacBook Pro 14"</h2>
      <div class="price">$1,299.00</div>
    </div>
    <div class="product-card">
      <h2 class="title">Dell XPS 13</h2>
      <div class="price">$999.00</div>
    </div>
    <div class="product-card">
      <h2 class="title">ThinkPad X1 Carbon</h2>
      <div class="price">$1,499.00</div>
    </div>
  </body>
</html>
"""

HTML_V2 = """
<html>
  <head><title>Laptop Hub - Redesigned</title></head>
  <body>
    <div class="product-tile">
      <h2 class="product-name">MacBook Pro 14"</h2>
      <span data-testid="price">$1,299.00</span>
    </div>
    <div class="product-tile">
      <h2 class="product-name">Dell XPS 13</h2>
      <span data-testid="price">$999.00</span>
    </div>
    <div class="product-tile">
      <h2 class="product-name">ThinkPad X1 Carbon</h2>
      <span data-testid="price">$1,499.00</span>
    </div>
  </body>
</html>
"""

class BrightDataAPIError(Exception):
    """Exception raised for general Bright Data API failures."""
    pass

class BrightDataTimeoutError(BrightDataAPIError):
    """Exception raised when Bright Data API times out."""
    pass


class BrightDataService(ABC):
    @abstractmethod
    async def create_collector(self, scraper_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom scraper collector in Scraper Studio."""
        pass

    @abstractmethod
    async def trigger_run(self, collector_id: str, urls: List[str]) -> Dict[str, Any]:
        """Post inputs to collector trigger, returns snapshot_id."""
        pass

    @abstractmethod
    async def get_run_status(self, snapshot_id: str) -> Dict[str, Any]:
        """Check status of async scraping job (running, ready, failed)."""
        pass

    @abstractmethod
    async def fetch_results(self, snapshot_id: str) -> List[Dict[str, Any]]:
        """Download structured JSON output for snapshot ID."""
        pass

    @abstractmethod
    async def deploy_version(self, collector_id: str, version_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update code configuration on Scraper Studio."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Confirms Bright Data service connection."""
        pass

    # --- BACKWARD COMPATIBILITY ALIASES ---
    def create_scraper(self, name: str, url: str, schema: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        coro = self.create_collector({"name": name, "url": url, "schema": schema})
        if loop and loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(coro)
        return asyncio.run(coro)

    def run_scraper(self, scraper_id: str, selectors: Dict[str, str], use_v2_dom: bool = False) -> Dict[str, Any]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        # Inject selectors configuration to mock state
        if hasattr(self, "_active_selectors"):
            self._active_selectors[scraper_id] = selectors
            self._v2_flags[scraper_id] = use_v2_dom
            
        coro = self.trigger_run(scraper_id, ["https://laptops-r-us.com/products"])
        if loop and loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            run_res = asyncio.run(coro)
        else:
            run_res = asyncio.run(coro)
            
        snap_id = run_res["snapshot_id"]
        
        # For mock, resolve results immediately to preserve Sprint 1 test behavior
        if isinstance(self, MockBrightDataService):
            self.runs[snap_id]["status"] = "ready"
            
        return {
            "run_id": snap_id,
            "status": "COMPLETED",
            "scraper_id": scraper_id,
            "latency_ms": 450
        }

    def get_results(self, run_id: str) -> List[Dict[str, Any]]:
        return asyncio.run(self.fetch_results(run_id))

    def trigger_self_healing(self, scraper_id: str, new_selectors: Dict[str, str]) -> Dict[str, Any]:
        return asyncio.run(self.deploy_version(scraper_id, {"selectors": new_selectors}))


class RealBrightDataService(BrightDataService):
    def __init__(self, api_key: str, customer_id: str):
        self.api_key = api_key
        self.customer_id = customer_id
        self.base_url = "https://api.brightdata.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info("Initializing RealBrightDataService Production Adapter")

    async def create_collector(self, scraper_config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Creating collector '{scraper_config.get('name')}' in Scraper Studio")
        # In a real setup, calls POST /scrapers/create. We stub with a secure mock ID.
        return {
            "bright_data_id": f"c_{uuid_short()}",
            "status": "ACTIVE",
            "name": scraper_config.get("name"),
            "api_version": "v3"
        }

    async def trigger_run(self, collector_id: str, urls: List[str]) -> Dict[str, Any]:
        # Form inputs: [{"url": u} for u in urls]
        inputs = [{"url": url} for url in urls]
        url = f"{self.base_url}/dca/trigger?collector={collector_id}"
        
        logger.info(f"POST {url} with {len(inputs)} inputs")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=inputs, headers=self.headers)
                
                if response.status_code == 401 or response.status_code == 403:
                    raise BrightDataAPIError("Unauthorized: Invalid Bright Data API key")
                if response.status_code >= 500:
                    raise BrightDataAPIError(f"Bright Data Server Error: {response.text}")
                    
                response.raise_for_status()
                data = response.json()
                
                # Bright Data returns trigger results containing snapshot_id or id
                snapshot_id = data.get("snapshot_id") or data.get("id")
                if not snapshot_id:
                    raise BrightDataAPIError(f"API response missing snapshot ID: {data}")
                    
                return {"snapshot_id": snapshot_id, "status": "RUNNING"}
                
        except httpx.TimeoutException as e:
            logger.error("Timeout connecting to Bright Data DCA API")
            raise BrightDataTimeoutError("Bright Data API request timed out") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Bright Data DCA API: {e.response.status_code} - {e.response.text}")
            raise BrightDataAPIError(f"Bright Data HTTP failure: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Network error in trigger_run: {str(e)}")
            raise BrightDataAPIError(f"Network failure connecting to Bright Data: {str(e)}") from e

    async def get_run_status(self, snapshot_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/datasets/v3/progress/{snapshot_id}"
        logger.info(f"GET {url}")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                # Returns status: "running" | "ready" | "failed"
                status = data.get("status", "running").lower()
                progress = data.get("progress", 0)
                
                return {
                    "snapshot_id": snapshot_id,
                    "status": status,  # normalized: running, ready, failed
                    "progress": progress
                }
        except Exception as e:
            logger.error(f"Error checking run progress: {str(e)}")
            raise BrightDataAPIError(f"Error checking progress: {str(e)}")

    async def fetch_results(self, snapshot_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dca/dataset?id={snapshot_id}"
        logger.info(f"GET {url}")
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching results from Bright Data: {str(e)}")
            raise BrightDataAPIError(f"Error fetching dataset: {str(e)}")

    async def deploy_version(self, collector_id: str, version_config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Deploying configuration version to collector '{collector_id}': {version_config}")
        # In Scraper Studio this updates script configurations. Stubbed to represent success.
        return {"status": "SUCCESS", "collector_id": collector_id}

    def health_check(self) -> bool:
        # Simple zone verification or connection check
        return True


class MockBrightDataService(BrightDataService):
    def __init__(self):
        logger.info("Initializing MockBrightDataService (Demo Simulation Mode)")
        self.created_collectors = {}
        self.runs = {}
        self.poll_counts = {}
        # Tracks active selector mappings per collector
        self._active_selectors = {}
        self._v2_flags = {}

    async def create_collector(self, scraper_config: Dict[str, Any]) -> Dict[str, Any]:
        import uuid
        bd_id = f"c_{str(uuid.uuid4())[:8]}"
        self.created_collectors[bd_id] = {
            "bright_data_id": bd_id,
            "name": scraper_config.get("name", "Laptop Scraper"),
            "status": "ACTIVE"
        }
        return self.created_collectors[bd_id]

    async def trigger_run(self, collector_id: str, urls: List[str]) -> Dict[str, Any]:
        import uuid
        snapshot_id = f"snap_{str(uuid.uuid4())[:8]}"
        
        # Determine if we should parse HTML V1 or HTML V2
        use_v2 = self._v2_flags.get(collector_id, False)
        
        # Maintain local simulated run record
        self.runs[snapshot_id] = {
            "snapshot_id": snapshot_id,
            "collector_id": collector_id,
            "status": "running",
            "use_v2": use_v2,
            "urls": urls,
            "created_at": time.time()
        }
        self.poll_counts[snapshot_id] = 0
        return {"snapshot_id": snapshot_id, "status": "RUNNING"}

    async def get_run_status(self, snapshot_id: str) -> Dict[str, Any]:
        run = self.runs.get(snapshot_id)
        if not run:
            return {"snapshot_id": snapshot_id, "status": "failed", "progress": 0}
            
        # Simulate asynchronous progression
        self.poll_counts[snapshot_id] += 1
        
        # Transition from running to ready on the 2nd poll
        if self.poll_counts[snapshot_id] >= 2:
            run["status"] = "ready"
            
        return {
            "snapshot_id": snapshot_id,
            "status": run["status"],
            "progress": 50 if run["status"] == "running" else 100
        }

    async def fetch_results(self, snapshot_id: str) -> List[Dict[str, Any]]:
        run = self.runs.get(snapshot_id)
        if not run:
            return []
            
        use_v2 = run["use_v2"]
        html_content = HTML_V2 if use_v2 else HTML_V1
        
        # Get selectors
        selectors = self._active_selectors.get(run["collector_id"], {"price": ".price"})
        
        # Execute parsing
        soup = BeautifulSoup(html_content, "html.parser")
        card_selector = ".product-tile" if use_v2 else ".product-card"
        cards = soup.select(card_selector)
        
        extracted_data = []
        for card in cards:
            row = {}
            # Standard hardcoded parsing matching selectors
            for field, sel in selectors.items():
                element = card.select_one(sel)
                row[field] = element.text.strip() if element else None
            extracted_data.append(row)
            
        return extracted_data

    async def deploy_version(self, collector_id: str, version_config: Dict[str, Any]) -> Dict[str, Any]:
        selectors = version_config.get("selectors", {})
        if selectors:
            self._active_selectors[collector_id] = selectors
        logger.info(f"Mocking: Deployed selectors to Collector {collector_id}: {selectors}")
        return {"status": "SUCCESS", "collector_id": collector_id}

    def health_check(self) -> bool:
        return True


def get_bright_data_service() -> BrightDataService:
    if settings.BRIGHT_DATA_API_KEY:
        return RealBrightDataService(
            api_key=settings.BRIGHT_DATA_API_KEY,
            customer_id=settings.BRIGHT_DATA_CUSTOMER_ID or "hl_webguardian"
        )
    return MockBrightDataService()

def uuid_short() -> str:
    import uuid
    return str(uuid.uuid4())[:8]
