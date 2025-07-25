"""
Design Token Extractor - Extract design tokens from websites using Playwright
"""

import asyncio
import json
import os
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import re
from collections import Counter

from playwright.async_api import async_playwright, Page, Browser
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import colorsys
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

# Setup rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("design_extractor")


class DesignExtractor:
    def __init__(self, output_dir: str = "extracted_designs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"🚀 Design Extractor initialized with output directory: {self.output_dir}")
        
    async def extract_design(self, url: str, site_name: Optional[str] = None) -> Dict[str, Any]:
        """Main extraction method"""
        start_time = time.time()
        
        if not site_name:
            site_name = urlparse(url).netloc.replace("www.", "")
        
        site_dir = self.output_dir / site_name
        site_dir.mkdir(exist_ok=True)
        
        logger.info(f"🌐 Starting extraction for: {url}")
        logger.info(f"📁 Output directory: {site_dir}")
        
        async with async_playwright() as p:
            logger.info("🎭 Launching Playwright browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            try:
                # Navigate and wait for content
                logger.info(f"🚀 Navigating to {url}...")
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                await page.wait_for_timeout(3000)  # Additional wait for dynamic content
                logger.info("✅ Page loaded successfully")
                
                # Extract all design tokens
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console
                ) as progress:
                    
                    extraction_task = progress.add_task("Extracting design tokens...", total=9)
                    
                    logger.info("📸 Taking screenshot...")
                    screenshot = await self._take_screenshot(page, site_dir)
                    progress.update(extraction_task, advance=1)
                    
                    logger.info("📄 Extracting HTML...")
                    html = await self._extract_html(page, site_dir)
                    progress.update(extraction_task, advance=1)
                    
                    logger.info("🏷️ Extracting design tokens...")
                    tokens = await self._extract_tokens(page)
                    progress.update(extraction_task, advance=1)
                    
                    logger.info("🎨 Analyzing CSS coverage...")
                    css_coverage = await self._extract_css_coverage(page, site_dir)
                    progress.update(extraction_task, advance=1)
                    
                    logger.info("🗂️ Extracting assets...")
                    assets = await self._extract_assets(page, site_dir)
                    progress.update(extraction_task, advance=1)
                    
                    logger.info("📱 Analyzing breakpoints...")
                    breakpoints = await self._extract_breakpoints(page)
                    progress.update(extraction_task, advance=1)
                    
                    logger.info("✨ Extracting animations...")
                    animations = await self._extract_animations(page)
                    progress.update(extraction_task, advance=1)
                    
                    logger.info("👆 Analyzing interactions...")
                    interactions = await self._extract_interactions(page, site_dir)
                    progress.update(extraction_task, advance=1)
                    
                    results = {
                        'url': url,
                        'site_name': site_name,
                        'screenshot': screenshot,
                        'html': html,
                        'tokens': tokens,
                        'css_coverage': css_coverage,
                        'assets': assets,
                        'responsive_breakpoints': breakpoints,
                        'animations': animations,
                        'interactions': interactions
                    }
                    
                    # Post-process tokens
                    logger.info("🔄 Processing tokens into design system...")
                    processed = self._process_tokens(results['tokens'])
                    results.update(processed)
                    progress.update(extraction_task, advance=1)
                    
                    # Save results
                    logger.info("💾 Saving results...")
                    await self._save_results(results, site_dir)
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"✅ Extraction completed in {elapsed_time:.2f}s")
                    
                    return results
                
            finally:
                await browser.close()
                logger.info("🔒 Browser closed")
    
    async def _take_screenshot(self, page: Page, site_dir: Path) -> str:
        """Take full page screenshot"""
        screenshot_path = site_dir / "screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        return str(screenshot_path)
    
    async def _extract_html(self, page: Page, site_dir: Path) -> str:
        """Extract rendered HTML"""
        html_path = site_dir / "page.html"
        content = await page.content()
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(html_path)
    
    async def _extract_tokens(self, page: Page) -> List[Dict[str, Any]]:
        """Extract computed style tokens from visible elements"""
        logger.debug("🔍 Evaluating page JavaScript to extract tokens...")
        tokens = await page.evaluate("""
            () => {
                const elements = Array.from(document.querySelectorAll('*'))
                    .filter(el => {
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        return rect.width * rect.height > 0 && 
                               style.display !== 'none' && 
                               style.visibility !== 'hidden';
                    })
                    .slice(0, 500); // Limit for performance
                
                return elements.map(el => {
                    const style = getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    
                    return {
                        tag: el.tagName.toLowerCase(),
                        classes: el.className,
                        id: el.id,
                        text: el.textContent?.trim().substring(0, 100) || '',
                        position: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        typography: {
                            fontFamily: style.fontFamily,
                            fontSize: style.fontSize,
                            fontWeight: style.fontWeight,
                            fontStyle: style.fontStyle,
                            lineHeight: style.lineHeight,
                            letterSpacing: style.letterSpacing,
                            textAlign: style.textAlign,
                            textTransform: style.textTransform
                        },
                        colors: {
                            color: style.color,
                            backgroundColor: style.backgroundColor,
                            borderColor: style.borderColor
                        },
                        spacing: {
                            margin: [style.marginTop, style.marginRight, style.marginBottom, style.marginLeft],
                            padding: [style.paddingTop, style.paddingRight, style.paddingBottom, style.paddingLeft]
                        },
                        borders: {
                            borderWidth: style.borderWidth,
                            borderStyle: style.borderStyle,
                            borderRadius: style.borderRadius
                        },
                        layout: {
                            display: style.display,
                            position: style.position,
                            flexDirection: style.flexDirection,
                            justifyContent: style.justifyContent,
                            alignItems: style.alignItems,
                            gridTemplateColumns: style.gridTemplateColumns,
                            gridTemplateRows: style.gridTemplateRows
                        },
                        effects: {
                            boxShadow: style.boxShadow,
                            transform: style.transform,
                            opacity: style.opacity,
                            transition: style.transition
                        }
                    };
                });
            }
        """)
        logger.debug(f"📊 Extracted {len(tokens)} design tokens from visible elements")
        return tokens
    
    async def _extract_assets(self, page: Page, site_dir: Path) -> List[Dict[str, str]]:
        """Extract asset URLs"""
        assets = []
        
        def handle_request(request):
            if request.resource_type in ['font', 'stylesheet', 'image']:
                assets.append({
                    'url': request.url,
                    'type': request.resource_type,
                    'method': request.method
                })
        
        page.on('request', handle_request)
        logger.debug("🔄 Reloading page to capture asset requests...")
        await page.reload(wait_until='networkidle')
        
        logger.debug(f"🗂️ Captured {len(assets)} asset requests")
        return assets
    
    async def _extract_css_coverage(self, page: Page, site_dir: Path) -> Dict[str, Any]:
        """Extract CSS coverage data"""
        try:
            client = await page.context.new_cdp_session(page)
            
            # Enable required domains first
            await client.send('DOM.enable')
            await client.send('CSS.enable')
            await client.send('Runtime.enable')
            
            # Start CSS coverage tracking
            await client.send('CSS.startRuleUsageTracking')
            
            # Wait for page to fully load and render
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(2000)
            
            # Trigger interactions to capture hover states and dynamic CSS
            try:
                # Scroll to trigger any scroll-based styles
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                await page.wait_for_timeout(500)
                await page.evaluate('window.scrollTo(0, 0)')
                await page.wait_for_timeout(500)
                
                # Hover over interactive elements
                buttons = await page.query_selector_all('button, a, .btn, [role="button"]')
                for i, button in enumerate(buttons[:5]):  # Limit to first 5
                    try:
                        await button.hover()
                        await page.wait_for_timeout(100)
                    except:
                        continue
                
                # Trigger any focus states
                inputs = await page.query_selector_all('input, textarea, select')
                for i, input_el in enumerate(inputs[:3]):  # Limit to first 3
                    try:
                        await input_el.focus()
                        await page.wait_for_timeout(100)
                    except:
                        continue
                        
            except Exception as interaction_error:
                print(f"Interaction simulation failed: {interaction_error}")
            
            # Stop coverage tracking and get results
            coverage = await client.send('CSS.stopRuleUsageTracking')
            
            # Process the coverage data to make it more useful
            processed_coverage = {
                'ruleUsage': coverage.get('ruleUsage', []),
                'totalRules': len(coverage.get('ruleUsage', [])),
                'usedRules': len([rule for rule in coverage.get('ruleUsage', []) if rule.get('used', False)]),
                'coverage_percentage': 0
            }
            
            if processed_coverage['totalRules'] > 0:
                processed_coverage['coverage_percentage'] = round(
                    (processed_coverage['usedRules'] / processed_coverage['totalRules']) * 100, 2
                )
            
            # Save the processed coverage
            coverage_path = site_dir / "css_coverage.json"
            with open(coverage_path, 'w') as f:
                json.dump(processed_coverage, f, indent=2)
            
            logger.info(f"📊 CSS Coverage: {processed_coverage['usedRules']}/{processed_coverage['totalRules']} rules used ({processed_coverage['coverage_percentage']}%)")
            
            return processed_coverage
            
        except Exception as e:
            logger.error(f"❌ CSS coverage extraction failed: {e}")
            return {
                'ruleUsage': [],
                'totalRules': 0,
                'usedRules': 0,
                'coverage_percentage': 0,
                'error': str(e)
            }
    
    async def _extract_breakpoints(self, page: Page) -> List[Dict[str, Any]]:
        """Extract responsive breakpoints"""
        breakpoints = await page.evaluate("""
            () => {
                const breakpoints = [];
                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            if (rule.type === CSSRule.MEDIA_RULE) {
                                const mediaText = rule.media.mediaText;
                                const widthMatch = mediaText.match(/(?:min-width|max-width):\\s*(\\d+)px/g);
                                if (widthMatch) {
                                    breakpoints.push({
                                        mediaText: mediaText,
                                        widths: widthMatch
                                    });
                                }
                            }
                        }
                    } catch (e) {
                        // Skip external stylesheets due to CORS
                    }
                }
                return breakpoints;
            }
        """)
        logger.debug(f"📱 Found {len(breakpoints)} responsive breakpoints")
        return breakpoints
    
    async def _extract_animations(self, page: Page) -> List[Dict[str, Any]]:
        """Extract animations and transitions"""
        animations = await page.evaluate("""
            () => {
                const animations = [];
                const keyframes = [];
                
                // Extract @keyframes
                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            if (rule.type === CSSRule.KEYFRAMES_RULE) {
                                keyframes.push({
                                    name: rule.name,
                                    keyframes: Array.from(rule.cssRules).map(kr => ({
                                        keyText: kr.keyText,
                                        style: kr.style.cssText
                                    }))
                                });
                            }
                        }
                    } catch (e) {
                        // Skip external stylesheets
                    }
                }
                
                // Extract active animations
                document.getAnimations().forEach(anim => {
                    animations.push({
                        animationName: anim.animationName,
                        duration: anim.effect?.getTiming().duration,
                        iterations: anim.effect?.getTiming().iterations,
                        playState: anim.playState
                    });
                });
                
                return { animations, keyframes };
            }
        """)
        logger.debug(f"✨ Found {len(animations.get('animations', []))} animations and {len(animations.get('keyframes', []))} keyframes")
        return animations
    
    async def _extract_interactions(self, page: Page, site_dir: Path) -> Dict[str, Any]:
        """Extract interaction states by simulating hover/focus"""
        interactions = {}
        
        # Find interactive elements
        interactive_elements = await page.evaluate("""
            () => {
                const selectors = ['button', 'a', 'input', '[role="button"]', '.btn'];
                const elements = [];
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach((el, i) => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            elements.push({
                                selector: selector,
                                index: i,
                                x: rect.x + rect.width / 2,
                                y: rect.y + rect.height / 2,
                                classes: el.className,
                                tag: el.tagName.toLowerCase()
                            });
                        }
                    });
                });
                
                return elements.slice(0, 10); // Limit for performance
            }
        """)
        
        logger.debug(f"🎯 Found {len(interactive_elements)} interactive elements")
        
        # Capture hover states
        hover_states = []
        for element in interactive_elements[:5]:  # Limit to first 5
            try:
                await page.mouse.move(element['x'], element['y'])
                await page.wait_for_timeout(100)
                
                hover_style = await page.evaluate(f"""
                    () => {{
                        const el = document.querySelectorAll('{element["selector"]}')[{element["index"]}];
                        if (el) {{
                            const style = getComputedStyle(el);
                            return {{
                                backgroundColor: style.backgroundColor,
                                color: style.color,
                                transform: style.transform,
                                boxShadow: style.boxShadow
                            }};
                        }}
                        return null;
                    }}
                """)
                
                if hover_style:
                    hover_states.append({
                        'element': element,
                        'hover_style': hover_style
                    })
            except Exception as e:
                logger.debug(f"Failed to capture hover state: {e}")
        
        interactions['hover_states'] = hover_states
        logger.debug(f"👆 Captured {len(hover_states)} hover states")
        return interactions
    
    def _process_tokens(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process and cluster tokens into design system"""
        if not tokens:
            logger.warning("⚠️ No tokens to process")
            return {}
        
        logger.debug(f"🔄 Processing {len(tokens)} tokens into design system...")
        
        # Extract and cluster colors
        colors = self._extract_colors(tokens)
        color_palette = self._cluster_colors(colors)
        logger.debug(f"🎨 Found {len(colors)} unique colors, clustered into {len(color_palette.get('primary_colors', []))} primary colors")
        
        # Extract and cluster fonts
        fonts = self._extract_fonts(tokens)
        font_system = self._cluster_fonts(fonts)
        logger.debug(f"📝 Found {len(fonts)} font instances, {len(font_system.get('primary_fonts', []))} primary fonts")
        
        # Extract spacing scale
        spacing_scale = self._extract_spacing_scale(tokens)
        logger.debug(f"📏 Generated spacing scale with {len(spacing_scale)} values")
        
        # Extract component patterns
        components = self._extract_components(tokens)
        component_count = sum(len(comp_list) for comp_list in components.values())
        logger.debug(f"🧩 Identified {component_count} components across {len(components)} categories")
        
        return {
            'color_palette': color_palette,
            'typography_system': font_system,
            'spacing_scale': spacing_scale,
            'components': components
        }
    
    def _extract_colors(self, tokens: List[Dict[str, Any]]) -> List[str]:
        """Extract all unique colors from tokens"""
        colors = set()
        for token in tokens:
            if token.get('colors'):
                for color_value in token['colors'].values():
                    if color_value and color_value != 'rgba(0, 0, 0, 0)':
                        colors.add(color_value)
        return list(colors)
    
    def _cluster_colors(self, colors: List[str], max_colors: int = 10) -> Dict[str, Any]:
        """Cluster colors into a palette"""
        if not colors:
            return {}
        
        # Convert colors to RGB
        rgb_colors = []
        for color in colors:
            rgb = self._color_to_rgb(color)
            if rgb:
                rgb_colors.append(rgb)
        
        if len(rgb_colors) < 2:
            return {'primary_colors': colors}
        
        # Cluster colors
        n_clusters = min(max_colors, len(rgb_colors))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(rgb_colors)
        
        # Get representative colors
        palette = []
        for i in range(n_clusters):
            cluster_colors = [rgb_colors[j] for j, c in enumerate(clusters) if c == i]
            if cluster_colors:
                # Use the most common color in cluster
                representative = Counter(map(tuple, cluster_colors)).most_common(1)[0][0]
                palette.append(f"rgb({representative[0]}, {representative[1]}, {representative[2]})")
        
        return {
            'primary_colors': palette,
            'all_colors': colors[:20]  # Limit for readability
        }
    
    def _color_to_rgb(self, color: str) -> Optional[tuple]:
        """Convert color string to RGB tuple"""
        try:
            # Handle rgb() format
            if color.startswith('rgb('):
                values = re.findall(r'\d+', color)
                if len(values) >= 3:
                    return (int(values[0]), int(values[1]), int(values[2]))
            
            # Handle rgba() format
            elif color.startswith('rgba('):
                values = re.findall(r'[\d.]+', color)
                if len(values) >= 3:
                    return (int(float(values[0])), int(float(values[1])), int(float(values[2])))
            
            # Handle hex format
            elif color.startswith('#'):
                color = color[1:]
                if len(color) == 6:
                    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))
                elif len(color) == 3:
                    return (int(color[0]*2, 16), int(color[1]*2, 16), int(color[2]*2, 16))
        
        except Exception:
            pass
        
        return None
    
    def _extract_fonts(self, tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract font information"""
        fonts = []
        for token in tokens:
            if token.get('typography'):
                fonts.append(token['typography'])
        return fonts
    
    def _cluster_fonts(self, fonts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cluster fonts into typography system"""
        if not fonts:
            return {}
        
        # Group by font family
        font_families = {}
        font_sizes = []
        font_weights = []
        
        for font in fonts:
            family = font.get('fontFamily', '').split(',')[0].strip().strip('"\'')
            if family:
                if family not in font_families:
                    font_families[family] = []
                font_families[family].append(font)
            
            # Collect sizes and weights
            size = font.get('fontSize', '')
            if size and 'px' in size:
                try:
                    font_sizes.append(int(float(size.replace('px', ''))))
                except ValueError:
                    pass
            
            weight = font.get('fontWeight', '')
            if weight and weight.isdigit():
                font_weights.append(int(weight))
        
        # Get most common families
        primary_fonts = sorted(font_families.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        
        # Get unique sizes and weights
        unique_sizes = sorted(set(font_sizes))
        unique_weights = sorted(set(font_weights))
        
        return {
            'primary_fonts': [family for family, _ in primary_fonts],
            'font_sizes': unique_sizes,
            'font_weights': unique_weights
        }
    
    def _extract_spacing_scale(self, tokens: List[Dict[str, Any]]) -> List[int]:
        """Extract spacing scale from margins and padding"""
        spacing_values = []
        
        for token in tokens:
            if token.get('spacing'):
                for space_type in ['margin', 'padding']:
                    if token['spacing'].get(space_type):
                        for value in token['spacing'][space_type]:
                            if value and 'px' in value:
                                try:
                                    px_value = int(float(value.replace('px', '')))
                                    if px_value > 0:
                                        spacing_values.append(px_value)
                                except ValueError:
                                    pass
        
        # Get unique values and sort
        unique_values = sorted(set(spacing_values))
        
        # Filter to common design system values
        scale = []
        for value in unique_values:
            if value <= 100 and (value % 4 == 0 or value % 8 == 0 or value in [2, 6, 10, 12, 14, 18, 20, 24, 28, 36, 44, 48, 52, 56, 60, 64, 72, 80, 96]):
                scale.append(value)
        
        return scale[:20]  # Limit for readability
    
    def _extract_components(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract component patterns"""
        components = {}
        
        # Group by common component classes
        component_patterns = {
            'buttons': ['button', 'btn', 'cta'],
            'cards': ['card', 'item', 'post'],
            'headers': ['header', 'nav', 'navigation'],
            'footers': ['footer']
        }
        
        for component_type, patterns in component_patterns.items():
            matching_tokens = []
            for token in tokens:
                classes = token.get('classes', '')
                if isinstance(classes, str):
                    classes = classes.lower()
                else:
                    classes = str(classes).lower()
                if any(pattern in classes for pattern in patterns) or token.get('tag') in patterns:
                    matching_tokens.append(token)
            
            if matching_tokens:
                components[component_type] = matching_tokens[:5]  # Limit examples
        
        return components
    
    async def _save_results(self, results: Dict[str, Any], site_dir: Path):
        """Save extraction results"""
        results_path = site_dir / "design_tokens.json"
        
        # Create a simplified version for JSON serialization
        simplified_results = {
            'url': results['url'],
            'site_name': results['site_name'],
            'color_palette': results.get('color_palette', {}),
            'typography_system': results.get('typography_system', {}),
            'spacing_scale': results.get('spacing_scale', []),
            'components': results.get('components', {}),
            'breakpoints': results.get('responsive_breakpoints', []),
            'animations': results.get('animations', {}),
            'asset_count': len(results.get('assets', []))
        }
        
        with open(results_path, 'w') as f:
            json.dump(simplified_results, f, indent=2)
        
        logger.info(f"✅ Design tokens saved to: {results_path}")


async def main():
    """Example usage"""
    extractor = DesignExtractor()
    
    # Test with a single URL
    url = "https://bryce-hall.com/"
    results = await extractor.extract_design(url)
    
    logger.info(f"🎯 Extraction Summary for: {url}")
    logger.info(f"   🎨 {len(results.get('color_palette', {}).get('primary_colors', []))} primary colors")
    logger.info(f"   📝 {len(results.get('typography_system', {}).get('primary_fonts', []))} primary fonts")
    logger.info(f"   📏 {len(results.get('spacing_scale', []))} spacing values")
    logger.info(f"   🧩 {len(results.get('components', {}))} component categories")


if __name__ == "__main__":
    asyncio.run(main())