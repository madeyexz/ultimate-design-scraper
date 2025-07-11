const { chromium } = require('@playwright/test');
const fs = require('fs/promises');
const path = require('path');
const chroma = require('chroma-js');

async function extractDesign(url, outputDir = 'output') {
  console.log(`Extracting design from: ${url}`);
  
  // Create output directory
  await fs.mkdir(outputDir, { recursive: true });
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ 
    recordVideo: { dir: path.join(outputDir, 'videos') },
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  try {
    // 1. Navigation & wait for network idle
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    
    // 2. Full-page screenshot
    await page.screenshot({ 
      path: path.join(outputDir, 'page.png'), 
      fullPage: true 
    });

    // 3. HTML snapshot
    const html = await page.content();
    await fs.writeFile(path.join(outputDir, 'page.html'), html);

    // 4. Start CSS coverage (Chromium only)
    const client = await context.newCDPSession(page);
    await client.send('CSS.startRuleUsageTracking');

    // 5. Font & other assets tracking
    const assets = [];
    page.on('requestfinished', req => {
      if (['font', 'stylesheet', 'image'].includes(req.resourceType())) {
        assets.push({ 
          url: req.url(), 
          type: req.resourceType(),
          size: req.sizes()?.responseBodySize || 0
        });
      }
    });

    // 6. Extract viewport info and media queries
    const mediaQueries = await page.evaluate(() => {
      const queries = [];
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule.type === CSSRule.MEDIA_RULE) {
              queries.push(rule.conditionText);
            }
          }
        } catch (e) {
          // Skip cross-origin stylesheets
        }
      }
      return queries;
    });

    // 7. Grab computed tokens for visible nodes
    const tokens = await page.evaluate(() => {
      const visible = Array.from(document.querySelectorAll('*'))
        .filter(el => {
          const rect = el.getBoundingClientRect();
          const style = getComputedStyle(el);
          return rect.width * rect.height > 0 && 
                 style.display !== 'none' && 
                 style.visibility !== 'hidden';
        })
        .slice(0, 500); // cap for performance
      
      return visible.map(el => {
        const cs = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        
        return {
          tag: el.tagName.toLowerCase(),
          classes: el.className,
          id: el.id,
          rect: {
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height
          },
          typography: {
            fontFamily: cs.fontFamily,
            fontSize: cs.fontSize,
            fontWeight: cs.fontWeight,
            fontStyle: cs.fontStyle,
            lineHeight: cs.lineHeight,
            letterSpacing: cs.letterSpacing,
            textAlign: cs.textAlign,
            textTransform: cs.textTransform
          },
          colors: {
            color: cs.color,
            backgroundColor: cs.backgroundColor,
            borderColor: cs.borderColor
          },
          spacing: {
            margin: [cs.marginTop, cs.marginRight, cs.marginBottom, cs.marginLeft],
            padding: [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft]
          },
          layout: {
            display: cs.display,
            position: cs.position,
            flexDirection: cs.flexDirection,
            justifyContent: cs.justifyContent,
            alignItems: cs.alignItems,
            gridTemplateColumns: cs.gridTemplateColumns,
            gridTemplateRows: cs.gridTemplateRows
          },
          borders: {
            borderWidth: cs.borderWidth,
            borderStyle: cs.borderStyle,
            borderRadius: cs.borderRadius
          },
          effects: {
            boxShadow: cs.boxShadow,
            opacity: cs.opacity,
            transform: cs.transform,
            transition: cs.transition
          }
        };
      });
    });

    // 8. Extract color palette from computed styles
    const colors = tokens
      .flatMap(token => [token.colors.color, token.colors.backgroundColor, token.colors.borderColor])
      .filter(color => color && color !== 'rgba(0, 0, 0, 0)' && color !== 'transparent')
      .filter((color, index, arr) => arr.indexOf(color) === index); // unique colors

    // 9. Extract typography scale
    const fontSizes = tokens
      .map(token => parseFloat(token.typography.fontSize))
      .filter(size => !isNaN(size))
      .sort((a, b) => a - b)
      .filter((size, index, arr) => arr.indexOf(size) === index);

    const fontFamilies = tokens
      .map(token => token.typography.fontFamily)
      .filter((family, index, arr) => arr.indexOf(family) === index);

    // 10. Extract spacing scale
    const spacingValues = tokens
      .flatMap(token => [...token.spacing.margin, ...token.spacing.padding])
      .map(val => parseFloat(val))
      .filter(val => !isNaN(val) && val >= 0)
      .sort((a, b) => a - b)
      .filter((val, index, arr) => arr.indexOf(val) === index);

    // 11. Stop coverage & save used CSS
    const { ruleUsage } = await client.send('CSS.stopRuleUsageTracking');
    
    // 12. Save all extracted data
    const extractedData = {
      url,
      timestamp: new Date().toISOString(),
      viewport: { width: 1920, height: 1080 },
      mediaQueries,
      designTokens: {
        colors,
        typography: {
          fontFamilies,
          fontSizes
        },
        spacing: spacingValues
      },
      elements: tokens,
      assets,
      cssRules: ruleUsage
    };

    await fs.writeFile(
      path.join(outputDir, 'extracted-data.json'), 
      JSON.stringify(extractedData, null, 2)
    );

    console.log(`✅ Extraction complete for ${url}`);
    console.log(`📁 Output saved to: ${outputDir}`);
    console.log(`📊 Extracted ${tokens.length} elements`);
    console.log(`🎨 Found ${colors.length} colors`);
    console.log(`📝 Found ${fontFamilies.length} font families`);
    console.log(`📏 Found ${spacingValues.length} spacing values`);

    return extractedData;

  } catch (error) {
    console.error(`❌ Error extracting ${url}:`, error.message);
    throw error;
  } finally {
    await browser.close();
  }
}

// CLI usage
if (require.main === module) {
  const url = process.argv[2];
  const outputDir = process.argv[3] || 'output';
  
  if (!url) {
    console.error('Usage: node extract.js <url> [output-dir]');
    console.error('Example: node extract.js https://example.com output');
    process.exit(1);
  }
  
  extractDesign(url, outputDir)
    .then(() => process.exit(0))
    .catch(error => {
      console.error('Extraction failed:', error);
      process.exit(1);
    });
}

module.exports = { extractDesign };