# Sprint 2: Design System & Theme Engine - Developer Guide

## Quick Start

### For Store Owners
```python
# Access theme management in dashboard
/dashboard/theme/              # Select preset
/dashboard/theme/customize/    # Customize colors/fonts
/dashboard/theme/custom-css/   # Add custom CSS
```

### For Platform Admins
```python
# Manage theme presets
/platform/theme-presets/       # List all presets
/platform/theme-presets/create/  # Create new preset
```

## Using Theme in Templates

### Storefront (automatic)
```html
{% load theme_tags %}
{% store_theme_css store %}
```

This injects a `<style>` block with all CSS variables.

### Using CSS Variables
```css
.my-button {
    background: var(--color-primary-500);
    color: white;
    border-radius: var(--radius-base);
    box-shadow: var(--shadow-base);
}

.my-button:hover {
    background: var(--color-primary-600);
}
```

## Available CSS Variables

### Color Scales (50-900 for each)
- `--color-primary-{50-900}`
- `--color-secondary-{50-900}`
- `--color-accent`

### Semantic Tokens
- `--button-bg-primary`
- `--button-bg-primary-hover`
- `--card-bg`
- `--text-heading`
- `--text-body`
- `--cta-color`

### Component Tokens
- `--btn-primary-bg`
- `--btn-primary-hover`
- `--input-border-focus`
- `--badge-success-bg`

### Typography
- `--font-heading`
- `--font-body`

### Spacing
- `--radius-base` (0, 0.25rem, 0.5rem, 0.75rem, 1rem, 9999px)
- `--shadow-base` (none, sm, md, lg, xl)

## Python API

### Generate Color Scale
```python
from core.theme_service import generate_color_scale

scale = generate_color_scale('#6366f1')
# Returns: {'50': '#f0f1fd', '100': '#e2e3fb', ..., '900': '#080a5d'}
```

### Validate Contrast
```python
from core.theme_service import validate_contrast

warnings = validate_contrast(theme)
# Returns list of WCAG AA warnings
```

### Compile Store CSS
```python
from core.theme_service import compile_store_css

css = compile_store_css(store)
# Returns full CSS variable block as string
```

### Sanitize Custom CSS
```python
from core.css_sanitizer import sanitize_css

sanitized, warnings = sanitize_css(raw_css)
# Returns (cleaned_css, list_of_warnings)
```

## Creating a Theme Preset (Admin)

```python
from core.models import ThemePreset

preset = ThemePreset.objects.create(
    name="My Theme",
    slug="my-theme",
    description="A custom theme",
    version="1.0.0",
    status=ThemePreset.Status.ACTIVE,
    tokens={
        "radius": "md",
        "shadow": "lg",
        "primary_color": "#6366f1",
    }
)
```

## Applying a Theme (Store)

```python
from core.models import StoreTheme, ThemePreset

# Get or create theme
theme, created = StoreTheme.objects.get_or_create(store=store)

# Apply preset
preset = ThemePreset.objects.get(slug='elegant')
theme.theme_preset = preset
theme.primary_color = '#8b5cf6'
theme.radius_scale = 'lg'
theme.save()
```

## Custom CSS Rules

Store owners can add custom CSS. It will be:
1. Sanitized (remove scripts, external URLs)
2. Size-limited (50KB max)
3. Appended after theme variables

Example:
```css
/* Custom store CSS */
.product-card {
    border: 2px solid var(--color-primary-300);
    padding: 1rem;
}

.sale-badge {
    background: var(--color-accent);
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-base);
}
```

## Architecture

### Token Hierarchy
```
Base Tokens (color scales, radius, shadow)
    ↓
Semantic Tokens (button-bg, text-color)
    ↓
Component Tokens (btn-primary, input-focus)
    ↓
Custom CSS (store-specific overrides)
```

### Model Relationships
```
ThemePreset (Platform) ←─┐
                          │ FK (nullable)
Store ──OneToOne──→ StoreTheme
```

### CSS Compilation Flow
```
1. Load StoreTheme from DB
2. Generate color scales (HSL math)
3. Build CSS variable block
4. Append sanitized custom CSS
5. Inject via {% store_theme_css store %}
```

## Security Considerations

### CSS Sanitization Removes:
- `<script>` tags
- `javascript:` URLs
- `expression()` functions
- External URLs in `url()` and `@import`

### Input Validation:
- Color values must be valid hex (#RRGGBB)
- CSS size limited to 50KB
- Font names limited to 100 chars

### Audit Logging:
All preset changes logged with:
- Actor (user)
- Action (created/updated/deprecated)
- Details (old/new values, affected stores)

## Management Commands

### Seed Theme Presets
```bash
python manage.py seed_theme_presets
```
Creates 4 default presets: Minimal, Bold Commerce, Elegant, Creator.

### Seed Platform (includes themes)
```bash
python manage.py seed_platform
```
Now automatically calls `seed_theme_presets`.

## Testing

```python
from django.test import TestCase
from core.models import Store, StoreTheme
from core.theme_service import compile_store_css

class ThemeTestCase(TestCase):
    def test_theme_css_generation(self):
        store = Store.objects.create(name="Test", username="test", owner=user)
        theme = StoreTheme.objects.create(store=store, primary_color="#6366f1")
        css = compile_store_css(store)
        self.assertIn("--color-primary-500", css)
```

## Troubleshooting

### Theme not appearing on storefront
1. Check `{% load theme_tags %}` at top of template
2. Ensure `{% store_theme_css store %}` is in `<head>`
3. Verify store is in context: `{{ store.name }}`

### Custom CSS not applying
1. Check sanitization warnings in dashboard
2. Ensure CSS is under 50KB
3. Remove external URLs/scripts
4. Use browser DevTools to verify CSS is injected

### Colors not matching
1. Verify hex color format (#RRGGBB)
2. Check contrast warnings in customize view
3. Test in different browsers for HSL support

## Future Enhancements

Potential Sprint 3+ features:
- Font upload support
- Theme preview before apply
- Export/import theme JSON
- A/B testing themes
- Dark mode variants
- Theme marketplace
- Responsive token overrides
- Animation tokens

---

**Version**: Sprint 2 (v1.0.0)  
**Last Updated**: 2024  
**Maintainer**: UltraShop Core Team
