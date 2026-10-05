# Release checklist

This checklist is intended for public release `v1.0.0` and Zenodo archiving.

## Before making the repository public

- [x] Add the `heading2diagram.py` implementation.
- [x] Confirm that the implementation uses Python 3.10+ standard library only.
- [x] Regenerate all example outputs and confirm all 14 reference outputs match exactly.
- [x] Add an automated regression test for the 14 reference outputs.
- [ ] Confirm that no password, API key, private data, or machine-specific path is included.
- [ ] Replace the temporary author entry in `CITATION.cff` with the actual author name, affiliation, and ORCID.
- [x] Confirm `version: "1.0.0"` in `CITATION.cff` and `VERSION`.
- [ ] Confirm that the MIT License is the intended license for the project.
- [ ] Perform a final review of `README.md`, `README_jp.md`, and `docs/見出し形式文法.md`.

## Local verification

```sh
python heading2diagram.py -h
python -m unittest discover -s tests -v
```

## GitHub and Zenodo

- [ ] Change repository visibility to Public.
- [ ] Connect the GitHub account to Zenodo.
- [ ] In Zenodo's GitHub integration, run **Sync now**.
- [ ] Enable the `heading2diagram` repository.
- [ ] Create Git tag `v1.0.0`.
- [ ] Publish GitHub Release `v1.0.0`.
- [ ] Confirm that Zenodo archives the release and issues a DOI.

## After DOI issuance

- [ ] Add the Zenodo DOI badge/link to `README.md` and `README_jp.md`.
- [ ] Add the DOI to the next-release version of `CITATION.cff`.
- [ ] Commit the metadata update to the default branch.
