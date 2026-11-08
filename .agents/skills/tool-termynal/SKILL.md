---
description: >-
  Guide for Termynal animated terminal widgets in documentation.
  Covers Markdown fenced code blocks with termynal comments, prompt configuration,
  comments, progress bars, and styling. Use when creating or debugging
  terminal animation widgets in Zensical docs.
  Triggers: termynal, termy, terminal animation, cli animation, animated terminal, docs animation.
name: tool-termynal
version: 1.0.0
---

# Termynal Animated Terminal (`tool-termynal`)

This skill documents **Termynal**, an animated terminal widget designed by Ines
Montani.

Termynal uses native browser `async`/`await` for typing animations without external
dependencies or layout reflows. Non-JavaScript visitors still see the complete
terminal output as clean static text.

---

## 1. Quick Reference & Core Syntax

Zensical loads Termynal through the `termynal` Python package (`termynal.include_assets = true` in `zensical.toml`).
The package embeds the required styles and scripts automatically.

The Python markdown extension converts fenced code blocks (`console` or `bash`) directly preceded by `<!-- termynal -->`.
Do not use old `<div class="termy">` wrappers.

### Markdown Integration

Place `<!-- termynal -->` directly before any fenced `console` or `bash` code block:

````markdown
<!-- termynal -->
```console
$ uv run my-cli greet "World"

✨ Hello, World!

# Inspect CLI options and help
$ uv run my-cli --help

<b>Usage: </b><b>my-cli [OPTIONS] COMMAND [ARGS]...</b>

╭─ Options ─────────────────────────────────────────╮
│ --version  -v        Show version and exit.       │
│ --help               Show this message and exit.  │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ greet                Display a personalized       │
│                      greeting.                    │
╰───────────────────────────────────────────────────╯
```
````

### Per-Block Configuration

Pass inline YAML configuration inside the HTML comment:

````markdown
<!-- termynal: {title: "python", prompt_literal_start: ["$", ">>>"]} -->
```console
$ python
>>> print("Hello from Python")
Hello from Python
```
````

Available configuration options:
- `title`: Window title string (default: `"bash"`).
- `prompt_literal_start`: Sequence of prompt strings recognized as input commands (default: `["$"]`). Set `prompt_literal_start: ["$", ">>>"]` for Python REPL examples.
- `buttons`: Window control style, `"macos"` or `"windows"` (default: `"macos"`).

### Line Syntax Mapping

When `termynal` processes a code block, it parses each line:

| Markdown Syntax | Parsed Type | Behavior in Animation |
| :--- | :--- | :--- |
| `$ <command>` | `input` | Types characters one by one with animated cursor and `$ ` prompt. |
| `>>> <command>` | `input` | Types command if `>>>` is in `prompt_literal_start`. |
| `<cmd> \` | `input` (multiline) | Continues input command onto subsequent lines. |
| `# <comment>` | `comment` | Displays instant line styled with `--termynal-comment`. |
| `---> 100%` | `progress` | Animates a loading progress bar from 0% to 100% (`████████ 100%`). |
| `<b>text</b>` | `output` | Output line preserving bold styling without typing delay. |
| `plain text` | `output` | Plain output displayed after line delay. |

> [!IMPORTANT]
> Always use `# <comment>` for comments inside termynal blocks. Do not use `// <comment>`.

---

## 2. Generated HTML Structure

The preprocessor converts fenced blocks into this HTML structure:

```html
<div class="termy" data-termynal data-ty-macos data-ty-title="bash">
    <span data-ty="input" data-ty-prompt="$">uv run my-cli</span>
    <span class="termynal-comment"># Progress demo</span>
    <span data-ty="progress"></span>
    <span data-ty>✨ Success!</span>
</div>
```

### Container Attributes

The generated container supports these data attributes:

| Attribute | Default | Description |
| :--- | :--- | :--- |
| `data-ty-startDelay` | `600` | Delay in milliseconds before typing starts. |
| `data-ty-typeDelay` | `80` (or `60`) | Delay in milliseconds between typed characters. |
| `data-ty-lineDelay` | `1200` (or `500`) | Delay in milliseconds before revealing the next line. |
| `data-ty-progressLength` | `40` | Total character width of the progress bar. |
| `data-ty-progressChar` | `█` | Character used to draw progress blocks. |
| `data-ty-progressPercent` | `100` | Percentage target where progress stops. |
| `data-ty-cursor` | `▋` | Cursor character displayed during typing. |

---

## 3. Interactive Controls & Styling

Termynal includes interactive control buttons in the top right corner of the terminal window:
- **`fast →`**: Instantly sets delays to `0`, finishing the animation immediately.
- **`restart ↻`**: Clears the container and replays the animation from the start.

### CSS Custom Properties

The embedded `termynal.css` defines these custom properties for theming:

```css
:root {
  --termynal-bg: #1e222b;          /* Terminal window background */
  --termynal-text: #eaeaea;        /* Primary command and output text */
  --termynal-subtle: #7d8590;      /* Header title and inactive controls */
  --termynal-accent: #2dd4bf;      /* Prompt ($) and active button accents */
  --termynal-comment: #5eead4;     /* Comment text (# ...) */
}
```

The top window bar renders macOS-style window controls (red `#ff5f56`, yellow
`#ffbd2e`, green `#27c93f`) via CSS pseudo-elements.

---

## 4. Guidelines and Best Practices

1. **Place `<!-- termynal -->` directly before the code block**:
   Do not wrap fenced blocks inside `<div class="termy">`.
2. **Use `#` for comments**:
   The parser recognizes lines starting with `# ` as comments. The parser treats lines that start with `//` as normal output.
3. **Configure custom prompts when needed**:
   If you demonstrate Python REPL sessions, specify `prompt_literal_start: ["$", ">>>"]` in the comment header.
4. **Constrain column width**:
   Keep terminal outputs concise (under 60–70 columns). Wide lines force unwanted horizontal scrolling on smaller screens.
5. **Use static code blocks**:
   Never use dynamic execution flags (`exec="on"`) in termynal blocks. Termynal parses static text.
6. **Preserve rich tags in output**:
   Use `<b>Usage: </b>` for command headers. Termynal renders HTML tags in output lines with correct browser styling.
