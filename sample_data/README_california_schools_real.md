# California schools real data (DuckDB)

`california_schools_real.duckdb` is a DuckDB copy of the historical school-level datasets already bundled in `california_schools/california_schools.sqlite`.

## Contents

- `schools`: 17,686 school directory records, with administrator names/emails, street and mailing addresses, phone numbers, and websites omitted.
- `frpm`: 9,986 school-level Free or Reduced-Price Meal records for academic year 2014–15.
- `satscores`: 2,269 school- and district-level SAT summary records.
- `dataset_metadata`: source, period, and transformation notes.

This is public, aggregate education data. It contains no student-level records. Original rows are retained in the three data tables; only the listed school contact fields are dropped.

## Provenance

The bundled FRPM data identifies the 2014–15 academic year. California’s Department of Education (CDE) describes its annual FRPM files as school-level counts from CALPADS: [CDE FRPM data](https://www.cde.ca.gov/DS/ad/filessp.asp). The SAT table is a historical CDE report assembled from College Board data matched to California public schools: [CDE SAT data archive](https://www.cde.ca.gov/re/pr/satdata.asp). The school directory is based on CDE’s public school and district files: [CDE Data & Statistics](https://www.cde.ca.gov/Ds/).

The DuckDB is derived from the snapshot already present in this repository; it is not a newly downloaded or current-year CDE release. Rebuild it with:

```bash
.venv/bin/python scripts/create_california_schools_db.py
```

The script refuses to overwrite an existing output file. Use `--source` and `--output` to select different paths.
