# Mobile Order Page CSS Structure Analysis

## 📱 **Mobile CSS Architecture Overview**

The mobile CSS for the order page follows a **responsive-first approach** with specific breakpoints and mobile-first design patterns. Here's the detailed structure:

## 🎯 **Breakpoint System**

### Primary Breakpoints
```css
/* Tablet and below */
@media screen and (max-width: 990px) {
  /* Mobile sidebar and layout changes */
}

/* Mobile phones */
@media screen and (max-width: 768px) {
  /* General mobile adjustments */
}

/* Small mobile phones */
@media screen and (max-width: 480px) {
  /* Small mobile specific styles */
}
```

## 🏗️ **Mobile Layout Structure**

### 1. **Mobile Header & Navigation**
```css
.mobile-header {
  display: none; /* Hidden on desktop */
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background-color: rgb(var(--color-background));
  border-bottom: 0.1rem solid rgba(var(--color-foreground), 0.1);
  z-index: 100;
}

.burger-icon {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.5rem;
  cursor: pointer;
}
```

### 2. **Mobile Sidebar System**
```css
.mobile-sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 101;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.account-sidebar.mobile {
  position: fixed;
  top: 0;
  left: auto;
  right: -100%; /* Starts off-screen */
  width: 80%;
  max-width: 300px;
  height: 100vh;
  background-color: rgb(var(--color-background));
  z-index: 102;
  transition: right 0.3s ease;
  overflow-y: auto;
  padding: 1.5rem 1rem;
  box-shadow: 0 0 2rem rgba(0, 0, 0, 0.1);
}

.account-sidebar.mobile.active {
  left: auto;
  right: 0; /* Slides in from right */
}
```

## 📋 **Order Page Mobile Structure**

### 1. **Mobile Order Navigation**
```css
.mobile-order-nav {
  display: block !important; /* Only on mobile */
  width: 100%;
  margin-bottom: 2rem;
}

.desktop-order-nav {
  display: none !important; /* Hidden on mobile */
}

.mobile-order-tab-select {
  width: 100%;
  padding: 1rem 1.5rem;
  border: 0.1rem solid rgba(var(--color-foreground), 0.2);
  border-radius: var(--inputs-radius);
  background-color: rgb(var(--color-background));
  color: rgb(var(--color-foreground));
  font-size: 1.6rem;
  /* Custom dropdown arrow */
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg...");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  background-size: 1.5rem;
}
```

### 2. **Order Card Mobile Layout**
```css
/* General mobile order card */
.order-card {
  width: 100%;
  margin-bottom: 1.5rem;
  padding: 1.5rem;
}

/* Responsive grid for order cards */
.order-card-grid {
  grid-template-columns: 1fr; /* Single column on mobile */
  gap: 1rem;
}

/* Order card content structure */
.order-card > div[style*="display: flex"] {
  flex-direction: column !important; /* Stack vertically */
  gap: 1rem !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* Order details grid */
.order-card .subscription-grid {
  grid-template-columns: 1fr 1fr !important; /* 2 columns on mobile */
  gap: 0.3rem !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

.order-card .subscription-grid > div {
  min-width: 0 !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
  padding: 0 !important;
  margin: 0 !important;
  font-size: 0.9rem !important;
}
```

### 3. **Mobile Order Actions**
```css
.order-actions {
  display: flex !important;
  flex-direction: column !important; /* Stack buttons vertically */
  gap: 0.05rem !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* Button rows - 2 buttons per row */
.order-actions > div {
  display: flex !important;
  flex-direction: row !important;
  gap: 0.4rem !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

.order-actions button {
  flex: 0 1 auto !important;
  padding: 0.25rem 0.5rem !important;
  text-align: center !important;
  font-size: 0.7rem !important;
  min-width: 0 !important;
  box-sizing: border-box !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
```

### 4. **Mobile Order Content Styling**
```css
/* Items included section */
.order-card div[style*="background-color: rgba(var(--color-foreground), 0.04)"] {
  padding: 0.4rem !important;
  margin-bottom: 0.6rem !important;
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  font-size: 0.9rem !important;
}

/* Order status and header */
.order-card h4 {
  font-size: 1.1rem !important;
  line-height: 1.1 !important;
  margin-bottom: 0.4rem !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
}

.order-card p {
  font-size: 0.9rem !important;
  line-height: 1.1 !important;
  margin-bottom: 0.4rem !important;
  word-wrap: break-word !important;
  overflow-wrap: break-word !important;
}
```

## 📱 **Small Mobile Optimization (480px and below)**

### Edge-to-Edge Design
```css
.subscription-card {
  padding: 1rem 1.5rem !important;
  margin-bottom: 0.8rem !important;
  width: 100vw !important; /* Full viewport width */
  min-width: 100vw !important;
  max-width: 100vw !important;
  margin-left: calc(-0.8rem) !important; /* Negative margins */
  margin-right: calc(-0.8rem) !important;
  box-sizing: border-box !important;
}

/* All cards on small mobile */
.address-card,
.payment-method-card,
.order-card,
.subscription-card {
  margin-left: -0.8rem !important;
  margin-right: -0.8rem !important;
  padding-left: 0.8rem !important;
  padding-right: 0.8rem !important;
}
```

## 🎨 **CSS Custom Properties Usage**

The mobile CSS heavily relies on CSS custom properties for theming:
```css
--color-background: /* Main background */
--color-foreground: /* Main text color */
--color-button: /* Button color */
--buttons-radius: /* Border radius */
--inputs-radius: /* Input radius */
--media-radius: /* Media radius */
```

## 🔧 **Key Mobile Design Patterns**

### 1. **Progressive Enhancement**
- Desktop-first base styles
- Mobile overrides at specific breakpoints
- Graceful degradation for older devices

### 2. **Touch-Friendly Design**
- Larger tap targets (minimum 44px)
- Adequate spacing between interactive elements
- Optimized button sizes for thumbs

### 3. **Content Prioritization**
- Important information displayed first
- Secondary content collapsed or hidden
- Clear visual hierarchy

### 4. **Performance Optimization**
- Minimal use of complex selectors
- Efficient CSS specificity
- Optimized for mobile rendering

## 📱 **Mobile Order Page Structure Summary**

```
Mobile Header (990px breakpoint)
├── Burger Menu (hamburger icon)
├── Account Title
└── Mobile Sidebar (slides in from right)

Order Navigation
├── Mobile Dropdown (select element)
└── Desktop Tabs (hidden on mobile)

Order Cards
├── Single Column Layout
├── Stacked Content Structure
├── 2-Column Detail Grid
├── Vertical Button Layout
└── Touch-Friendly Actions

Small Mobile (480px)
├── Edge-to-Edge Design
├── Full Width Cards
├── Negative Margins
└── Optimized Spacing
```

## 🎯 **Recommendations for Mobile Order Page Changes**

### 1. **Maintain Breakpoint Structure**
- Keep existing breakpoints (990px, 768px, 480px)
- Use mobile-first approach for new styles
- Test across different screen sizes

### 2. **Preserve Touch Targets**
- Keep button sizes ≥44px
- Maintain adequate spacing
- Ensure accessibility

### 3. **Follow Existing Patterns**
- Use similar class naming conventions
- Maintain CSS custom properties
- Follow the established mobile layout patterns

### 4. **Optimize for Performance**
- Use efficient selectors
- Avoid unnecessary overrides
- Test on real mobile devices

This structure provides a solid foundation for making mobile-specific changes to the order page while maintaining consistency with the existing design system.