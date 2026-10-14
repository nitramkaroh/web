# Mechanics of Soft Materials Group website

This is a static HTML/CSS/JS website template for a research group. It includes:

- homepage
- people page with team cards, photos, and short biographies
- projects page
- teaching page with the two courses and links to the course portal (CTU login)
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

The generated group list includes publications from 2020 onward by default.

Team ORCID IDs are stored in:

```text
data/orcid_members.csv
```

Names to be bolded in author lists are stored in:

```text
data/group_members.txt
```

## Teaching portal link

`teaching.html` lists the courses. Its two buttons open the separate teaching
portal (homework status, teacher's comments and uploads behind the CTU login),
which runs on the faculty server, not on this site:

```text
https://mech.fsv.cvut.cz/~mhorak/vyuka/
```

The address is declared once as `PORTAL_URL` in an HTML comment just before
`<main>`. The buttons link to `PORTAL_URL?course=prpe` (Pružnost a pevnost) and
`PORTAL_URL?course=ppm` (Přetváření a porušování materiálů); after login the
portal shows each student only the course whose list contains them. If the
portal moves, replace the address everywhere at once (the portal's `app_url`,
with its trailing slash):

```bash
sed -i 's|https://mech.fsv.cvut.cz/~mhorak/vyuka/|https://<new address>/|g' teaching.html
```

The course ids `prpe` and `ppm` must match the `courses` keys in the portal's
`config.php`. No student data belongs in this repository: the student lists and
homework records live only in the portal.

## Server automation

See:

```text
README_DEPLOYMENT.md
```

It contains both cron and systemd-timer examples for running the ORCID update every morning.


Navigation includes dedicated Teaching, Openings and Contact pages. People, Publications, and Projects also include introductory page-opening sections.
