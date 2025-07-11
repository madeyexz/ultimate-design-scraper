# Design Token Extractor

A Python-based tool for extracting design tokens and generating AI-friendly prompts from websites using Playwright.

## Features

- 🎨 **Visual Analysis**: Full-page screenshots and element analysis
- 🔤 **Typography Extraction**: Font families, sizes, weights, and spacing
- 🎨 **Color Palette**: Intelligent color clustering and palette generation
- 📏 **Spacing System**: Margin/padding analysis and spacing scale extraction
- 🧩 **Component Patterns**: Automatic detection of UI components
- 📱 **Responsive Analysis**: Breakpoint detection and responsive patterns
- ✨ **Animation Detection**: CSS animations and transitions
- 🤖 **AI Prompt Generation**: Converts tokens into detailed recreation prompts
- 📊 **Rich Terminal UI**: Progress bars and colored logging output
- 🔄 **Batch Processing**: Sequential processing to avoid browser conflicts

## Installation

### Recommended: Using uv (Fast)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that handles dependencies and virtual environments automatically.

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies:**
```bash
uv sync
```

3. **Install Playwright browsers:**
```bash
uv run playwright install chromium
```

### Alternative: Using pip

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers:**
```bash
playwright install chromium
```

## Usage

### Single URL Extraction

**Using uv:**
```bash
uv run python -c "
from design_extractor import DesignExtractor
import asyncio

async def extract_single_site():
    extractor = DesignExtractor()
    results = await extractor.extract_design('https://example.com')
    print(f'Extracted tokens for: {results[\"site_name\"]}')

asyncio.run(extract_single_site())
"
```

**Using regular Python:**
```python
from design_extractor import DesignExtractor
import asyncio

async def extract_single_site():
    extractor = DesignExtractor()
    results = await extractor.extract_design("https://example.com")
    print(f"Extracted tokens for: {results['site_name']}")

asyncio.run(extract_single_site())
```

### Batch Processing

Process multiple URLs from your `links.txt` file:

**Using uv:**
```bash
uv run python batch_extractor.py
```

**Using regular Python:**
```bash
python batch_extractor.py
```

This will:
- Read URLs from `links.txt` (one URL per line)
- Extract design tokens for each site sequentially (to avoid browser conflicts)
- Generate AI-friendly prompts automatically
- Save results to `extracted_designs/` directory
- Show progress bars and colored output for better visibility

### Manual Processing

**Using uv:**
```bash
uv run python -c "
from design_extractor import DesignExtractor
from prompt_generator import generate_prompt_from_tokens
from pathlib import Path
import asyncio

async def process_site(url):
    # Extract design tokens
    extractor = DesignExtractor()
    results = await extractor.extract_design(url)
    
    # Generate prompt
    site_name = results['site_name']
    tokens_file = Path(f'extracted_designs/{site_name}/design_tokens.json')
    prompt_file = Path(f'extracted_designs/{site_name}/recreation_prompt.md')
    
    generate_prompt_from_tokens(tokens_file, prompt_file)

# Process your links
asyncio.run(process_site('https://example.com'))
"
```

**Using regular Python:**
```python
from design_extractor import DesignExtractor
from prompt_generator import generate_prompt_from_tokens
from pathlib import Path
import asyncio

async def process_site(url):
    # Extract design tokens
    extractor = DesignExtractor()
    results = await extractor.extract_design(url)
    
    # Generate prompt
    site_name = results['site_name']
    tokens_file = Path(f"extracted_designs/{site_name}/design_tokens.json")
    prompt_file = Path(f"extracted_designs/{site_name}/recreation_prompt.md")
    
    generate_prompt_from_tokens(tokens_file, prompt_file)

# Process your links
asyncio.run(process_site("https://example.com"))
```

## Output Structure

For each processed site, the tool creates:

```
extracted_designs/
├── example.com/
│   ├── screenshot.png          # Full page screenshot
│   ├── page.html              # Rendered HTML
│   ├── design_tokens.json     # Extracted design tokens
│   ├── recreation_prompt.md   # AI-friendly prompt
│   └── css_coverage.json      # CSS usage analysis
└── batch_summary.json         # Batch processing summary
```

## Design Tokens Structure

The extracted `design_tokens.json` includes:

```json
{
  "color_palette": {
    "primary_colors": ["#ff4d4f", "#1890ff", "#52c41a"],
    "all_colors": ["..."]
  },
  "typography_system": {
    "primary_fonts": ["Inter", "Georgia"],
    "font_sizes": [14, 16, 18, 24, 32, 48],
    "font_weights": [400, 500, 600, 700]
  },
  "spacing_scale": [4, 8, 12, 16, 24, 32, 48, 64],
  "components": {
    "buttons": [...],
    "cards": [...],
    "headers": [...]
  },
  "breakpoints": [...],
  "animations": {...}
}
```

## AI Prompt Generation

The tool automatically generates detailed prompts like:

```markdown
# Website Recreation Prompt

Create a pixel-perfect recreation of this website using modern web technologies.

## 🎨 Design System

### Typography
**Primary Fonts:**
- Inter
- Georgia

**Font Sizes:**
- 14px, 16px, 18px, 24px, 32px, 48px

### Color Palette
**Primary Colors:**
- Color 1: `rgb(255, 77, 79)`
- Color 2: `rgb(24, 144, 255)`

### Spacing Scale
**Spacing Scale:**
- Small: 4, 8px
- Medium: 12, 16, 24px
- Large: 32, 48, 64px

[... detailed sections continue ...]
```

## Configuration

### Extraction Settings

Modify `design_extractor.py` to adjust:
- Viewport size (default: 1920x1080)
- Element limit (default: 500)
- Asset extraction types
- Screenshot quality

### Batch Processing

Configure `batch_extractor.py`:
- `max_concurrent`: Processing mode (default: 1 for sequential processing to avoid browser conflicts)
- `delay_between_requests`: Delay between requests in seconds (default: 3.0)

## Advanced Usage

### Custom Token Processing

```python
from design_extractor import DesignExtractor

class CustomExtractor(DesignExtractor):
    def _process_tokens(self, tokens):
        # Custom token processing logic
        processed = super()._process_tokens(tokens)
        
        # Add custom analysis
        processed['custom_metrics'] = self._analyze_custom_patterns(tokens)
        
        return processed
```

### Prompt Customization

```python
from prompt_generator import PromptGenerator

class CustomPromptGenerator(PromptGenerator):
    def __init__(self):
        super().__init__()
        # Customize template
        self.template = """
        # Custom Prompt Template
        {custom_sections}
        """
```

## Troubleshooting

### Common Issues

1. **Playwright Installation**
   ```bash
   # If browsers fail to install
   playwright install --with-deps chromium
   ```

2. **Memory Issues**
   - Reduce element limit in `_extract_tokens()`
   - Process URLs in smaller batches

3. **Rate Limiting**
   - Increase `delay_between_requests`
   - Processing is sequential by default to avoid browser conflicts

4. **CORS Issues**
   - Some CSS coverage may be limited due to CORS
   - Screenshots and HTML extraction work regardless

5. **Browser Conflicts**
   - The tool processes URLs sequentially to avoid "Only one live display may be active at once" errors
   - Each URL uses a fresh browser instance

### Performance Tips

- Use `headless=True` for faster extraction (default)
- Limit element analysis to visible elements only
- Process in smaller batches for large URL lists
- Use SSD storage for better I/O performance
- Consider using `uv` for faster dependency management

## License

This project is open source. Please respect website terms of service and robots.txt when scraping.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Playwright documentation
3. Submit an issue with detailed logs