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

## Data Format

Movies are stored in `movies.log` using a hierarchical text format:

```
- watched:
    - I highly recommend:
        [x] Movie Title
            - Director: Name
            - Year: 2024
            - review: Your review here
            - IMDB Rating: 8.5/10 (IMDb)
            - Genres: Drama, Thriller (IMDb)
- To Watch
    - Recommended by
        - Person Name
            [] Movie Title
                - Recommender: Person Name
                - Director: Name
```

Checkbox status: `[x]` watched, `[]` unwatched, `[-]` in-progress, `[?]` uncertain.
