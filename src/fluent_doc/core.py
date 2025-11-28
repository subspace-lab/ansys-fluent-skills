"""Core module for fetching Ansys Fluent documentation using Playwright.

Key findings from exploration:
1. Must establish session via landing page first (or use wrapped URL)
2. Content is in Frame 1 (iframe)
3. Can navigate directly via iframe.goto() after session established
4. Or use wrapped URL format: /account/secured?returnurl=/Views/Secured/...
5. TOC pages contain all section links - can build dynamic index
6. TOC can be cached as skill references for faster lookups
"""

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page, Frame


# Path to cached TOC references (skill resources)
SKILL_REFERENCES_DIR = Path(__file__).parent.parent.parent / ".claude/skills/fluent-doc/references"


@dataclass
class DocContent:
    """Documentation content container."""
    title: str
    url: str
    content: str
    breadcrumb: list[str]


@dataclass
class TocEntry:
    """Table of contents entry."""
    title: str
    url: str
    section_number: str = ""


# URL mappings for common theory sections
# Note: URLs validated against ansyshelp.ansys.com v252 (2025 R2)
THEORY_URLS = {
    # Theory Guide - Turbulence (Chapter 4)
    "turbulence_overview": "corp/v252/en/flu_th/flu_th_turb.html",
    "k_epsilon": "corp/v252/en/flu_th/flu_th_sec_turb_keps.html",
    "k_epsilon_standard": "corp/v252/en/flu_th/flu_th_sec_turb_ke_std.html",
    "k_omega": "corp/v252/en/flu_th/flu_th_sec_turb_komega.html",
    "k_omega_standard": "corp/v252/en/flu_th/flu_th_sec_turb_kw_std.html",
    "k_omega_sst": "corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html",

    # Theory Guide - Heat Transfer (Chapter 5)
    "heat_transfer": "corp/v252/en/flu_th/flu_th_sec_hxfer_theory.html",
    "natural_convection": "corp/v252/en/flu_th/flu_th_sec_hxfer_buoy.html",

    # Theory Guide - Radiation (Chapter 5.3)
    "radiation_overview": "corp/v252/en/flu_th/flu_th_radiation.html",
    "radiation_do": "corp/v252/en/flu_th/flu_th_sec_mod_disco.html",
    "radiation_s2s": "corp/v252/en/flu_th/flu_th_sec_rad_surface2surface.html",

    # Theory Guide - Other chapters
    "multiphase": "corp/v252/en/flu_th/flu_th_multiphase.html",
    "battery": "corp/v252/en/flu_th/flu_th_battery.html",
    "solver_theory": "corp/v252/en/flu_th/flu_th_solver.html",

    # User's Guide sections
    "user_turbulence": "corp/v252/en/flu_ug/flu_ug_turb.html",
    "user_boundary": "corp/v252/en/flu_ug/flu_ug_bcs.html",
    "user_heat_transfer": "corp/v252/en/flu_ug/flu_ug_sec_hxfer.html",
    "user_radiation": "corp/v252/en/flu_ug/flu_ug_sec_radiation.html",

    # TUI reference
    "tui_define": "corp/v252/en/flu_tcl/flu_tcl_define.html",
    "tui_solve": "corp/v252/en/flu_tcl/flu_tcl_solve.html",
}

# Friendly names for display
SECTION_NAMES = {
    # Turbulence
    "turbulence_overview": "Turbulence (Chapter 4)",
    "k_epsilon": "k-ε Models Overview",
    "k_epsilon_standard": "Standard k-ε Model",
    "k_omega": "k-ω Models Overview",
    "k_omega_standard": "Standard k-ω Model",
    "k_omega_sst": "SST k-ω Model",
    # Heat Transfer
    "heat_transfer": "Heat Transfer Theory (5.2.1)",
    "natural_convection": "Natural Convection & Buoyancy (5.2.2)",
    # Radiation
    "radiation_overview": "Radiation Modeling (Chapter 5.3)",
    "radiation_do": "Discrete Ordinates (DO) Model",
    "radiation_s2s": "Surface-to-Surface (S2S) Model",
    # Other
    "multiphase": "Multiphase Flows (Chapter 14)",
    "battery": "Battery Model (Chapter 19)",
    "solver_theory": "Solver Theory (Chapter 23)",
    # User's Guide
    "user_turbulence": "User's Guide: Turbulence",
    "user_boundary": "User's Guide: Boundary Conditions",
    "user_heat_transfer": "User's Guide: Heat Transfer",
    "user_radiation": "User's Guide: Radiation",
    # TUI
    "tui_define": "TUI: /define commands",
    "tui_solve": "TUI: /solve commands",
}


class FluentDocFetcher:
    """Fetcher for Ansys Fluent documentation.

    Uses Playwright with efficient direct URL navigation after session establishment.
    """

    BASE_URL = "https://ansyshelp.ansys.com"
    LANDING_URL = f"{BASE_URL}/public/Views/Secured/prod_page.html?pn=Fluent&pid=Fluent&lang=en"

    # Guide TOC URLs (version-independent pattern)
    GUIDE_TOCS = {
        "theory": "flu_th/flu_th.html",
        "user": "flu_ug/flu_ug.html",
        "tui": "flu_tcl/flu_tcl.html",
    }

    def __init__(self, headless: bool = False, version: str = "v252"):
        self.headless = headless
        self.version = version
        self._browser = None
        self._context = None
        self._page = None
        self._session_established = False
        self._toc_cache: dict[str, list[TocEntry]] = {}  # Cache for TOC entries

    async def __aenter__(self):
        await self._setup_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup()

    async def _setup_browser(self):
        """Set up browser with stealth settings."""
        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )

        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        self._page = await self._context.new_page()
        await self._page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

    async def _cleanup(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _establish_session(self) -> bool:
        """Establish session by visiting landing page once."""
        if self._session_established:
            return True

        try:
            await self._page.goto(self.LANDING_URL, timeout=90000, wait_until="domcontentloaded")

            # Accept cookies
            try:
                btn = await self._page.query_selector("text=Accept All Cookies")
                if btn: await btn.click()
            except: pass

            await self._page.wait_for_timeout(3000)
            self._session_established = True
            return True

        except Exception as e:
            print(f"Failed to establish session: {e}")
            return False

    def _get_content_frame(self) -> Optional[Frame]:
        """Get the content iframe (Frame 1)."""
        frames = self._page.frames
        return frames[1] if len(frames) > 1 else None

    async def fetch_by_key(self, section_key: str) -> Optional[DocContent]:
        """Fetch a documentation section by its key.

        Args:
            section_key: Key from THEORY_URLS (e.g., 'k_omega_sst', 'battery')

        Returns:
            DocContent with the section content.
        """
        if section_key not in THEORY_URLS:
            print(f"Unknown section: {section_key}")
            print(f"Available: {list(THEORY_URLS.keys())}")
            return None

        if not await self._establish_session():
            return None

        # Navigate iframe directly to the target URL
        content_frame = self._get_content_frame()
        if not content_frame:
            return None

        target_path = THEORY_URLS[section_key]
        target_url = f"{self.BASE_URL}/public//Views/Secured/{target_path}"

        try:
            await content_frame.goto(target_url, timeout=30000, wait_until="domcontentloaded")
            await self._page.wait_for_timeout(3000)

            body = await content_frame.inner_text("body")

            # Check for error pages
            if "page cannot be found" in body.lower() or "PageNotfound" in content_frame.url:
                print(f"ERROR: Page not found for section '{section_key}'")
                print(f"  URL attempted: {target_url}")
                print(f"  This URL mapping may be incorrect - please verify.")
                return None

            # Skip TOC to get main content
            if "PRINT PAGE" in body:
                idx = body.find("PRINT PAGE")
                main_content = body[idx + 10:].strip()
            else:
                main_content = body

            return DocContent(
                title=SECTION_NAMES.get(section_key, section_key),
                url=content_frame.url,
                content=main_content,
                breadcrumb=[SECTION_NAMES.get(section_key, section_key)]
            )

        except Exception as e:
            print(f"Failed to fetch {section_key}: {e}")
            return None

    async def fetch_by_url(self, doc_path: str) -> Optional[DocContent]:
        """Fetch documentation by direct URL path.

        Args:
            doc_path: Path like 'corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html'

        Returns:
            DocContent with the page content.
        """
        if not await self._establish_session():
            return None

        content_frame = self._get_content_frame()
        if not content_frame:
            return None

        target_url = f"{self.BASE_URL}/public//Views/Secured/{doc_path}"

        try:
            await content_frame.goto(target_url, timeout=30000, wait_until="domcontentloaded")
            await self._page.wait_for_timeout(3000)

            body = await content_frame.inner_text("body")

            # Check for error pages
            if "page cannot be found" in body.lower() or "PageNotfound" in content_frame.url:
                print(f"ERROR: Page not found for URL path '{doc_path}'")
                print(f"  URL attempted: {target_url}")
                return None

            if "PRINT PAGE" in body:
                idx = body.find("PRINT PAGE")
                main_content = body[idx + 10:].strip()
            else:
                main_content = body

            # Try to extract title
            title = doc_path.split("/")[-1].replace(".html", "").replace("_", " ").title()

            return DocContent(
                title=title,
                url=content_frame.url,
                content=main_content,
                breadcrumb=[title]
            )

        except Exception as e:
            print(f"Failed to fetch {doc_path}: {e}")
            return None

    async def search(self, query: str) -> Optional[str]:
        """Search documentation using the site's search.

        Args:
            query: Search query

        Returns:
            Search results as text.
        """
        if not await self._establish_session():
            return None

        content_frame = self._get_content_frame()
        if not content_frame:
            return None

        try:
            # Find search input
            search_input = await content_frame.query_selector('input[type="search"], input[placeholder*="search" i]')
            if search_input:
                await search_input.fill(query)
                await search_input.press("Enter")
                await self._page.wait_for_timeout(5000)

                content_frame = self._get_content_frame()
                return await content_frame.inner_text("body")

        except Exception as e:
            print(f"Search failed: {e}")

        return None

    def _load_cached_toc(self, guide: str) -> list[TocEntry]:
        """Load TOC from cached JSON file if available.

        Cached TOC files are stored in skill references directory.
        """
        cache_file = SKILL_REFERENCES_DIR / f"{guide}_toc_{self.version}.json"
        if not cache_file.exists():
            return []

        try:
            with open(cache_file) as f:
                links = json.load(f)

            entries = []
            section_pattern = re.compile(r'^(\d+(?:\.\d+)*\.?)\s+(.+)$')

            for link in links:
                title = link['text']
                url = link['href']

                match = section_pattern.match(title)
                if match:
                    section_num = match.group(1).rstrip('.')
                    section_title = match.group(2)
                else:
                    section_num = ""
                    section_title = title

                entries.append(TocEntry(
                    title=section_title,
                    url=url,
                    section_number=section_num
                ))

            print(f"Loaded cached TOC for {guide}: {len(entries)} entries")
            return entries

        except Exception as e:
            print(f"Failed to load cached TOC: {e}")
            return []

    async def build_toc_index(self, guide: str = "theory") -> list[TocEntry]:
        """Build an index of all sections from a guide's TOC page.

        First checks for cached TOC in skill references, then falls back
        to fetching from Ansys Help if no cache exists.

        Args:
            guide: Guide name - 'theory', 'user', or 'tui'

        Returns:
            List of TocEntry with title and URL for each section.
        """
        # Return in-memory cache if available
        if guide in self._toc_cache:
            return self._toc_cache[guide]

        if guide not in self.GUIDE_TOCS:
            print(f"Unknown guide: {guide}. Available: {list(self.GUIDE_TOCS.keys())}")
            return []

        # Try loading from cached file first (fast path)
        entries = self._load_cached_toc(guide)
        if entries:
            self._toc_cache[guide] = entries
            return entries

        # No cache - fetch from Ansys Help (slow path)
        print(f"No cached TOC found, fetching from Ansys Help...")

        if not await self._establish_session():
            return []

        content_frame = self._get_content_frame()
        if not content_frame:
            return []

        # Build TOC URL for the specified version
        toc_path = f"corp/{self.version}/en/{self.GUIDE_TOCS[guide]}"
        toc_url = f"{self.BASE_URL}/public//Views/Secured/{toc_path}"

        try:
            await content_frame.goto(toc_url, timeout=30000, wait_until="domcontentloaded")
            await self._page.wait_for_timeout(3000)

            # Extract all links using JavaScript
            links = await content_frame.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a').forEach(a => {
                        const text = a.textContent.trim();
                        const href = a.href;
                        if (href && text && href.includes('/flu_') && !href.endsWith('.pdf')) {
                            links.push({ text: text, href: href });
                        }
                    });
                    return links;
                }
            """)

            # Convert to TocEntry objects
            entries = []
            section_pattern = re.compile(r'^(\d+(?:\.\d+)*\.?)\s+(.+)$')

            for link in links:
                title = link['text']
                url = link['href']

                # Extract section number if present
                match = section_pattern.match(title)
                if match:
                    section_num = match.group(1).rstrip('.')
                    section_title = match.group(2)
                else:
                    section_num = ""
                    section_title = title

                entries.append(TocEntry(
                    title=section_title,
                    url=url,
                    section_number=section_num
                ))

            # Cache the results in memory
            self._toc_cache[guide] = entries
            print(f"Built TOC index for {guide}: {len(entries)} entries")
            return entries

        except Exception as e:
            print(f"Failed to build TOC index: {e}")
            return []

    async def find_section(self, query: str, guide: str = "theory") -> Optional[TocEntry]:
        """Find a section by searching the TOC index.

        Args:
            query: Search query (e.g., "SST k-omega", "heat transfer", "radiation")
            guide: Which guide to search - 'theory', 'user', or 'tui'

        Returns:
            Best matching TocEntry or None.
        """
        entries = await self.build_toc_index(guide)
        if not entries:
            return None

        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Score each entry
        scored = []
        for entry in entries:
            title_lower = entry.title.lower()

            # Exact match
            if query_lower == title_lower:
                return entry

            # Calculate score based on word matches
            score = 0
            for word in query_words:
                if word in title_lower:
                    score += 10
                    # Bonus for word at start
                    if title_lower.startswith(word):
                        score += 5

            # Bonus for shorter titles (more specific)
            if score > 0:
                score += 5 / (len(entry.title) / 10)
                scored.append((score, entry))

        if scored:
            scored.sort(key=lambda x: -x[0])
            return scored[0][1]

        return None

    async def fetch_by_search(self, query: str, guide: str = "theory") -> Optional[DocContent]:
        """Fetch documentation by searching the TOC dynamically.

        This is the recommended method as it doesn't rely on hardcoded URLs.

        Args:
            query: Search query (e.g., "SST k-omega model", "natural convection")
            guide: Which guide to search - 'theory', 'user', or 'tui'

        Returns:
            DocContent with the section content.
        """
        entry = await self.find_section(query, guide)
        if not entry:
            print(f"No section found matching '{query}' in {guide} guide")
            return None

        print(f"Found: {entry.section_number} {entry.title}")

        # Extract path from full URL
        # URL format: https://ansyshelp.ansys.com/public//Views/Secured/corp/v252/en/flu_th/...
        url_prefix = f"{self.BASE_URL}/public//Views/Secured/"
        if entry.url.startswith(url_prefix):
            doc_path = entry.url[len(url_prefix):]
        else:
            doc_path = entry.url

        return await self.fetch_by_url(doc_path)


def get_available_sections() -> dict[str, str]:
    """Get available section keys and their names."""
    return SECTION_NAMES.copy()


async def fetch_section(section_key: str, headless: bool = False) -> Optional[DocContent]:
    """Convenience function to fetch a section.

    Args:
        section_key: Key like 'k_omega_sst', 'battery'
        headless: Run headless

    Returns:
        DocContent or None
    """
    async with FluentDocFetcher(headless=headless) as fetcher:
        return await fetcher.fetch_by_key(section_key)


# For backward compatibility with COMMON_PATHS
COMMON_PATHS = {
    "turbulence_overview": ["Fluent Theory Guide", "4. Turbulence"],
    "k_epsilon": ["Fluent Theory Guide", "4. Turbulence", "4.3. Standard, RNG, and Realizable k-ε Models"],
    "k_omega": ["Fluent Theory Guide", "4. Turbulence", "4.4. Standard, BSL, and SST k-ω Models"],
    "k_omega_sst": ["Fluent Theory Guide", "4. Turbulence", "4.4. Standard, BSL, and SST k-ω Models", "4.4.3. SST k-ω Model"],
    "heat_transfer": ["Fluent Theory Guide", "5. Heat Transfer"],
    "multiphase": ["Fluent Theory Guide", "14. Multiphase Flows"],
    "battery": ["Fluent Theory Guide", "19. Battery Model"],
}

# Alias for CLI compatibility
async def fetch_theory_section(section_key: str, headless: bool = False) -> Optional[DocContent]:
    """Alias for fetch_section."""
    return await fetch_section(section_key, headless)


if __name__ == "__main__":
    import sys

    async def main():
        section = sys.argv[1] if len(sys.argv) > 1 else "k_omega_sst"
        print(f"Fetching: {section}")

        result = await fetch_section(section, headless=False)
        if result:
            print(f"\nTitle: {result.title}")
            print(f"URL: {result.url}")
            print(f"\nContent ({len(result.content)} chars):")
            print(result.content[:2000])
        else:
            print("Failed")

    asyncio.run(main())
