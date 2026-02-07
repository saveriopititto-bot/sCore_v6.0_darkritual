# CSS Style Guide - style.css Organization

> 📝 **Session Updates:** [`../CHANGELOG_SESSION.md`](../CHANGELOG_SESSION.md)

## Navigation Map (Line Numbers)

### 1. Variables & Imports (Lines 1-28)
- Font imports
- CSS Custom Properties (`:root`)
- Color tier system for score-based styling

### 2. Global Styles (Lines 30-41)
- Base element styling (html, body)
- App container (`.stApp`)

### 3. Cards & Containers (Lines 43-86)
- `.glass-card` - Glass morphism effects
- Hover transitions and shimmer effects

### 4. Stat Circles (Lines 88-259)
- `.stat-circle` - Base circle styling
- `.stat-circle-zones` - Zone distribution circles  
- Tier-specific hover effects (epic, great, solid, weak)
- Progress circles
- Animations (pulse, float, glow)

### 5. Hover Labels (Lines 315-333)
- `.stat-label` - Smooth reveal animations

### 6. Buttons (Lines 335-390)
- Standard button styling
- Primary/secondary states
- Link buttons

### 7. Expanders & Popovers (Lines 392-475)
- `div[data-testid="stExpander"]` - Expander components
- Button-style expanders
- SVG icon hiding
- Open/closed states

### 8. Charts & Visualizations (Lines 475-520)
- Altair chart styling
- Data table styling

### 9. Forms & Inputs (Lines 520-580)
- Input fields
- Textareas
- Number inputs
- Date inputs

### 10. Layout Utilities (Lines 614-655)
- `.details-row` - Horizontal scrollable container
- Popover positioning

### 11. Responsive Breakpoints (Lines 540-580)
- Mobile (<768px)
- Tablet (768-1024px)
- Desktop adjustments

### 12. Scrollbars & Selection (Lines 600-627)
- Custom scrollbar styling
- Text selection colors

## CSS Variables Reference

### Colors
```css
--bg-primary: #ffffff
--bg-secondary: #f8f9fa
--text-primary: #1a1a1a
--text-secondary: #636E72
```

### Score Tiers
```css
--tier-epic: #CDFAD5 (green)
--tier-great: #F6FDC3 (yellow)
--tier-solid: #FFCF96 (orange)
--tier-weak: #FF8080 (red)
```

### Transitions
```css
--transition-smooth: all 0.4s cubic-bezier(0.4, 0, 0.2, 1)
--transition-bounce: all 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55)
```

## Naming Conventions

- **Component Classes**: `.component-name` (kebab-case)
- **Utility Classes**: `.utility-name` (kebab-case)
- **State Modifiers**: `[data-state="value"]` (data attributes)
- **Streamlit Selectors**: `div[data-testid="stComponent"]`

## Common Patterns

### Flexbox Centering
```css
display: flex;
align-items: center;
justify-content: center;
```

### Glass Effect
```css
background: #ffffff;
backdrop-filter: blur(20px) saturate(180%);
border: 1px solid rgba(0, 0, 0, 0.08);
```

### Hover Lift
```css
transition: transform 0.3s ease;
&:hover {
    transform: translateY(-4px);
}
```

## Maintenance Guidelines

1. **Adding New Styles**: Place in relevant section
2. **Color Changes**: Update CSS variables in `:root`
3. **Responsive**: Add breakpoints in Responsive section
4. **Testing**: Check mobile (<768px) and desktop (>1024px)

## Future Optimizations

- [ ] Extract navbar styles to separate section
- [ ] Create utility class library
- [ ] Consolidate duplicate flex patterns
- [ ] Add dark mode variables

---

## 🤖 Agent Task Reporting
**CSS Modification Rule:** Dopo ogni modifica CSS, l'agente DEVE documentare in `CHANGELOG_SESSION.md`:
- Selettori modificati con line numbers
- Breakpoint testati (mobile/tablet/desktop)
- Browser compatibility verificata
- Screenshot/video se cambio visivo significativo

