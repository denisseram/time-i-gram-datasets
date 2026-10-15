# Novelists: lives and masterpieces (Wikidata)

Two SPARQL queries against the Wikidata Query Service (https://query.wikidata.org/sparql), run on **2026-10-15**; the CSV files are the service's CSV exports (`Accept: text/csv`), **unedited**.

| Query | Export | Rows | Content |
|---|---|---|---|
| `writers.rq` | `writers.csv` | 24 | `writer, writerLabel, birth, death`: 24 novelists born after 1700, chosen by hand (the `VALUES` list) |
| `works.rq` | `works.csv` | 74 | `writer, writerLabel, birth, death, work, workLabel, sitelinks, published`: their notable works (P800) that are literary works (P31/P279* Q7725634), with articles in at least 30 Wikipedias (`sitelinks`), first published (the earliest P577, the first edition) in the writer's lifetime or up to 10 years after their death |

Notes:
- Victor Hugo (Q535) was part of the first list, but Wikidata had no labels for Q535 on the query date (in any language); he was replaced by Jules Verne (Q33977).
- Marcel Proust and Toni Morrison have no row in `works.csv`: the only first-publication date of *In Search of Lost Time* is 2000 (an edition), which the 10-year rule excludes, and none of Morrison's works has 30 sitelinks.
- Dates known only to the year are stored as 1 January (e.g. `1847-01-01T00:00:00Z`).

To reproduce (results may change as Wikidata is edited):

```bash
curl -G https://query.wikidata.org/sparql -H "Accept: text/csv" --data-urlencode query@works.rq -o works.csv
```

Source: Wikidata, https://www.wikidata.org. License: [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
