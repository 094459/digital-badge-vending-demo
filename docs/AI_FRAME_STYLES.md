# AI Frame Generator Style Guide

## The Problem (Fixed!)

Previously, all AI-generated frames used the hardcoded `SOFT_DIGITAL_PAINTING` style, which resulted in floral/artistic designs regardless of your prompt. This has been fixed!

## What Changed

1. **Removed hardcoded style** - The system no longer forces a specific art style
2. **Added style selector** - You can now choose from 8 different art styles or let AI decide
3. **Better prompt handling** - Your prompt is now respected without adding unwanted descriptors

## Available Styles

### Auto (Recommended)
Leave the style dropdown as "Auto" to let the AI interpret your prompt naturally. This gives the most flexibility and often produces the best results.

### Style Options

- **Photographic** - Realistic, photo-like rendering. Great for professional, corporate frames.
- **Cinematic** - Movie-quality, dramatic lighting and composition. Good for prestigious awards.
- **Digital Art** - Modern digital illustration style. Works well for tech/creative badges.
- **Pop Art** - Bold, vibrant colors with high contrast. Great for energetic, modern designs.
- **Impressionist** - Artistic, painterly style with visible brushstrokes. Good for elegant, artistic badges.
- **Abstract** - Non-representational art with shapes and colors. Perfect for creative, unique designs.
- **Graffiti** - Street art style with bold lines and urban feel. Great for youth/creative community badges.
- **Sketch** - Hand-drawn appearance with pencil-like strokes. Good for informal, artistic badges.

## Example Prompts

### Geometric/Modern
```
Prompt: "A sleek geometric border with sharp angles and metallic silver finish"
Style: Digital Art or Photographic
```

### Professional/Corporate
```
Prompt: "A simple professional border with subtle corner accents in navy blue"
Style: Photographic or Auto
```

### Certificate Style
```
Prompt: "A formal certificate border with ribbon corners and gold trim"
Style: Photographic or Cinematic
```

### Tech/Gaming
```
Prompt: "A futuristic border with circuit board patterns and neon blue accents"
Style: Digital Art or Pop Art
```

### Minimalist
```
Prompt: "A thin elegant border with rounded corners, single color black line"
Style: Sketch or Auto
```

### Artistic/Creative
```
Prompt: "An ornate border with flowing curves and watercolor effects"
Style: Impressionist or Abstract
```

## Tips for Better Results

1. **Be specific** - Instead of "nice frame", say "thin gold border with art deco corners"
2. **Mention materials** - "brushed metal", "wood grain", "marble texture"
3. **Describe geometry** - "rounded corners", "sharp angles", "ornate curves"
4. **Specify colors** - "navy blue and gold", "monochrome black", "gradient purple"
5. **Try Auto first** - The AI is smart enough to interpret most prompts without style constraints

## Troubleshooting

**Still getting floral designs?**
- Make sure you're using the updated version (check that the Style dropdown exists)
- Try selecting "Sketch" or "Digital Art" for non-organic styles
- Be explicit: "geometric border, no flowers, no organic shapes"

**Getting validation errors?**
- The style values are specific to Amazon Bedrock Nova Canvas
- Valid styles: PHOTOGRAPHIC, CINEMATIC, DIGITAL_ART, POP_ART, IMPRESSIONIST, ABSTRACT, GRAFFITI, SKETCH
- If you see an error, try "Auto" or a different style

**Frame not transparent in center?**
- This is handled automatically by post-processing
- The center 70% of the image is made transparent after generation
