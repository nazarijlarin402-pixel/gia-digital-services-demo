# Export CSV safely for spreadsheets — a practical checklist

*Original GIA technical guide · November 2026 · informational demo, not a client deliverable.*

A CSV file can look like ordinary data but still be dangerous when opened in a spreadsheet. The main problem is **formula injection**: if a user-controlled cell starts with certain characters, spreadsheet software may interpret it as a formula rather than text.

## Five checks before exporting

1. **Define the columns.** A stable schema such as `id,name,note` makes it harder to mix fields accidentally. Reject malformed records, and decide whether blank IDs are allowed.
2. **Deduplicate deliberately.** If `id` must be unique, decide whether the first or last record wins. In the accompanying GIA demonstration, the first valid ID wins.
3. **Quote fields using a CSV library.** Commas, quotation marks, carriage returns and line breaks require careful escaping. Manually joining fields with commas is fragile.
4. **Treat spreadsheet formulas as untrusted text.** Values starting with `=`, `+`, `-`, `@` or certain control characters may be dangerous when opened in spreadsheets. The GIA demo prefixes potentially formula-like values with a literal apostrophe as a simple spreadsheet-oriented mitigation. This is not a universal guarantee across every spreadsheet importer; test your target software and locale.
5. **Test the actual recipient workflow.** Verify encoding (usually UTF-8), delimiter, line endings, locale and the spreadsheet application. The safest export for a machine pipeline may differ from the safest export for a person opening Excel.

## Reproducible example

See [the original Python example](../examples/clean_csv.py) and its [synthetic JSON input](../examples/example_input.json). It uses the Python standard library and makes no network requests.

Try the command:

```bash
python examples/clean_csv.py < examples/example_input.json > exported.csv
```

You should get three data rows: the duplicate ID is omitted, and the formula-looking sample is handled as text.

## Before asking someone to clean your data

Explain the source format, row count, unique-key rule, exact output schema and whether your files include private information. Never publish sensitive input data in a GitHub issue or public discussion. A confidentiality agreement and approved transfer mechanism may be needed.

**Need a small CSV/JSON conversion?** You can [describe a task to GIA](https://gia-2p2.pages.dev/). Budget, scope and permitted AI use are agreed separately. This example is **not proof of previous client work**.
