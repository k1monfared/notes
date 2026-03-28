# Photoblog Convention

Photo blog posts imported from [k1-photo.blogspot.com](https://k1-photo.blogspot.com/).

## File Organization

### Images
- **Directory**: `blog/files/photoblog/`
- **Naming**: `YYYY-MM-DD_slug_NN.ext`
  - `YYYY-MM-DD` = post date
  - `slug` = slugified title (or `photo` if untitled)
  - `NN` = photo number within the post (`01`, `02`, etc.)
  - `ext` = `.jpg`, `.png`, or `.gif`
- Example: `2014-06-08_still_01.jpg`, `2014-06-08_still_02.jpg`

### Post Files
- **Naming**: `YYYYMMDD_slug_photo.md` (the `_photo` suffix distinguishes from regular posts)
- **Frontmatter**:
  ```yaml
  ---
  tags: photoblog
  thumbnail: files/photoblog/YYYY-MM-DD_slug_01.jpg
  ---
  ```
- **Title format**:
  - With title: `# Original Title - photo`
  - Without title: `# YYYY-MM-DD - photo`
- **Body**: Each image as `![alt](files/photoblog/filename.jpg)`, one per line
- **Footer**: Link back to original Blogger post

### Untitled Posts
Titles that are ".", "-", "...", "—", or empty are treated as untitled.
The slug becomes `photo` and the title becomes `YYYY-MM-DD - photo`.

### Comments
Stored in `blog/comments/<url_slug>/NNN.yml` using the standard blog comment format:
```yaml
name: Commenter Name
date: YYYY-MM-DD
comment: Comment text here
```

## Tags
All photoblog posts are tagged with `photoblog`.

## Import Script
`blog/import_photoblog.py` — fetches posts from Blogger JSON feed API, downloads images, and creates markdown files.

```bash
# Full import
python blog/import_photoblog.py

# Preview without downloading
python blog/import_photoblog.py --dry-run

# Import only N posts
python blog/import_photoblog.py --max 10

# Resume from a specific index
python blog/import_photoblog.py --start 100
```
