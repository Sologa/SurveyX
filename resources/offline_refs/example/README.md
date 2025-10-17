# Offline References Example

Put your converted `.md` references here (or in a sibling folder).

Quick start
- Convert PDFs → MD:
  - `python scripts/pdf_to_md.py --in_dir /path/to/pdfs --out_dir resources/offline_refs/example`
- Validate MD:
  - `python scripts/validate_md_refs.py --ref_path resources/offline_refs/example`
- Run offline pipeline:
  - `python tasks/offline_run.py --title "Your Survey Title" --key_words "kw1, kw2" --ref_path resources/offline_refs/example`

Notes
- First line should be a Markdown H1 title (`# ...`).
- Include an “Abstract” section to improve downstream extraction.

