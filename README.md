# Mechanics of Soft Materials Group website

This is a static HTML/CSS/JS website template for a research group. It includes:

- homepage
- people page with team cards, photos, and short biographies
- projects page
- news page
- contact page with group details and a contact-mechanics animation
- publication page generated from public ORCID records

## Local preview

```bash
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000
```

## Automatic publications

The publication page can be regenerated from ORCID:

```bash
python3 tools/generate_publications_from_orcid.py
```

Team ORCID IDs are stored in:

```text
data/orcid_members.csv
```

Names to be bolded in author lists are stored in:

```text
data/group_members.txt
```

## Server automation

See:

```text
README_DEPLOYMENT.md
```

It contains both cron and systemd-timer examples for running the ORCID update every morning.


Navigation includes dedicated Openings and Contact pages. People, Publications, and Projects also include introductory page-opening sections.
