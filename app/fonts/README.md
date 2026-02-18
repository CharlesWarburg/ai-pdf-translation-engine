# Unicode font for PDF output

Place **DejaVuSans.ttf** here for full Unicode support in generated PDFs (accents, €, —, etc.). If missing, the app falls back to the default font and may show black boxes for non-ASCII characters.

**Easiest:** from the project root run once:

```bash
python scripts/fetch_dejavu.py
```

This downloads the font from SourceForge into this folder. Alternatively:

- Download: [DejaVu Fonts](https://dejavu-fonts.github.io/Download.html) → e.g. `dejavu-fonts-ttf-2.37.tar.bz2` → use `ttf/DejaVuSans.ttf`.
- macOS with Homebrew: `brew install --cask font-dejavu` (font goes to `~/Library/Fonts/`; the app will find it).
- In Docker, the image runs the fetch script so this folder is populated automatically.
