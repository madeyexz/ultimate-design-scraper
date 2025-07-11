"""
Prompt Generator - Convert extracted design tokens into AI-friendly prompts
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import re


class PromptGenerator:
    def __init__(self):
        self.template = """
# Website Recreation Prompt

Create a pixel-perfect recreation of this website using modern web technologies.

## 🎨 Design System

### Typography
{typography_section}

### Color Palette
{color_section}

### Spacing Scale
{spacing_section}

### Components
{components_section}

### Layout & Responsive
{responsive_section}

### Animations & Effects
{animations_section}

## 🛠️ Technical Requirements

- Use modern HTML5 semantic elements
- Implement responsive design with mobile-first approach
- Use CSS Grid and Flexbox for layout
- Optimize for performance and accessibility
- Include hover states and interactions
- Ensure cross-browser compatibility

## 📋 Implementation Notes

{implementation_notes}

## 🎯 Key Focus Areas

1. **Typography**: Match font families, sizes, and spacing exactly
2. **Colors**: Use the extracted color palette consistently
3. **Spacing**: Follow the spacing scale for margins and padding
4. **Components**: Recreate interactive elements with proper states
5. **Responsive**: Ensure proper breakpoints and mobile experience

Please provide clean, semantic HTML and CSS code that recreates this design accurately.
"""
    
    def generate_prompt(self, design_tokens: Dict[str, Any]) -> str:
        """Generate a comprehensive prompt from design tokens"""
        
        # Generate each section
        typography_section = self._generate_typography_section(design_tokens)
        color_section = self._generate_color_section(design_tokens)
        spacing_section = self._generate_spacing_section(design_tokens)
        components_section = self._generate_components_section(design_tokens)
        responsive_section = self._generate_responsive_section(design_tokens)
        animations_section = self._generate_animations_section(design_tokens)
        implementation_notes = self._generate_implementation_notes(design_tokens)
        
        # Fill template
        prompt = self.template.format(
            typography_section=typography_section,
            color_section=color_section,
            spacing_section=spacing_section,
            components_section=components_section,
            responsive_section=responsive_section,
            animations_section=animations_section,
            implementation_notes=implementation_notes
        )
        
        return prompt.strip()
    
    def _generate_typography_section(self, tokens: Dict[str, Any]) -> str:
        """Generate typography section"""
        typography = tokens.get('typography_system', {})
        
        if not typography:
            return "- Use system fonts (Arial, Helvetica, sans-serif)\n- Standard web font sizes"
        
        section = []
        
        # Primary fonts
        fonts = typography.get('primary_fonts', [])
        if fonts:
            section.append(f"**Primary Fonts:**")
            for font in fonts[:3]:  # Top 3 fonts
                section.append(f"- {font}")
            section.append("")
        
        # Font sizes
        sizes = typography.get('font_sizes', [])
        if sizes:
            section.append(f"**Font Sizes:**")
            for size in sorted(sizes):
                section.append(f"- {size}px")
            section.append("")
        
        # Font weights
        weights = typography.get('font_weights', [])
        if weights:
            section.append(f"**Font Weights:**")
            for weight in sorted(set(weights)):
                section.append(f"- {weight}")
        
        return "\n".join(section) if section else "- Standard web typography"
    
    def _generate_color_section(self, tokens: Dict[str, Any]) -> str:
        """Generate color section"""
        colors = tokens.get('color_palette', {})
        
        if not colors:
            return "- Use standard web colors"
        
        section = []
        
        # Primary colors
        primary = colors.get('primary_colors', [])
        if primary:
            section.append("**Primary Colors:**")
            for i, color in enumerate(primary[:8]):  # Top 8 colors
                section.append(f"- Color {i+1}: `{color}`")
            section.append("")
        
        # CSS Custom Properties suggestion
        if primary:
            section.append("**CSS Custom Properties:**")
            section.append("```css")
            section.append(":root {")
            for i, color in enumerate(primary[:6]):
                var_name = self._color_to_css_var(color, i)
                section.append(f"  --{var_name}: {color};")
            section.append("}")
            section.append("```")
        
        return "\n".join(section) if section else "- Standard web colors"
    
    def _color_to_css_var(self, color: str, index: int) -> str:
        """Convert color to CSS variable name"""
        # Try to determine color type
        if 'rgb(0' in color or 'rgba(0' in color:
            return f"color-dark-{index+1}"
        elif 'rgb(255' in color or 'rgba(255' in color:
            return f"color-light-{index+1}"
        else:
            return f"color-primary-{index+1}"
    
    def _generate_spacing_section(self, tokens: Dict[str, Any]) -> str:
        """Generate spacing section"""
        spacing = tokens.get('spacing_scale', [])
        
        if not spacing:
            return "- Use standard spacing: 4px, 8px, 16px, 24px, 32px, 48px, 64px"
        
        section = []
        section.append("**Spacing Scale:**")
        
        # Group spacing values logically
        small_spacing = [s for s in spacing if s <= 8]
        medium_spacing = [s for s in spacing if 8 < s <= 32]
        large_spacing = [s for s in spacing if s > 32]
        
        if small_spacing:
            section.append(f"- Small: {', '.join(map(str, small_spacing))}px")
        if medium_spacing:
            section.append(f"- Medium: {', '.join(map(str, medium_spacing))}px")
        if large_spacing:
            section.append(f"- Large: {', '.join(map(str, large_spacing))}px")
        
        section.append("")
        section.append("**CSS Custom Properties:**")
        section.append("```css")
        section.append(":root {")
        for i, space in enumerate(spacing[:10]):  # Top 10 values
            section.append(f"  --space-{i+1}: {space}px;")
        section.append("}")
        section.append("```")
        
        return "\n".join(section)
    
    def _generate_components_section(self, tokens: Dict[str, Any]) -> str:
        """Generate components section"""
        components = tokens.get('components', {})
        
        if not components:
            return "- Standard web components (buttons, cards, navigation)"
        
        section = []
        
        for component_type, examples in components.items():
            if not examples:
                continue
                
            section.append(f"**{component_type.title()}:**")
            
            # Analyze common patterns
            common_styles = self._analyze_component_styles(examples)
            if common_styles:
                for style_key, style_value in common_styles.items():
                    section.append(f"- {style_key}: {style_value}")
            
            section.append("")
        
        return "\n".join(section) if section else "- Standard web components"
    
    def _analyze_component_styles(self, examples: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze common styles in component examples"""
        styles = {}
        
        # Analyze common patterns
        border_radii = []
        background_colors = []
        paddings = []
        
        for example in examples:
            # Border radius
            if example.get('borders', {}).get('borderRadius'):
                border_radii.append(example['borders']['borderRadius'])
            
            # Background color
            if example.get('colors', {}).get('backgroundColor'):
                bg = example['colors']['backgroundColor']
                if bg and 'rgba(0, 0, 0, 0)' not in bg:
                    background_colors.append(bg)
            
            # Padding
            if example.get('spacing', {}).get('padding'):
                paddings.extend(example['spacing']['padding'])
        
        # Most common values
        if border_radii:
            most_common_radius = max(set(border_radii), key=border_radii.count)
            styles['Border Radius'] = most_common_radius
        
        if background_colors:
            most_common_bg = max(set(background_colors), key=background_colors.count)
            styles['Background Color'] = most_common_bg
        
        if paddings:
            # Filter valid padding values
            valid_paddings = [p for p in paddings if p and 'px' in p]
            if valid_paddings:
                most_common_padding = max(set(valid_paddings), key=valid_paddings.count)
                styles['Padding'] = most_common_padding
        
        return styles
    
    def _generate_responsive_section(self, tokens: Dict[str, Any]) -> str:
        """Generate responsive section"""
        breakpoints = tokens.get('breakpoints', [])
        
        section = []
        section.append("**Responsive Breakpoints:**")
        
        if breakpoints:
            # Extract breakpoint values
            breakpoint_values = set()
            for bp in breakpoints:
                media_text = bp.get('mediaText', '')
                # Extract pixel values
                pixel_matches = re.findall(r'(\d+)px', media_text)
                for match in pixel_matches:
                    breakpoint_values.add(int(match))
            
            if breakpoint_values:
                sorted_breakpoints = sorted(breakpoint_values)
                for bp in sorted_breakpoints:
                    section.append(f"- {bp}px")
            else:
                section.append("- 768px (tablet)")
                section.append("- 1024px (desktop)")
        else:
            section.append("- 768px (tablet)")
            section.append("- 1024px (desktop)")
        
        section.append("")
        section.append("**Layout Notes:**")
        section.append("- Mobile-first approach")
        section.append("- Flexible grid system")
        section.append("- Scalable typography")
        
        return "\n".join(section)
    
    def _generate_animations_section(self, tokens: Dict[str, Any]) -> str:
        """Generate animations section"""
        animations = tokens.get('animations', {})
        
        if not animations:
            return "- Subtle hover transitions (0.2s ease-out)\n- Smooth scroll behavior"
        
        section = []
        
        # Keyframes
        keyframes = animations.get('keyframes', [])
        if keyframes:
            section.append("**Keyframe Animations:**")
            for kf in keyframes[:3]:  # Top 3 animations
                section.append(f"- {kf.get('name', 'unnamed')}")
            section.append("")
        
        # Active animations
        active_animations = animations.get('animations', [])
        if active_animations:
            section.append("**Active Animations:**")
            for anim in active_animations[:3]:
                name = anim.get('animationName', 'unnamed')
                duration = anim.get('duration', 'unknown')
                section.append(f"- {name} ({duration}ms)")
            section.append("")
        
        # Default recommendations
        section.append("**Recommended Transitions:**")
        section.append("- Hover effects: 0.2s ease-out")
        section.append("- Focus states: 0.1s ease-in")
        section.append("- Modal/overlay: 0.3s ease-in-out")
        
        return "\n".join(section)
    
    def _generate_implementation_notes(self, tokens: Dict[str, Any]) -> str:
        """Generate implementation-specific notes"""
        notes = []
        
        # Font loading
        typography = tokens.get('typography_system', {})
        if typography.get('primary_fonts'):
            notes.append("**Font Loading:**")
            notes.append("- Use `font-display: swap` for web fonts")
            notes.append("- Include fallback fonts in font-family declarations")
            notes.append("")
        
        # Color usage
        colors = tokens.get('color_palette', {})
        if colors.get('primary_colors'):
            notes.append("**Color Usage:**")
            notes.append("- Use CSS custom properties for consistent theming")
            notes.append("- Ensure WCAG AA contrast ratios")
            notes.append("- Consider dark mode variants")
            notes.append("")
        
        # Performance
        notes.append("**Performance:**")
        notes.append("- Optimize images with WebP format")
        notes.append("- Minimize CSS and JavaScript")
        notes.append("- Use CSS Grid/Flexbox instead of floats")
        notes.append("- Implement lazy loading for images")
        
        return "\n".join(notes)
    
    def save_prompt(self, prompt: str, output_path: Path):
        """Save generated prompt to file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print(f"✅ Prompt saved to: {output_path}")


def generate_prompt_from_tokens(tokens_file: Path, output_file: Path = None):
    """Generate prompt from saved design tokens"""
    if not tokens_file.exists():
        print(f"❌ Tokens file not found: {tokens_file}")
        return
    
    with open(tokens_file, 'r') as f:
        tokens = json.load(f)
    
    generator = PromptGenerator()
    prompt = generator.generate_prompt(tokens)
    
    if output_file is None:
        output_file = tokens_file.parent / "recreation_prompt.md"
    
    generator.save_prompt(prompt, output_file)
    return prompt


if __name__ == "__main__":
    # Example usage
    tokens_file = Path("extracted_designs/example.com/design_tokens.json")
    if tokens_file.exists():
        generate_prompt_from_tokens(tokens_file)
    else:
        print("Run design_extractor.py first to generate tokens")