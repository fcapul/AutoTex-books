# AutoTex Books

**AutoTex Books** is an open-source tool that lets you write professional, print-ready books using [Claude Code](https://claude.ai/code) as the AI author. You describe what you want — Claude plans the chapters, writes the content, generates illustrations, compiles the PDF, and visually reviews every page. The result is a KDP-ready (Amazon Kindle Direct Publishing) PDF you can upload and sell.

No LaTeX knowledge required. No writing experience required. Just Claude Code, a few free installs, and your ideas.

---

## What it produces

- A fully typeset PDF book, ready to upload to Amazon KDP or any print-on-demand service
- Professional-quality layout: correct trim sizes, binding margins, table of contents, headers, page numbers
- AI-generated illustrations (via Google Gemini) or precise mathematical/technical diagrams (via TikZ)
- Custom-designed visual boxes (definitions, examples, notes, tips) styled to match your book's theme

---

## How it works

```
You describe your book idea
        ↓
Claude Code plans chapters, writes LaTeX, generates images
        ↓
AutoTex compiles LaTeX → PDF, renders pages → PNG
        ↓
Claude visually reviews every page, fixes issues
        ↓
You get a print-ready PDF
```

**Claude Code** is the brain — it plans, writes, and reviews. The **AutoTex Python package** (`autotex/`) is the hands — it provides CLI commands for compiling, rendering, and image generation that Claude calls automatically.

---

## Prerequisites

You need four things installed before you start:

### 1. Claude Code

Claude Code is Anthropic's official AI coding assistant for the terminal.

- Install it from: https://claude.ai/code
- You need an Anthropic account (free tier available)
- After install, run `claude` in your terminal to confirm it works

### 2. Python 3.11 or newer

Python runs the AutoTex utility package.

- Download from: https://www.python.org/downloads/
- During install on Windows, check **"Add Python to PATH"**
- Confirm it works: open a terminal and run `python --version`

### 3. A LaTeX distribution (MiKTeX recommended)

LaTeX is the typesetting system that turns text into beautifully formatted PDFs. You don't need to know LaTeX — Claude writes it — but you do need it installed.

**Windows:** Download and install MiKTeX from https://miktex.org/download
  - During setup, choose **"Install missing packages on-the-fly: Yes"** — this lets MiKTeX automatically download any LaTeX packages it needs

**macOS:** Install MacTeX from https://www.tug.org/mactex/

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install texlive-full
```

After install, confirm it works:
```bash
pdflatex --version
```

### 4. A Google Gemini API key (for AI-generated images)

Gemini generates the illustrations. The free tier is generous enough for most books.

- Go to: https://aistudio.google.com/apikey
- Click **"Create API key"**
- Copy the key — you'll need it in the setup step below

> **Note:** If you don't need AI-generated images (TikZ diagrams only), you can skip this. Just don't use `%%IMAGE_REQUEST{...}%%` markers in your chapters.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/fcapul/autotex-books.git
cd autotex-books
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

Create a file named `.env` in the project root with your Gemini key:

```
GOOGLE_API_KEY=your_key_here
```

### 4. Verify the setup

```bash
python -m autotex info
```

You should see the default configuration printed. If you get an error, re-check that Python and `pdflatex` are both in your PATH.

---

## Quick Start: Your First Book

Open a terminal in the project folder and start Claude Code:

```bash
claude
```

Then simply tell Claude what you want:

```
Write me a beginner's guide to home gardening. Make it friendly and practical,
about 8 chapters, novel trim size (6×9 inches).
```

Claude will:
1. Ask you a few planning questions (audience, style, length)
2. Create the book folder under `books/`
3. Plan the chapters and write them one by one
4. Generate illustrations
5. Compile and visually review the PDF
6. Fix any formatting issues

The finished PDF will be at `books/your-book-name/build/main.pdf`.

---

## Project Structure

```
autotex-books/
├── autotex/              Python utility package (the CLI engine)
├── autotex-book.sty      LaTeX style file (handles KDP layout, typography)
├── config.yaml           Default configuration template
├── requirements.txt      Python dependencies
├── .env                  Your API keys (you create this, never commit it)
└── books/
    └── my-book/          Each book lives in its own self-contained folder
        ├── config.yaml   Book settings (title, author, chapters, trim size)
        ├── CLAUDE.md     Instructions for Claude about this specific book
        ├── main.tex      Generated LaTeX root file (don't edit manually)
        ├── text/         Chapter .tex files (written by Claude)
        ├── assets/       Generated images (.png files)
        └── build/        Compiled output (PDF, page previews)
```

> **Important:** Never edit the root-level `config.yaml` or `main.tex` when working on a book. Always edit the files inside `books/your-book-name/`.

---

## Creating and Managing Books

### Start a new book

You can just ask Claude in natural language, or use the init command directly:

```bash
python -m autotex init my-book-name
```

This creates `books/my-book-name/` with all the necessary files.

### All CLI commands

> **Tip:** You almost never need to run these commands manually — Claude runs them automatically as part of the book writing workflow.

For all commands below, replace `books/my-book/config.yaml` with the path to your book's config file.

| Command | What it does |
|---------|-------------|
| `python -m autotex init <name>` | Create a new book folder |
| `python -m autotex --config books/<name>/config.yaml update-main` | Regenerate `main.tex` after editing the chapter list in `config.yaml` |
| `python -m autotex --config books/<name>/config.yaml compile` | Compile the book to PDF |
| `python -m autotex --config books/<name>/config.yaml render 0 1 2` | Render pages 0, 1, 2 to PNG images for review |
| `python -m autotex --config books/<name>/config.yaml render-chapter 3 "Chapter Title"` | Render the last pages of a specific chapter |
| `python -m autotex --config books/<name>/config.yaml images text/chapter01.tex` | Generate AI images from markers in a chapter file |
| `python -m autotex --config books/<name>/config.yaml search "some text"` | Find which pages contain specific text |
| `python -m autotex --config books/<name>/config.yaml info` | Print the book's current configuration |

---

## Book Configuration (`config.yaml`)

Each book has its own `config.yaml`. Here's what the fields mean:

```yaml
book:
  title: "My Book Title"        # The book's title (appears on the cover and headers)
  author: "Jane Smith"          # Author name
  language: "english"           # Language for hyphenation rules
  chapters:                     # List of chapters (Claude fills this in during planning)
    - number: 1
      title: "Introduction"
    - number: 2
      title: "Getting Started"

api:
  gemini_model: "gemini-3.1-flash-image-preview"   # Gemini model for image generation

kdp:
  enabled: true
  trim_size: "novel"    # Page size — see KDP Trim Sizes table below
  bleed: false          # Set true only if images extend to the page edge
  gutter: ""            # Binding margin override (e.g. "0.5in"), leave empty for default
  paper: "white"        # "white" or "cream"

latex:
  compiler: "pdflatex"
  root_file: "main.tex"
  output_dir: "build"
```

### KDP Trim Sizes

| Name | Dimensions | Best for |
|------|-----------|----------|
| `pocket` | 5.25 × 8 in | Small guides, poetry |
| `digest` | 5.5 × 8.5 in | Workbooks, journals |
| `novel` | 6 × 9 in | **Default.** Most non-fiction, textbooks |
| `royal` | 6.14 × 9.21 in | Academic books |
| `crown` | 7 × 10 in | Technical manuals |
| `large` | 7.5 × 9.25 in | Illustrated books |
| `letter` | 8.5 × 11 in | Workbooks, coloring books |
| `ustrade` | 6 × 9 in | US trade paperback |
| `uktrade` | 5.5 × 8.5 in | UK trade paperback |

---

## Illustrations

AutoTex supports two kinds of illustrations, and Claude chooses the right one automatically:

### TikZ diagrams (built into LaTeX)

For graphs, charts, flowcharts, geometric diagrams, and anything that can be drawn precisely. These are vector graphics — infinitely sharp at any zoom level, no external service needed.

### AI-generated images (Google Gemini)

For realistic scenes, conceptual illustrations, maps, covers, or anything that needs visual richness. Claude places a marker in the chapter:

```
%%IMAGE_REQUEST{description="A watercolor-style illustration of a vegetable garden in summer", filename="ch01-garden", aspect_ratio="16:9"}%%
```

When you run `autotex images text/chapter01.tex`, the marker is replaced with the generated image automatically. Supported aspect ratios:

| Ratio | Best for |
|-------|---------|
| `16:9` | Wide diagrams, flowcharts |
| `4:3` | Standard illustrations |
| `1:1` | Square icons, portraits |
| `3:4` | Tall diagrams |
| `9:16` | Narrow vertical illustrations |

---

## Customizing Your Book's Visual Style

Every book gets a custom-designed set of boxes (called **tcolorbox environments**) that match its theme. For example:

- A **mathematics textbook** might have: Definition, Theorem, Example, Remark
- A **practical guide** might have: Key Principle, Exercise, Insight, Warning
- A **history book** might have: Primary Source, Context, Analysis, Timeline

Claude designs these from scratch for every book during the planning phase and adds them to `main.tex`. You don't need to do anything — just tell Claude the mood and color palette you want when planning.

---

## Book-Specific Instructions (`CLAUDE.md`)

Each book folder contains a `CLAUDE.md` file where you can give Claude specific instructions for that book. After `autotex init`, it contains a template:

```markdown
# Book: my-book

## Topic & Scope
This is a beginner's guide to urban gardening in small spaces.

## Target Audience
Adults aged 25-45 living in apartments with no garden experience.

## Writing Style
Friendly and encouraging. No jargon. Practical tips over theory.

## Special Instructions
Use metric units (cm, kg, liters). Include a "Quick Tip" box in every chapter.
```

Edit this file before asking Claude to write chapters. The more specific you are, the better the output.

---

## Workflow: Writing a Book from Scratch

Here is the full flow, from idea to finished PDF:

**1. Start Claude Code in the project folder:**
```bash
claude
```

**2. Describe your book:**
```
I want to write a beginner's guide to personal finance for young adults.
Novel size, conversational tone, about 10 chapters.
```

**3. Answer Claude's planning questions** (audience, style, color palette, etc.)

**4. Claude will:**
- Run `autotex init your-book-name`
- Plan all chapters and update `books/your-book-name/config.yaml`
- Run `autotex update-main` to generate `main.tex`
- Write chapters one by one, generating images along the way
- Compile the PDF after each chapter
- Render pages and visually review them
- Fix any formatting issues

**5. Your PDF is ready** at `books/your-book-name/build/main.pdf`

---

## Troubleshooting

### `pdflatex not found`
LaTeX is not installed or not in your PATH. Reinstall MiKTeX/MacTeX and restart your terminal.

### `GOOGLE_API_KEY not set` or image generation fails
Check that your `.env` file is in the project root folder (not inside `books/`) and contains exactly:
```
GOOGLE_API_KEY=your_key_here
```

### Missing LaTeX packages during compilation
MiKTeX will prompt you to install missing packages automatically. Click **Install** when it asks. On TeX Live, run:
```bash
sudo tlmgr install <package-name>
```

### `python -m autotex` not found
Make sure you're running the command from inside the `autotex-books` folder, and that you ran `pip install -r requirements.txt`.

### Compilation errors
Claude handles LaTeX errors automatically (up to 3 retry attempts). If compilation still fails after 3 tries, check `books/your-book/build/main.log` for the error message and paste it to Claude.

---

## Tips for Better Results

- **Be specific when planning.** "A textbook on calculus for engineering students, formal tone, with many worked examples and TikZ diagrams" will give better results than "a math book."
- **Edit `CLAUDE.md` before writing.** The more context Claude has about your audience and style, the more consistent the writing.
- **Review the PDF after each chapter.** Claude renders and reviews pages automatically, but you should also open the PDF and check that you're happy with the direction before continuing.
- **Use `novel` trim size as the default.** It's the most widely accepted KDP format and looks professional for almost any genre.
- **Keep chapter descriptions in `config.yaml` detailed.** Claude reads these when writing each chapter, so richer descriptions mean better content.

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)** — see [LICENSE](LICENSE) for details.

This means you are free to use, modify, and distribute this software, but any derivative works must also be released under the GPLv3. You may not incorporate this code into proprietary software without complying with the license terms.

---

## Acknowledgments

Built on top of [Claude Code](https://claude.ai/code) by Anthropic, [Google Gemini](https://deepmind.google/technologies/gemini/) for image generation, and the [LaTeX](https://www.latex-project.org/) typesetting system.

---

> **Legal notice:** This software is provided "as is", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort, or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.
