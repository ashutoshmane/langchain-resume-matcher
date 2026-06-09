"""Web/URL document loader with LinkedIn special-case handling.

LinkedIn has crawling terms that prohibit automated scraping. This module
provides a best-effort fetch with a clear fallback path to manual paste.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from langchain_core.documents import Document
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)

LINKEDIN_DOMAINS = {"linkedin.com", "www.linkedin.com"}


class WebPageLoader:
    """Load a public web page and return a LangChain Document.

    LinkedIn URLs receive special treatment: we attempt a polite fetch with
    a descriptive User‑Agent, but if the response is blocked, incomplete, or
    a login wall we raise an exception so the caller can prompt the user to
    paste the job description manually.
    """

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def load(self, url: str) -> Document:
        """Fetch *url* and return a Document with page text and metadata.

        Raises
        ------
        LinkedInBlockedError
            When a LinkedIn URL returns a non‑public page.
        httpx.HTTPError
            On network or HTTP errors.
        """
        is_linkedin = self._is_linkedin_url(url)
        headers = self._build_headers(is_linkedin)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            if is_linkedin:
                self._validate_linkedin_response(response)

            raw_html = response.text
            logger.info("Fetched URL %s: %d bytes of HTML (before JS removal)", url, len(raw_html))
            # Strip JavaScript (<script> tags) from the raw HTML
            raw_html = self._strip_javascript(raw_html)
            logger.info("Fetched URL %s: %d bytes of HTML (after JS removal)", url, len(raw_html))

            text = self._extract_text(raw_html)

            if not text or len(text.strip()) < 50:
                logger.warning(
                    "Extracted text too short (%d chars). Passing raw HTML (%d bytes) to LLM for extraction.",
                    len(text.strip()) if text else 0,
                    len(raw_html),
                )
                text = raw_html

        metadata = {
            "source": url,
            "is_linkedin": is_linkedin,
            "content_type": response.headers.get("content-type", ""),
        }
        return Document(page_content=text, metadata=metadata)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_javascript(html: str) -> str:
        """Remove all JavaScript from HTML content.

        Strips <script> tags, inline event handlers (on* attributes),
        and javascript: URLs to reduce noise for text extraction.
        """
        soup = BeautifulSoup(html, "lxml")

        # Remove all <script> tags
        for tag in soup.find_all("script"):
            tag.decompose()

        # Remove inline event handlers (onclick, onload, etc.)
        for tag in soup.find_all(True):
            attrs_to_remove = [attr for attr in tag.attrs if attr.startswith("on")]
            for attr in attrs_to_remove:
                del tag[attr]

        return str(soup)

    @staticmethod
    def _is_linkedin_url(url: str) -> bool:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.hostname in LINKEDIN_DOMAINS

    @staticmethod
    def _build_headers(is_linkedin: bool) -> dict[str, str]:
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": settings.linkedin_user_agent,
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        return headers

    def _validate_linkedin_response(self, response: httpx.Response) -> None:
        """Heuristic checks that we actually got a public job page."""
        text_lower = response.text.lower()

        # Common LinkedIn blocking signals
        if len(response.text) < 2000:
            raise LinkedInBlockedError(
                "LinkedIn returned very little content — likely blocked or a login wall. "
                "Please paste the job description text directly."
            )
        if any(phrase in text_lower for phrase in [
            "sign in", "login", "join linkedin", "verify you are human",
            "unusual activity", "security check",
        ]):
            raise LinkedInBlockedError(
                "LinkedIn returned a sign‑in or verification page. "
                "Please paste the job description text directly."
            )

    @staticmethod
    def _extract_text(html: str) -> str:
        import re

        soup = BeautifulSoup(html, "lxml")

        # Strategy 1: Look for job-posting-specific containers first
        job_selectors = [
            soup.find("main"),
            soup.find("article"),
            soup.find(attrs={"class": re.compile(r"job|career|posting|description", re.I)}),
            soup.find(attrs={"id": re.compile(r"job|career|posting|description", re.I)}),
        ]
        for container in job_selectors:
            if container:
                # Remove noisy elements inside the container
                for tag in container(["script", "style", "noscript"]):
                    tag.decompose()
                text = container.get_text(separator="\n", strip=True)
                if len(text) > 100:
                    logger.info("Extracted %d chars using targeted container", len(text))
                    return re.sub(r"\n{3,}", "\n\n", text).strip()

        # Strategy 2: Full page with aggressive cleanup
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        logger.info("Extracted %d chars using full page fallback", len(text))
        return text

class LinkedInBlockedError(Exception):
    """Raised when a LinkedIn URL cannot be fetched as a public page."""
