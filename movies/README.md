# Movies

Personal movie watchlist and reviews. Data lives in `movies.log` at the repo root.

## Browsing

**Web UI:** [https://k1monfared.github.io/notes/movies/](https://k1monfared.github.io/notes/movies/)

The `index.html` page provides a read-only interface with search, genre filters, rating sliders, and expandable movie cards.

## Mobile Editor (Movie Writer PWA)

A Progressive Web App for adding, editing, and reviewing movies from your phone.

**Live URL:** [https://k1monfared.github.io/notes/movie-writer/](https://k1monfared.github.io/notes/movie-writer/)

### Setup

1. Open the URL above on your phone
2. If you already use the Blog Writer PWA, the token is shared automatically. Otherwise, create a [fine-grained Personal Access Token](https://github.com/settings/personal-access-tokens/new):
   - Repository access: select **k1monfared/notes** only
   - Permissions: **Contents** read and write
3. Paste the token into the app
4. Tap "Add to Home Screen" in your browser menu to install it

### Features

- Browse movies with "To Watch" / "Watched" tabs
- Search and filter by title, director, recommender, genre
- Expand cards to see full details (synopsis, cast, review, IMDb link)
- Add new movies with title, director, year, recommender, and review
- New movies with a recommender are placed under their name in the "Recommended by" section
- Mark movies as watched (with optional review prompt)
- Edit existing movie properties
- Dark mode (follows system preference)

### IMDb Enrichment

When you add or edit a movie via the app, a GitHub Actions workflow automatically runs after push to:

1. Fix any missing recommender properties (`scripts/fix_recommenders.py`)
2. Fetch IMDb data for unenriched movies (`scripts/enrich_all.py`)
3. Commit the enriched data back to `movies.log`

This requires the `OMDB_API_KEY` repository secret to be set (Settings > Secrets > Actions).

The enrichment step labels every fetched field with a trailing `(IMDb)`. Run `./movie strip-imdb --apply` (or the full `./movie cleanup --apply`) to remove those markers; the operation is idempotent and safe to re-run any time the file gets re-enriched.

## CLI Tool

The `movie` script in this directory provides command-line management:

```bash
./movie add              # Interactive add to "To Watch"
./movie watched "Title"  # Mark as watched
./movie review "Title" "text"  # Add review
./movie fetch-imdb "Title"     # Fetch IMDb data
./movie server           # Local dev server (port 8787)
./movie push             # Commit and push changes
```

### Cleanup pipeline

A four-stage pipeline normalises and reorganises `movies.log`. Each stage is its own subcommand, defaults to dry-run, and takes `--apply` to write. All stages are idempotent.

```bash
./movie strip-imdb       # 1. remove "(IMDb)" annotations
./movie normalize-keys   # 2. canonicalise property keys
./movie dedupe           # 3. merge duplicate movie entries
./movie route            # 4. move misplaced [x] and [-] entries
./movie cleanup          # run all four stages in order
```

Add `--apply` to write changes, or `-v`/`--verbose` for per-line reports on stages 1, 2, and 4.

What each stage does:

- **strip-imdb** removes every `(IMDb)` suffix from value lines and inside `Cast (IMDb):`-style headers.
- **normalize-keys** rewrites property keys to a canonical form: `recommended by`, `recommmender`, `receommender` → `Recommender`; `directors` → `Director`; bare `Rating` (when value is `<n>/10`) → `IMDB Rating`. Multi-role keys like `Director and screenwriter` are left untouched.
- **dedupe** merges duplicate entries (matched by IMDb id, falling back to title + year). The winner is the entry in the strongest section (rated `watched` category > `to categorize` > `I've watched it` > `To review` > `Skipped` > `To Watch`). All distinct reviews and recommenders from every copy are preserved on the merged entry. Two copies *both* in `watched` under different categories are reported as conflicts, never auto-merged.
- **route** moves every misplaced entry to its proper section:
  - `[x]` with a review → `watched: > to categorize:`
  - `[x]` without a review → top-level `- To review`
  - `[-]` (skipped) → top-level `- Skipped`
  - When the entry has no `Recommender` line, one is derived from the parent context (e.g. `Festivals > TIFF 2023` → `Recommender: TIFF 2023`; `Because of the director > Damien Chazelle, ...` → `Recommender: Director: Damien Chazelle`; top-level list categories like `NYT 2025 top 100` → that name).

`cleanup` runs `strip-imdb → normalize-keys → dedupe → route` against a single in-memory buffer and writes once at the end (with `--apply`). The order matters: stripping `(IMDb)` lets dedupe see equal-value matches, and normalising keys ensures dedupe treats `recommended by` and `Recommender` as the same field.

## Data Format

Movies are stored in `movies.log` using a hierarchical text format:

```
- watched:
    - I highly recommend:
        [x] Movie Title
            - Director: Name
            - Year: 2024
            - review: Your review here
            - IMDB Rating: 8.5/10
            - Genres: Drama, Thriller
    - to categorize:
        [x] Reviewed but not yet rated
- To review
    [x] Watched but no review yet
- Skipped
    [-] Movie I won't watch
- To Watch
    - Recommended by
        - Person Name
            [] Movie Title
                - Recommender: Person Name
                - Director: Name
```

Checkbox status: `[x]` watched, `[]` unwatched, `[-]` skipped (won't watch), `[?]` uncertain.

Top-level sections:

- **`watched:`** — entries you've watched and rated, organised into categories like `I highly recommend:`, `I recommend:`, `Good entertainment/fun and/or well-made:`, `Not a good one:`, `I highly discourage:`. The `to categorize:` and `I've watched it:` sub-buckets hold reviewed-but-unrated entries.
- **`To review`** — `[x]` entries that have been watched but don't yet have a `review` line. Move from here into a `watched:` category once you've written a review.
- **`Skipped`** — `[-]` entries you've decided not to watch.
- **`To Watch`** — the active queue, grouped by `Festivals`, `Recommended by > <person>`, `Because of the director > <name>`, and ad-hoc list categories like `NYT 2025 top 100`.

The `cleanup` pipeline above keeps these sections in sync: any `[x]` outside `watched:` or `To review` gets routed to its proper home, and any `[-]` outside `Skipped` ends up there.
