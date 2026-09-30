# Automatic publication import from ORCID

This site can generate `publications.html` automatically from public ORCID records.

## 1. Edit ORCID IDs

The team configuration is stored in:

```text
data/orcid_members.csv
```

Current entries:

```csv
name,orcid,role,start_year
Martin Horák,0000-0001-8537-5984,PI,
Michal Šmejkal,0000-0003-1849-7900,PhD student,
Ondřej Faltus,0000-0002-9747-7803,Postdoctoral researcher,
Marco Amato,0000-0003-3764-3889,Postdoctoral researcher,2025
Riccardo Voso,0000-0002-5511-8618,Postdoctoral researcher,
```

## 2. Generate locally

From the root directory of the website, run:

```bash
python3 tools/generate_publications_from_orcid.py
```

By default, the generated group list contains publications from 2020 onward.
Use `--min-year 0` to include the full ORCID histories or another year to
change the group-wide cutoff. The optional `start_year` value in the CSV can
apply a later cutoff to an individual member.

The daily GitHub workflow uses the default 2020 cutoff.

Then preview:

```bash
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/publications.html
```

## 3. Automatic updates with GitHub Actions

The package includes:

```text
.github/workflows/update-publications.yml
```

After pushing the site to GitHub, this workflow regenerates `publications.html` daily at 05:15 UTC or manually through **Actions → Update publications from ORCID → Run workflow**.

The workflow commits the updated `publications.html` back to the repository.

## 4. Notes

- The generator uses the public ORCID API and only public ORCID works.
- The group-wide publication cutoff defaults to 2020.
- ORCID records are user-maintained, so completeness depends on whether each member keeps their ORCID works up to date.
- Duplicates are merged by DOI first, otherwise by normalized title.
- Names listed in `data/group_members.txt` are bolded in author lists.
- The script is server-side/static-generation oriented. Calling ORCID directly from browser JavaScript is not reliable because ORCID API responses may be blocked by browser CORS rules.
