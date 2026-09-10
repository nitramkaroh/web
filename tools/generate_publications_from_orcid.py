#!/usr/bin/env python3
"""
Generate publications.html from public ORCID works.

Usage:
    python3 tools/generate_publications_from_orcid.py
    python3 tools/generate_publications_from_orcid.py --members data/orcid_members.csv --out publications.html

The script uses only the Python standard library. It fetches public ORCID works,
retrieves individual work details, de-duplicates records by DOI/title, groups them by year,
and bolds authors listed in data/group_members.txt.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ORCID_API = "https://pub.orcid.org/v3.0"
USER_AGENT = "MSM-ORCID-Publications/1.0 (static-site-generator)"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Member:
    name: str
    orcid: str = ""
    role: str = ""
    start_year: int | None = None


@dataclass
class Publication:
    title: str
    year: str = "Unknown year"
    date_sort: str = "0000-00-00"
    authors: list[str] = field(default_factory=list)
    venue: str = ""
    pub_type: str = ""
    doi: str = ""
    url: str = ""
    source_orcids: set[str] = field(default_factory=set)
    source_names: set[str] = field(default_factory=set)

    def key(self) -> str:
        if self.doi:
            return "doi:" + normalize_doi(self.doi)
        return "title:" + normalize_key(self.title)

    def merge(self, other: "Publication") -> None:
        # Prefer the record with richer metadata.
        if len(other.authors) > len(self.authors):
            self.authors = other.authors
        if not self.venue and other.venue:
            self.venue = other.venue
        if not self.pub_type and other.pub_type:
            self.pub_type = other.pub_type
        if not self.doi and other.doi:
            self.doi = other.doi
        if not self.url and other.url:
            self.url = other.url
        if self.date_sort == "0000-00-00" and other.date_sort != "0000-00-00":
            self.date_sort = other.date_sort
            self.year = other.year
        self.source_orcids |= other.source_orcids
        self.source_names |= other.source_names


def request_json(url: str, *, retries: int = 3, pause: float = 0.6) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.orcid+json; charset=utf-8, application/json",
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(pause * attempt)
    raise RuntimeError(f"Could not fetch {url}: {last_error}")


def load_members(path: Path) -> list[Member]:
    members: list[Member] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            start_year_str = (row.get("start_year") or "").strip()
            start_year = int(start_year_str) if start_year_str.isdigit() else None
            members.append(
                Member(
                    name=name,
                    orcid=(row.get("orcid") or "").strip(),
                    role=(row.get("role") or "").strip(),
                    start_year=start_year,
                )
            )
    return members


def load_group_names(path: Path, members: Iterable[Member]) -> list[str]:
    names = [m.name for m in members]
    if path.exists():
        names += [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    # preserve order, remove duplicates
    seen: set[str] = set()
    unique = []
    for n in names:
        key = normalize_key(n)
        if key not in seen:
            seen.add(key)
            unique.append(n)
    return unique


def normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    value = value.replace("’", "'")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_doi(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.strip()


def get_nested(obj: dict[str, Any] | None, *keys: str) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def value_of(obj: Any) -> str:
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, dict):
        val = obj.get("value")
        if isinstance(val, str):
            return val.strip()
    return ""


def parse_title(work: dict[str, Any]) -> str:
    title = value_of(get_nested(work, "title", "title"))
    subtitle = value_of(get_nested(work, "title", "subtitle"))
    if title and subtitle:
        return f"{title}: {subtitle}"
    return title or "Untitled work"


def parse_publication_date(work: dict[str, Any]) -> tuple[str, str]:
    date = work.get("publication-date") or {}
    year = value_of(date.get("year"))
    month = value_of(date.get("month")) or "00"
    day = value_of(date.get("day")) or "00"
    if year:
        return year, f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
    return "Unknown year", "0000-00-00"


def parse_external_ids(work: dict[str, Any]) -> tuple[str, str]:
    doi = ""
    url = ""
    extids = get_nested(work, "external-ids", "external-id") or []
    if not isinstance(extids, list):
        extids = [extids]
    for ext in extids:
        if not isinstance(ext, dict):
            continue
        typ = (ext.get("external-id-type") or "").lower()
        val = (ext.get("external-id-value") or "").strip()
        ext_url = value_of(ext.get("external-id-url"))
        if typ == "doi" and val and not doi:
            doi = normalize_doi(val)
            url = ext_url or f"https://doi.org/{doi}"
        elif typ in {"arxiv", "arxiv-id"} and val and not url:
            url = ext_url or f"https://arxiv.org/abs/{val}"
        elif ext_url and not url:
            url = ext_url
    explicit_url = value_of(work.get("url"))
    if explicit_url and not url:
        url = explicit_url
    return doi, url


def parse_authors(work: dict[str, Any]) -> list[str]:
    contributors = get_nested(work, "contributors", "contributor") or []
    if not isinstance(contributors, list):
        contributors = [contributors]
    authors: list[str] = []
    for contributor in contributors:
        if not isinstance(contributor, dict):
            continue
        name = value_of(contributor.get("credit-name"))
        if not name:
            # Fallback to contributor-orcid path name is generally not present; keep blank.
            continue
        if name not in authors:
            authors.append(name)
    return authors


def parse_work_detail(work: dict[str, Any], member: Member) -> Publication:
    title = parse_title(work)
    year, date_sort = parse_publication_date(work)
    doi, url = parse_external_ids(work)
    venue = value_of(work.get("journal-title"))
    pub_type = (work.get("type") or "").replace("-", " ").title()
    authors = parse_authors(work)
    if not authors:
        # ORCID records sometimes lack contributor lists in public data.
        # Use the record owner as a minimal fallback so the item remains usable.
        authors = [member.name]
    return Publication(
        title=title,
        year=year,
        date_sort=date_sort,
        authors=authors,
        venue=venue,
        pub_type=pub_type,
        doi=doi,
        url=url,
        source_orcids={member.orcid} if member.orcid else set(),
        source_names={member.name},
    )


def fetch_member_publications(member: Member, *, max_works: int | None = None, verbose: bool = True) -> list[Publication]:
    if not member.orcid:
        if verbose:
            print(f"Skipping {member.name}: no ORCID iD in CSV", file=sys.stderr)
        return []
    if verbose:
        print(f"Fetching works for {member.name} ({member.orcid})", file=sys.stderr)
    works_url = f"{ORCID_API}/{urllib.parse.quote(member.orcid)}/works"
    data = request_json(works_url)
    groups = data.get("group") or []
    put_codes: list[str] = []
    for group in groups:
        summaries = group.get("work-summary") if isinstance(group, dict) else None
        if not isinstance(summaries, list):
            continue
        # Use first summary in the group; groups represent the same work from different sources.
        summary = summaries[0] if summaries else None
        put_code = str(summary.get("put-code")) if isinstance(summary, dict) and summary.get("put-code") is not None else ""
        if put_code:
            put_codes.append(put_code)
    if max_works is not None:
        put_codes = put_codes[:max_works]

    pubs: list[Publication] = []
    for idx, put_code in enumerate(put_codes, start=1):
        detail_url = f"{ORCID_API}/{urllib.parse.quote(member.orcid)}/work/{urllib.parse.quote(put_code)}"
        try:
            work = request_json(detail_url)
            pub = parse_work_detail(work, member)
            if member.start_year is not None and pub.year.isdigit() and int(pub.year) < member.start_year:
                continue
            pubs.append(pub)
        except RuntimeError as exc:
            print(f"Warning: {member.name}: failed work {put_code}: {exc}", file=sys.stderr)
        # Be polite to the public API.
        if idx % 10 == 0:
            time.sleep(0.5)
    return pubs


def deduplicate(publications: Iterable[Publication]) -> list[Publication]:
    by_key: dict[str, Publication] = {}
    for pub in publications:
        key = pub.key()
        if key in by_key:
            by_key[key].merge(pub)
        else:
            by_key[key] = pub
    return list(by_key.values())


def is_arxiv_preprint(pub: Publication) -> bool:
    venue = normalize_key(pub.venue)
    url = pub.url.lower()
    doi = pub.doi.lower()
    return venue == "arxiv" or "arxiv.org" in url or doi.startswith("10.48550/arxiv.")


def remove_redundant_preprints(publications: Iterable[Publication]) -> list[Publication]:
    pubs = list(publications)
    published_titles = {
        normalize_key(pub.title)
        for pub in pubs
        if not is_arxiv_preprint(pub)
    }
    return [pub for pub in pubs if not (is_arxiv_preprint(pub) and normalize_key(pub.title) in published_titles)]


def is_member_author(author: str, group_names: Iterable[str]) -> bool:
    a = normalize_key(author.replace(",", " "))
    for member in group_names:
        m = normalize_key(member)
        parts = m.split()
        swapped = " ".join(parts[::-1]) if len(parts) >= 2 else m
        # Exact normalized match or conservative full-name containment.
        if a == m or a == swapped or m in a or swapped in a:
            return True
    return False


# ORCID records are deposited by many hands, so the same person turns up as
# "Horak, Martin" in one and "Martin Horak" in another, with the diacritics
# dropped either way. Canonical spellings, keyed by the accent-stripped name.
CANONICAL_NAMES = {
    "martin horak": "Martin Hor\u00e1k",
    "michal smejkal": "Michal \u0160mejkal",
    "ondrej faltus": "Ond\u0159ej Faltus",
    "marco amato": "Marco Amato",
    "riccardo voso": "Riccardo Voso",
    "borek patzak": "Bo\u0159ek Patz\u00e1k",
    "petr havlasek": "Petr Havl\u00e1sek",
    "milan jirasek": "Milan Jir\u00e1sek",
    "ondrej rokos": "Ond\u0159ej Roko\u0161",
    "martin doskar": "Martin Do\u0161k\u00e1\u0159",
    "pavel rychnovsky": "Pavel Rychnovsk\u00fd",
    "jan havelka": "Jan Havelka",
}


def canonical_author(author: str) -> str:
    """Normalize one author name: "Last, First" -> "First Last", then apply
    the canonical spelling if the person is known."""
    name = author.strip()
    if name.count(",") == 1:
        last, first = (part.strip() for part in name.split(","))
        if last and first:
            name = f"{first} {last}"
    stripped = normalize_key(name)
    return CANONICAL_NAMES.get(stripped, name)


def format_authors(authors: list[str], group_names: list[str]) -> str:
    rendered = []
    for author in authors:
        name = canonical_author(author)
        safe = html.escape(name)
        if is_member_author(name, group_names):
            safe = f"<strong>{safe}</strong>"
        rendered.append(safe)
    return "; ".join(rendered)


def format_meta(pub: Publication) -> str:
    bits: list[str] = []
    if pub.venue:
        bits.append(f"<em>{html.escape(pub.venue)}</em>")
    if pub.pub_type:
        bits.append(html.escape(pub.pub_type))
    if pub.year != "Unknown year":
        bits.append(html.escape(pub.year))
    return ", ".join(bits)


def item_class(pub: Publication) -> str:
    t = normalize_key(pub.pub_type)
    if "preprint" in t or "working paper" in t:
        return "publication-item preprint"
    if "conference" in t or "proceeding" in t:
        return "publication-item proceedings"
    return "publication-item"


def render_publications_page(publications: list[Publication], group_names: list[str], generated_note: str) -> str:
    publications.sort(key=lambda p: (p.date_sort, normalize_key(p.title)), reverse=True)
    years: dict[str, list[Publication]] = {}
    for pub in publications:
        years.setdefault(pub.year, []).append(pub)

    if not publications:
        body = """
      <h2 class="pub-year">No ORCID works found</h2>
      <article class="publication-item">
        <h3>No public ORCID works were downloaded.</h3>
        <p class="pub-meta">Check <code>data/orcid_members.csv</code>, internet access, and whether the ORCID records contain public works.</p>
      </article>
"""
    else:
        parts = []
        for year in sorted(years.keys(), key=lambda y: int(y) if y.isdigit() else -1, reverse=True):
            parts.append(f'      <h2 class="pub-year">{html.escape(year)}</h2>')
            for pub in years[year]:
                links = []
                if pub.doi:
                    doi_url = pub.url or f"https://doi.org/{pub.doi}"
                    links.append(f'<a href="{html.escape(doi_url)}">doi:{html.escape(pub.doi)}</a>')
                elif pub.url:
                    links.append(f'<a href="{html.escape(pub.url)}">link</a>')
                links_html = " | ".join(links)
                parts.append(f"""      <article class="{item_class(pub)}">
        <h3>{html.escape(pub.title)}</h3>
        <p class="pub-authors">{format_authors(pub.authors, group_names)}</p>
        <p class="pub-meta">{format_meta(pub)}</p>
        <p class="pub-links">{links_html}</p>
      </article>""")
        body = "\n".join(parts)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Mechanics of Soft Materials Group | Publications</title>
  <link rel="icon" type="image/svg+xml" href="figs/msm-logo.svg" />
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="index.html">
        <img class="brand-mark" src="figs/msm-logo.svg" alt="" width="38" height="38" />
        <span class="brand-text">
          <span class="brand-name">Mechanics of Soft Materials Group</span>
          <span class="brand-sub">Czech Technical University in Prague</span>
        </span>
      </a>
      <button class="nav-toggle" aria-label="Toggle navigation" aria-expanded="false">&#9776;</button>
      <nav class="site-nav" aria-label="Main navigation">
        <a href="people.html">People</a>
        <a href="publications.html" class="active">Publications</a>
        <a href="projects.html">Projects</a>
        <a href="news.html">News</a>
        <a href="openings.html">Openings</a>
        <a href="contact.html">Contact</a>
      </nav>
    </div>
  </header>

  <main class="container page-layout">
    <section class="page-opening">
      <p class="eyebrow">Publications</p>
      <h1>Publications</h1>
      <p class="lead">
        The publication list is generated from public ORCID records and organized by year. Group members are shown in <strong>bold</strong>.
      </p>
    </section>

    <section class="publication-list" aria-label="Publication list">
{body}
    </section>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          <h3>Mechanics of Soft Materials Group</h3>
          <p>
            Mathematical models, numerical methods and open scientific software for soft
            solids, surface mechanics, instabilities, contact and multiphysics problems.
          </p>
          <p>
            Department of Mechanics, Faculty of Civil Engineering<br />
            Czech Technical University in Prague<br />
            Th&aacute;kurova 7, 166 29 Prague 6, Czech Republic
          </p>
        </div>
        <div>
          <h3>Pages</h3>
          <ul class="footer-links">
            <li><a href="people.html">People</a></li>
            <li><a href="publications.html">Publications</a></li>
            <li><a href="projects.html">Projects</a></li>
            <li><a href="news.html">News</a></li>
            <li><a href="openings.html">Openings</a></li>
            <li><a href="contact.html">Contact</a></li>
          </ul>
        </div>
        <div>
          <h3>Affiliation</h3>
          <div class="footer-logos">
            <a href="https://www.cvut.cz/en"><img src="figs/ctu-logo.png" alt="Czech Technical University in Prague" loading="lazy" /></a>
          </div>
          <p>
            Funding is acknowledged on the
            <a href="projects.html">projects</a> page.
          </p>
        </div>
      </div>
      <div class="footer-bottom">
        Mechanics of Soft Materials Group
      </div>
    </div>
  </footer>

  <script src="script.js"></script>
</body>
</html>
"""


def resolve_project_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate publications.html from public ORCID works.")
    parser.add_argument("--members", default="data/orcid_members.csv", help="CSV with columns name,orcid,role")
    parser.add_argument("--group-members", default="data/group_members.txt", help="Names to bold in author lists")
    parser.add_argument("--out", default="publications.html", help="Output HTML file")
    parser.add_argument("--max-works", type=int, default=None, help="Limit works per ORCID record, useful for testing")
    parser.add_argument("--note", default="Generated from public ORCID records. Re-run tools/generate_publications_from_orcid.py to update this page.")
    args = parser.parse_args()

    members_path = resolve_project_path(args.members)
    if not members_path.exists():
        print(f"Missing members file: {members_path}", file=sys.stderr)
        return 2

    members = load_members(members_path)
    group_names = load_group_names(resolve_project_path(args.group_members), members)
    all_publications: list[Publication] = []
    for member in members:
        all_publications.extend(fetch_member_publications(member, max_works=args.max_works))

    publications = remove_redundant_preprints(deduplicate(all_publications))
    html_text = render_publications_page(publications, group_names, args.note)
    out_path = resolve_project_path(args.out)
    out_path.write_text(html_text, encoding="utf-8")
    print(f"Wrote {out_path} with {len(publications)} unique publications.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
