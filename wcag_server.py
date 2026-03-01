"""
WCAG 2.2 MCP Server — Level A & AA
Provides tools for accessibility auditing, criterion lookup, color contrast checking,
accessible code generation, and fix suggestions.
"""

import json
import re
import math
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WCAG 2.2 Accessibility Server")

# ─────────────────────────────────────────────
# WCAG 2.2 Knowledge Base (Level A + AA = 56 criteria)
# ─────────────────────────────────────────────
WCAG_CRITERIA = {
    # ── PRINCIPLE 1: PERCEIVABLE ──────────────────────────────────────────
    # Guideline 1.1 – Text Alternatives
    "1.1.1": {
        "title": "Non-text Content",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Text Alternatives",
        "description": "All non-text content presented to the user has a text alternative that serves the equivalent purpose.",
        "applies_to": "Images, icons, buttons with images, CAPTCHA, decorative images",
        "how_to_meet": [
            "Add meaningful alt text to <img> elements: <img alt='Description'>",
            "Use alt='' for purely decorative images",
            "Provide text labels for icon-only buttons: <button aria-label='Close'>",
            "For complex images (charts/graphs), provide a long description",
            "For CAPTCHA, provide an audio alternative",
        ],
        "common_failures": [
            "Missing alt attribute on <img>",
            "Uninformative alt text like 'image' or 'photo'",
            "No label on icon-only buttons",
        ],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-content",
    },
    # Guideline 1.2 – Time-based Media
    "1.2.1": {
        "title": "Audio-only and Video-only (Prerecorded)",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Time-based Media",
        "description": "Prerecorded audio-only and video-only content has a text transcript or audio description.",
        "applies_to": "Podcasts, recorded videos without audio track, audio clips",
        "how_to_meet": [
            "Provide a text transcript for audio-only content",
            "Provide a text description for video-only content",
            "Link to transcript near the media element",
        ],
        "common_failures": ["No transcript for podcast episodes", "Video with no audio track and no text description"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/audio-only-and-video-only-prerecorded",
    },
    "1.2.2": {
        "title": "Captions (Prerecorded)",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Time-based Media",
        "description": "Captions are provided for all prerecorded audio content in synchronized media.",
        "applies_to": "Videos with audio track",
        "how_to_meet": [
            "Add <track kind='captions'> to <video> elements",
            "Provide .vtt or .srt caption files",
            "Ensure captions include all speech and important non-speech sounds",
        ],
        "common_failures": ["Video with no captions", "Auto-generated captions not reviewed for accuracy"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/captions-prerecorded",
    },
    "1.2.3": {
        "title": "Audio Description or Media Alternative (Prerecorded)",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Time-based Media",
        "description": "Audio description or full text alternative is provided for synchronized media.",
        "applies_to": "Videos with visual information not conveyed by audio",
        "how_to_meet": [
            "Add <track kind='descriptions'> with audio description file",
            "Provide a text transcript as an alternative",
            "Offer a version of video with audio descriptions embedded",
        ],
        "common_failures": ["Video with important visual content and no audio description"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/audio-description-or-media-alternative-prerecorded",
    },
    "1.2.4": {
        "title": "Captions (Live)",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Time-based Media",
        "description": "Captions are provided for all live audio content in synchronized media.",
        "applies_to": "Live streams, webinars, video calls",
        "how_to_meet": [
            "Use real-time captioning service (CART)",
            "Enable live caption feature if platform supports it",
        ],
        "common_failures": ["Live webinar with no captions"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/captions-live",
    },
    "1.2.5": {
        "title": "Audio Description (Prerecorded)",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Time-based Media",
        "description": "Audio description is provided for all prerecorded video content.",
        "applies_to": "Recorded videos",
        "how_to_meet": [
            "Add audio descriptions via <track kind='descriptions'>",
            "Create alternate version with narrated descriptions of visual content",
        ],
        "common_failures": ["Training video with visual-only demonstrations and no audio description"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/audio-description-prerecorded",
    },
    # Guideline 1.3 – Adaptable
    "1.3.1": {
        "title": "Info and Relationships",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Adaptable",
        "description": "Information, structure, and relationships conveyed through presentation can be programmatically determined.",
        "applies_to": "Headings, lists, tables, forms, emphasis",
        "how_to_meet": [
            "Use semantic HTML: <h1>-<h6>, <ul>, <ol>, <table>, <form>",
            "Use <th> for table headers with scope attribute",
            "Use <label> elements associated with form inputs",
            "Use ARIA roles when semantic HTML isn't possible",
        ],
        "common_failures": [
            "Using <div> styled as heading instead of <h1>-<h6>",
            "Table with no <th> elements",
            "Form fields without <label>",
        ],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships",
    },
    "1.3.2": {
        "title": "Meaningful Sequence",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Adaptable",
        "description": "If reading sequence affects meaning, a correct reading order can be programmatically determined.",
        "applies_to": "Multi-column layouts, CSS-positioned content",
        "how_to_meet": [
            "Ensure DOM order matches visual reading order",
            "Don't use CSS to visually reorder content in a misleading way",
        ],
        "common_failures": ["Content visually reordered with CSS float/position but DOM order is illogical"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/meaningful-sequence",
    },
    "1.3.3": {
        "title": "Sensory Characteristics",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Adaptable",
        "description": "Instructions don't rely solely on sensory characteristics like shape, color, size, location, or sound.",
        "applies_to": "Instructions, help text, UI guidance",
        "how_to_meet": [
            "Avoid 'click the green button' — add a text label too",
            "Avoid 'see the box on the right' — provide a heading or label",
        ],
        "common_failures": ["Instructions say 'click the round button' with no additional text"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/sensory-characteristics",
    },
    "1.3.4": {
        "title": "Orientation",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Adaptable",
        "description": "Content doesn't restrict view/operation to a single orientation unless essential.",
        "applies_to": "Mobile apps, responsive web pages",
        "how_to_meet": [
            "Don't lock orientation via CSS or JS",
            "Test both portrait and landscape on mobile",
            "Remove: <meta name='viewport' content='...user-scalable=no'>",
        ],
        "common_failures": ["Locking orientation to portrait/landscape with CSS/JS"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/orientation",
    },
    "1.3.5": {
        "title": "Identify Input Purpose",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Adaptable",
        "description": "The purpose of each input field collecting personal information can be programmatically determined.",
        "applies_to": "Login forms, contact forms, checkout forms",
        "how_to_meet": [
            "Use autocomplete attribute: <input autocomplete='email'>",
            "Common values: name, email, tel, bday, street-address, postal-code, country",
        ],
        "common_failures": ["Form inputs missing autocomplete attribute for personal data fields"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/identify-input-purpose",
    },
    # Guideline 1.4 – Distinguishable
    "1.4.1": {
        "title": "Use of Color",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "Color is not used as the only visual means of conveying information.",
        "applies_to": "Charts, form validation, links, status indicators",
        "how_to_meet": [
            "Add icons or text labels alongside color indicators",
            "Underline links rather than relying on color alone",
            "Add patterns to charts in addition to colors",
        ],
        "common_failures": ["Required form fields shown only with a red border", "Links distinguished only by color"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/use-of-color",
    },
    "1.4.2": {
        "title": "Audio Control",
        "level": "A",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "Audio playing automatically for more than 3 seconds must be controllable.",
        "applies_to": "Auto-playing audio/video",
        "how_to_meet": [
            "Provide pause/stop button for auto-playing audio",
            "Provide volume control independent of system volume",
            "Better yet, don't auto-play audio",
        ],
        "common_failures": ["Background music auto-plays with no way to stop it"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/audio-control",
    },
    "1.4.3": {
        "title": "Contrast (Minimum)",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "Text has a contrast ratio of at least 4.5:1 (3:1 for large text 18pt/14pt bold).",
        "applies_to": "All text content",
        "how_to_meet": [
            "Use contrast checker tools to verify color pairs",
            "Normal text: minimum 4.5:1 ratio",
            "Large text (18pt+ or 14pt+ bold): minimum 3:1 ratio",
            "Exceptions: decorative text, logos, inactive UI components",
        ],
        "common_failures": ["Light gray text on white background", "Yellow text on white background"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum",
    },
    "1.4.4": {
        "title": "Resize Text",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "Text can be resized up to 200% without loss of content or functionality.",
        "applies_to": "All web pages",
        "how_to_meet": [
            "Use relative units (em, rem, %) instead of fixed px for font sizes",
            "Test page at 200% browser zoom",
            "Ensure no horizontal scrolling or content overlap at 200%",
        ],
        "common_failures": [
            "Fixed pixel font sizes that don't scale with browser zoom",
            "Content overflows or disappears at 200% zoom",
        ],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/resize-text",
    },
    "1.4.5": {
        "title": "Images of Text",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "Text is used instead of images of text where possible.",
        "applies_to": "Logos, banners, decorative text",
        "how_to_meet": [
            "Use actual HTML text styled with CSS instead of text images",
            "If image of text is essential (logos), provide alt text",
        ],
        "common_failures": ["Navigation menu items as images of text"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/images-of-text",
    },
    "1.4.10": {
        "title": "Reflow",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "Content can be presented without scrolling in two directions at 320 CSS pixels wide.",
        "applies_to": "All web pages",
        "how_to_meet": [
            "Use responsive design (CSS flexbox/grid)",
            "Test at 320px viewport width",
            "Avoid fixed-width containers that cause horizontal scroll",
        ],
        "common_failures": ["Fixed-width layout requiring horizontal scrolling at mobile size"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/reflow",
    },
    "1.4.11": {
        "title": "Non-text Contrast",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "UI components and graphical objects have a contrast ratio of at least 3:1.",
        "applies_to": "Form input borders, focus indicators, icons, charts",
        "how_to_meet": [
            "Input borders must have 3:1 contrast against background",
            "Icons that convey meaning must have 3:1 contrast",
            "Chart colors must have 3:1 contrast against adjacent colors",
        ],
        "common_failures": ["Light gray input border on white background", "Low-contrast icon buttons"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast",
    },
    "1.4.12": {
        "title": "Text Spacing",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "No loss of content when text spacing is overridden (line height 1.5x, letter/word spacing, paragraph spacing 2x).",
        "applies_to": "All text content",
        "how_to_meet": [
            "Don't use fixed-height containers that clip overflow text",
            "Test with bookmarklet that injects spacing overrides",
            "Use min-height instead of height for text containers",
        ],
        "common_failures": ["Fixed-height containers that clip text when spacing is increased"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/text-spacing",
    },
    "1.4.13": {
        "title": "Content on Hover or Focus",
        "level": "AA",
        "principle": "Perceivable",
        "guideline": "Distinguishable",
        "description": "Additional content shown on hover/focus is dismissible, hoverable, and persistent.",
        "applies_to": "Tooltips, custom dropdowns, popovers",
        "how_to_meet": [
            "User can dismiss tooltip without moving pointer (e.g., Escape key)",
            "User can move pointer to tooltip without it disappearing",
            "Content stays visible until dismissed or trigger loses focus",
        ],
        "common_failures": ["Tooltip disappears when moving pointer from trigger to tooltip text"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus",
    },
    # ── PRINCIPLE 2: OPERABLE ─────────────────────────────────────────────
    # Guideline 2.1 – Keyboard Accessible
    "2.1.1": {
        "title": "Keyboard",
        "level": "A",
        "principle": "Operable",
        "guideline": "Keyboard Accessible",
        "description": "All functionality is operable via keyboard without requiring specific timing.",
        "applies_to": "All interactive elements",
        "how_to_meet": [
            "Ensure all interactive elements are focusable and operable with keyboard",
            "Tab to all controls, Enter/Space to activate buttons",
            "Arrow keys for widget navigation (menus, sliders, etc.)",
            "Avoid relying on mouse-only events (mouseover, drag)",
        ],
        "common_failures": [
            "Custom widget only operable by mouse",
            "Drag-and-drop with no keyboard alternative",
        ],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/keyboard",
    },
    "2.1.2": {
        "title": "No Keyboard Trap",
        "level": "A",
        "principle": "Operable",
        "guideline": "Keyboard Accessible",
        "description": "Keyboard focus is not trapped in a component unless it's a modal dialog.",
        "applies_to": "Modals, date pickers, custom widgets",
        "how_to_meet": [
            "Ensure Tab can always exit a component",
            "Modal dialogs should trap focus but provide clear close mechanism (Escape)",
            "Document any non-standard navigation method",
        ],
        "common_failures": ["Focus trapped in a widget with no way to exit using keyboard"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/no-keyboard-trap",
    },
    "2.1.4": {
        "title": "Character Key Shortcuts",
        "level": "A",
        "principle": "Operable",
        "guideline": "Keyboard Accessible",
        "description": "Single-character keyboard shortcuts can be turned off, remapped, or only active on focus.",
        "applies_to": "Apps with keyboard shortcuts",
        "how_to_meet": [
            "Allow users to disable single-key shortcuts in settings",
            "Allow remapping shortcuts to include modifier keys (Ctrl, Alt)",
            "Only activate shortcut when a relevant component has focus",
        ],
        "common_failures": ["Single-key shortcuts active globally that conflict with AT commands"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts",
    },
    # Guideline 2.2 – Enough Time
    "2.2.1": {
        "title": "Timing Adjustable",
        "level": "A",
        "principle": "Operable",
        "guideline": "Enough Time",
        "description": "Time limits can be turned off, adjusted, or extended.",
        "applies_to": "Session timeouts, timed forms, auto-advancing slideshows",
        "how_to_meet": [
            "Warn user before timeout with option to extend",
            "Allow at least 20 seconds to respond to extension prompt",
            "Provide option to turn off or increase time limit",
        ],
        "common_failures": ["Session times out with no warning or option to extend"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable",
    },
    "2.2.2": {
        "title": "Pause, Stop, Hide",
        "level": "A",
        "principle": "Operable",
        "guideline": "Enough Time",
        "description": "Moving, blinking, scrolling, or auto-updating content can be paused, stopped, or hidden.",
        "applies_to": "Carousels, animations, news tickers, live feeds",
        "how_to_meet": [
            "Provide pause button for carousels and animations",
            "Provide stop button for content that auto-updates",
            "Use CSS prefers-reduced-motion media query",
        ],
        "common_failures": ["Auto-playing carousel with no pause control"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide",
    },
    # Guideline 2.3 – Seizures and Physical Reactions
    "2.3.1": {
        "title": "Three Flashes or Below Threshold",
        "level": "A",
        "principle": "Operable",
        "guideline": "Seizures and Physical Reactions",
        "description": "Content doesn't flash more than 3 times per second, or flash is below thresholds.",
        "applies_to": "Animations, videos, interactive content",
        "how_to_meet": [
            "Avoid flashing content entirely if possible",
            "If needed, keep flashing below 3 Hz",
            "Test with Photosensitive Epilepsy Analysis Tool (PEAT)",
        ],
        "common_failures": ["Rapid flashing animation on page load"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold",
    },
    # Guideline 2.4 – Navigable
    "2.4.1": {
        "title": "Bypass Blocks",
        "level": "A",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "A mechanism exists to skip past repeated blocks of content.",
        "applies_to": "Navigation menus, repeated header content",
        "how_to_meet": [
            "Add 'Skip to main content' link as first element in <body>",
            "Use ARIA landmarks: <header>, <nav>, <main>, <footer>",
            "Provide page navigation links at the top",
        ],
        "common_failures": ["No skip navigation link or landmark regions"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks",
    },
    "2.4.2": {
        "title": "Page Titled",
        "level": "A",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "Web pages have titles that describe the topic or purpose.",
        "applies_to": "All web pages",
        "how_to_meet": [
            "Add descriptive <title> to every page",
            "Format: 'Page Name | Site Name'",
            "Titles should be unique across pages",
        ],
        "common_failures": ["Missing <title>", "All pages have the same generic title"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/page-titled",
    },
    "2.4.3": {
        "title": "Focus Order",
        "level": "A",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "Focusable components receive focus in an order that preserves meaning and operability.",
        "applies_to": "All interactive elements",
        "how_to_meet": [
            "Ensure DOM order is logical",
            "Avoid positive tabindex values that override natural order",
            "Test with Tab key through the entire page",
        ],
        "common_failures": ["tabindex values create unexpected focus order", "DOM order doesn't match visual order"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/focus-order",
    },
    "2.4.4": {
        "title": "Link Purpose (In Context)",
        "level": "A",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "The purpose of each link can be determined from its text or surrounding context.",
        "applies_to": "All links",
        "how_to_meet": [
            "Use descriptive link text: 'Download report' not 'Click here'",
            "For ambiguous links, use aria-label or aria-describedby",
            "Context: text in same <p>, <li>, <td>, or heading",
        ],
        "common_failures": [
            "Multiple 'Read more' links with no context",
            "Link text is just a URL",
        ],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context",
    },
    "2.4.5": {
        "title": "Multiple Ways",
        "level": "AA",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "More than one way to locate a page within a set of pages.",
        "applies_to": "Multi-page websites",
        "how_to_meet": [
            "Provide site search",
            "Provide site map",
            "Provide navigation menu",
            "Any two of: search, sitemap, nav, table of contents, related links",
        ],
        "common_failures": ["Single-page app with no search or nav aside from back button"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/multiple-ways",
    },
    "2.4.6": {
        "title": "Headings and Labels",
        "level": "AA",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "Headings and labels describe the topic or purpose.",
        "applies_to": "All headings and form labels",
        "how_to_meet": [
            "Use descriptive headings that convey page structure",
            "Avoid vague headings like 'More' or 'Section 1'",
            "Form labels should clearly describe the input purpose",
        ],
        "common_failures": ["Generic or ambiguous heading text"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels",
    },
    "2.4.7": {
        "title": "Focus Visible",
        "level": "AA",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "Keyboard focus indicator is visible.",
        "applies_to": "All focusable elements",
        "how_to_meet": [
            "Never use outline: none without a custom focus indicator",
            "CSS: :focus { outline: 2px solid blue; }",
            "Ensure focus indicator has sufficient contrast (see 2.4.11)",
        ],
        "common_failures": ["outline: none or outline: 0 in CSS with no replacement"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/focus-visible",
    },
    "2.4.11": {
        "title": "Focus Not Obscured (Minimum)",
        "level": "AA",
        "principle": "Operable",
        "guideline": "Navigable",
        "description": "When a component receives keyboard focus, at least part of it is not hidden by other content.",
        "applies_to": "Pages with sticky headers/footers, modals",
        "how_to_meet": [
            "Add scroll-padding-top to compensate for sticky headers",
            "css: html { scroll-padding-top: 80px; }",
            "Ensure focused elements scroll into view with clearance",
        ],
        "common_failures": ["Sticky header covers focused element completely"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum",
    },
    # Guideline 2.5 – Input Modalities
    "2.5.1": {
        "title": "Pointer Gestures",
        "level": "A",
        "principle": "Operable",
        "guideline": "Input Modalities",
        "description": "All functionality using multipoint or path-based gestures has a single-pointer alternative.",
        "applies_to": "Maps, sliders, carousels using gestures",
        "how_to_meet": [
            "Provide buttons as alternatives to swipe gestures",
            "Provide click alternatives to pinch-zoom gestures",
        ],
        "common_failures": ["Map requiring pinch-zoom with no +/- zoom buttons"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/pointer-gestures",
    },
    "2.5.2": {
        "title": "Pointer Cancellation",
        "level": "A",
        "principle": "Operable",
        "guideline": "Input Modalities",
        "description": "Functionality triggered on single pointer can be cancelled or reversed.",
        "applies_to": "Buttons, links, custom controls",
        "how_to_meet": [
            "Use mouseup/pointerup for activation, not mousedown/pointerdown",
            "Allow aborting by moving pointer off target before releasing",
        ],
        "common_failures": ["Button activates on mousedown with no ability to cancel"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/pointer-cancellation",
    },
    "2.5.3": {
        "title": "Label in Name",
        "level": "A",
        "principle": "Operable",
        "guideline": "Input Modalities",
        "description": "UI components with visible text labels contain the visible text in their accessible name.",
        "applies_to": "All interactive elements with visible labels",
        "how_to_meet": [
            "Accessible name must contain the visible label text",
            "Don't override with aria-label that doesn't include visible text",
            "aria-label='Submit form' is fine if button says 'Submit'",
        ],
        "common_failures": ["aria-label='Close dialog' on button that says 'X' (different, but X is not text)"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/label-in-name",
    },
    "2.5.4": {
        "title": "Motion Actuation",
        "level": "A",
        "principle": "Operable",
        "guideline": "Input Modalities",
        "description": "Functionality triggered by device motion has a UI alternative and can be disabled.",
        "applies_to": "Shake to undo, tilt to scroll features",
        "how_to_meet": [
            "Provide UI button alternatives to motion-triggered actions",
            "Allow user to disable motion actuation",
        ],
        "common_failures": ["Shake to undo with no other way to undo"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/motion-actuation",
    },
    "2.5.7": {
        "title": "Dragging Movements",
        "level": "AA",
        "principle": "Operable",
        "guideline": "Input Modalities",
        "description": "All functionality using dragging has a single-pointer alternative.",
        "applies_to": "Drag-and-drop interfaces, sliders",
        "how_to_meet": [
            "Provide click/tap alternatives for all drag operations",
            "Keyboard accessible drag operations",
            "For sliders: ensure arrow key operation works",
        ],
        "common_failures": ["Kanban board with drag-only card movement"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements",
    },
    "2.5.8": {
        "title": "Target Size (Minimum)",
        "level": "AA",
        "principle": "Operable",
        "guideline": "Input Modalities",
        "description": "Target size is at least 24x24 CSS pixels, or sufficient spacing exists around smaller targets.",
        "applies_to": "Buttons, links, checkboxes, touch targets",
        "how_to_meet": [
            "Make interactive targets at least 24x24 CSS pixels",
            "Or ensure 24px offset from adjacent targets",
            "Recommended: aim for 44x44 pixels for comfortable touch",
        ],
        "common_failures": ["Small icon buttons with no padding or spacing"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum",
    },
    # ── PRINCIPLE 3: UNDERSTANDABLE ───────────────────────────────────────
    # Guideline 3.1 – Readable
    "3.1.1": {
        "title": "Language of Page",
        "level": "A",
        "principle": "Understandable",
        "guideline": "Readable",
        "description": "The default human language of each page can be programmatically determined.",
        "applies_to": "All web pages",
        "how_to_meet": [
            "<html lang='en'> (use correct BCP 47 language code)",
            "Examples: lang='fr' for French, lang='de' for German, lang='ja' for Japanese",
        ],
        "common_failures": ["Missing lang attribute on <html>", "Wrong language code"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/language-of-page",
    },
    "3.1.2": {
        "title": "Language of Parts",
        "level": "AA",
        "principle": "Understandable",
        "guideline": "Readable",
        "description": "Language of each passage or phrase can be programmatically determined.",
        "applies_to": "Multilingual pages, foreign words/phrases",
        "how_to_meet": [
            "Mark language changes with lang attribute: <span lang='fr'>Bonjour</span>",
            "Technical terms, proper nouns, and common words don't need marking",
        ],
        "common_failures": ["French paragraph in English page without lang='fr'"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/language-of-parts",
    },
    # Guideline 3.2 – Predictable
    "3.2.1": {
        "title": "On Focus",
        "level": "A",
        "principle": "Understandable",
        "guideline": "Predictable",
        "description": "Receiving focus doesn't automatically trigger a context change.",
        "applies_to": "Form elements, interactive components",
        "how_to_meet": [
            "Don't submit forms when a field receives focus",
            "Don't navigate to a new page on focus",
            "Only trigger context changes on explicit user activation",
        ],
        "common_failures": ["Select menu navigates to page as soon as option is focused"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/on-focus",
    },
    "3.2.2": {
        "title": "On Input",
        "level": "A",
        "principle": "Understandable",
        "guideline": "Predictable",
        "description": "Changing a UI component setting doesn't automatically cause a context change unless the user is advised.",
        "applies_to": "Form controls, settings toggles",
        "how_to_meet": [
            "Don't auto-submit form on change events without warning",
            "Don't auto-navigate on radio button change",
            "Use submit buttons rather than onChange navigation",
        ],
        "common_failures": ["Selecting a radio button immediately navigates to a new page"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/on-input",
    },
    "3.2.3": {
        "title": "Consistent Navigation",
        "level": "AA",
        "principle": "Understandable",
        "guideline": "Predictable",
        "description": "Navigation that repeats on multiple pages occurs in the same relative order.",
        "applies_to": "Site navigation, repeated UI patterns",
        "how_to_meet": [
            "Keep navigation menu items in the same order across all pages",
            "Don't reorder navigation based on current page",
        ],
        "common_failures": ["Navigation items in different order on different pages"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/consistent-navigation",
    },
    "3.2.4": {
        "title": "Consistent Identification",
        "level": "AA",
        "principle": "Understandable",
        "guideline": "Predictable",
        "description": "Components with the same functionality are identified consistently.",
        "applies_to": "Repeated UI components across pages",
        "how_to_meet": [
            "Use same label/icon/alt text for same functionality across pages",
            "Search button should always be labeled 'Search', not sometimes 'Find'",
        ],
        "common_failures": ["Same button labeled differently on different pages"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification",
    },
    "3.2.6": {
        "title": "Consistent Help",
        "level": "AA",
        "principle": "Understandable",
        "guideline": "Predictable",
        "description": "Help mechanisms are in the same location across pages.",
        "applies_to": "Help links, contact info, support chat",
        "how_to_meet": [
            "Place help/contact in same position on every page (e.g., always in footer)",
            "Consistent order in navigation if help is a nav item",
        ],
        "common_failures": ["Help link in header on some pages, footer on others"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/consistent-help",
    },
    # Guideline 3.3 – Input Assistance
    "3.3.1": {
        "title": "Error Identification",
        "level": "A",
        "principle": "Understandable",
        "guideline": "Input Assistance",
        "description": "Input errors are automatically detected and described in text.",
        "applies_to": "Forms, data entry",
        "how_to_meet": [
            "Describe errors in text, not just with color or icon",
            "Identify which field has the error",
            "Use aria-describedby to connect error message to input",
            "<span id='err'>Email is required</span> + aria-describedby='err'",
        ],
        "common_failures": ["Red border on field with no text describing the error"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/error-identification",
    },
    "3.3.2": {
        "title": "Labels or Instructions",
        "level": "A",
        "principle": "Understandable",
        "guideline": "Input Assistance",
        "description": "Labels or instructions are provided when content requires user input.",
        "applies_to": "All form fields",
        "how_to_meet": [
            "Provide visible label for every form field",
            "Include format instructions: 'Date (MM/DD/YYYY)'",
            "Indicate required fields",
        ],
        "common_failures": ["Form field with only placeholder text (no visible label)"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions",
    },
    "3.3.3": {
        "title": "Error Suggestion",
        "level": "AA",
        "principle": "Understandable",
        "guideline": "Input Assistance",
        "description": "Error messages provide suggestions for correction if possible.",
        "applies_to": "Form validation",
        "how_to_meet": [
            "Tell users how to fix the error: 'Enter a valid email address (e.g., name@example.com)'",
            "For constrained fields, tell user the constraints",
        ],
        "common_failures": ["Error message says 'Invalid input' with no guidance"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion",
    },
    "3.3.4": {
        "title": "Error Prevention (Legal, Financial, Data)",
        "level": "AA",
        "principle": "Understandable",
        "guideline": "Input Assistance",
        "description": "For important transactions: submissions are reversible, checked for errors, or confirmed.",
        "applies_to": "Checkout, account deletion, legal agreements, financial transactions",
        "how_to_meet": [
            "Provide review step before final submission",
            "Allow cancellation or reversal of actions",
            "Show confirmation dialog for irreversible actions",
        ],
        "common_failures": ["One-click purchase with no confirmation step"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data",
    },
    "3.3.7": {
        "title": "Redundant Entry",
        "level": "A",
        "principle": "Understandable",
        "guideline": "Input Assistance",
        "description": "Information entered previously is auto-populated or available for selection.",
        "applies_to": "Multi-step forms, checkout flows",
        "how_to_meet": [
            "Pre-fill fields with previously entered data",
            "Add 'same as billing address' checkbox for shipping",
            "Don't ask users to re-enter information they already provided",
        ],
        "common_failures": ["Multi-step form asks user to re-enter name on every step"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry",
    },
    "3.3.8": {
        "title": "Accessible Authentication (Minimum)",
        "level": "AA",
        "principle": "Understandable",
        "guideline": "Input Assistance",
        "description": "Authentication doesn't require cognitive tests unless an alternative is provided.",
        "applies_to": "Login, CAPTCHA, security questions",
        "how_to_meet": [
            "Allow password manager use (don't block paste)",
            "Provide alternative to CAPTCHA (email link, SMS code)",
            "Support passkeys and SSO authentication",
        ],
        "common_failures": ["Login form that blocks paste (prevents password managers)"],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum",
    },
    # ── PRINCIPLE 4: ROBUST ───────────────────────────────────────────────
    # Guideline 4.1 – Compatible
    "4.1.2": {
        "title": "Name, Role, Value",
        "level": "A",
        "principle": "Robust",
        "guideline": "Compatible",
        "description": "All UI components have an accessible name, role, and state/property/value.",
        "applies_to": "All interactive and custom UI elements",
        "how_to_meet": [
            "Use semantic HTML elements that have built-in roles",
            "For custom widgets, add role, aria-label, and aria-* states",
            "Buttons: <button> has role=button automatically",
            "Custom toggle: <div role='switch' aria-checked='false' aria-label='Dark mode'>",
        ],
        "common_failures": [
            "Custom button using <div> with no role='button'",
            "Icon button with no accessible name",
        ],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/name-role-value",
    },
    "4.1.3": {
        "title": "Status Messages",
        "level": "AA",
        "principle": "Robust",
        "guideline": "Compatible",
        "description": "Status messages can be programmatically determined through role or property.",
        "applies_to": "Alerts, notifications, success messages, loading indicators",
        "how_to_meet": [
            "Use aria-live='polite' for non-urgent status updates",
            "Use role='alert' or aria-live='assertive' for urgent messages",
            "Use role='status' for progress or success messages",
        ],
        "common_failures": [
            "Success message appears visually but not announced to screen reader",
            "Loading spinner with no aria-live region",
        ],
        "wcag_url": "https://www.w3.org/WAI/WCAG22/Understanding/status-messages",
    },
}

# ─────────────────────────────────────────────
# TOOL 1: Lookup a criterion by ID
# ─────────────────────────────────────────────
@mcp.tool()
def lookup_criterion(criterion_id: str) -> str:
    """
    Look up a WCAG 2.2 success criterion by its ID (e.g. '1.4.3', '2.1.1').
    Returns the full description, level, how to meet it, and common failures.
    """
    crit = WCAG_CRITERIA.get(criterion_id.strip())
    if not crit:
        available = ", ".join(sorted(WCAG_CRITERIA.keys()))
        return f"Criterion '{criterion_id}' not found in the A/AA knowledge base.\nAvailable: {available}"

    lines = [
        f"## {criterion_id} – {crit['title']} (Level {crit['level']})",
        f"**Principle:** {crit['principle']}  |  **Guideline:** {crit['guideline']}",
        f"\n**Description:** {crit['description']}",
        f"\n**Applies to:** {crit['applies_to']}",
        "\n**How to meet it:**",
    ]
    for tip in crit["how_to_meet"]:
        lines.append(f"  • {tip}")
    lines.append("\n**Common failures:**")
    for fail in crit["common_failures"]:
        lines.append(f"  ✗ {fail}")
    lines.append(f"\n**Full documentation:** {crit['wcag_url']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# TOOL 2: List all criteria for a level/principle
# ─────────────────────────────────────────────
@mcp.tool()
def list_criteria(level: str = "all", principle: str = "all") -> str:
    """
    List WCAG 2.2 success criteria filtered by level and/or principle.
    level: 'A', 'AA', or 'all'
    principle: 'Perceivable', 'Operable', 'Understandable', 'Robust', or 'all'
    """
    level = level.upper() if level.lower() != "all" else "all"
    principle = principle.title() if principle.lower() != "all" else "all"

    results = []
    for cid, crit in sorted(WCAG_CRITERIA.items()):
        if level != "all" and crit["level"] != level:
            continue
        if principle != "all" and crit["principle"] != principle:
            continue
        results.append(f"  [{crit['level']}] {cid} – {crit['title']}")

    if not results:
        return "No criteria found for the given filters."

    header = f"WCAG 2.2 Criteria (level={level}, principle={principle}) — {len(results)} found:\n"
    return header + "\n".join(results)


# ─────────────────────────────────────────────
# TOOL 3: Check color contrast
# ─────────────────────────────────────────────
def _hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _relative_luminance(r, g, b):
    def linearize(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def _contrast_ratio(hex1: str, hex2: str) -> float:
    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    l1 = _relative_luminance(r1, g1, b1)
    l2 = _relative_luminance(r2, g2, b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


@mcp.tool()
def check_color_contrast(foreground: str, background: str, text_size: str = "normal") -> str:
    """
    Check color contrast between two hex colors against WCAG 2.2 AA requirements.
    foreground: hex color of text (e.g. '#333333' or '333333')
    background: hex color of background (e.g. '#ffffff')
    text_size: 'normal' (default) or 'large' (18pt+ regular, or 14pt+ bold)
    Returns contrast ratio and pass/fail for AA and AAA levels.
    """
    try:
        ratio = _contrast_ratio(foreground, background)
    except Exception as e:
        return f"Error parsing colors: {e}. Use hex format like #FF5733 or FF5733."

    is_large = text_size.lower() == "large"
    aa_threshold = 3.0 if is_large else 4.5
    aaa_threshold = 4.5 if is_large else 7.0

    aa_pass = ratio >= aa_threshold
    aaa_pass = ratio >= aaa_threshold
    non_text_pass = ratio >= 3.0  # For UI components (1.4.11)

    result = [
        f"## Contrast Check: {foreground} on {background}",
        f"**Contrast Ratio:** {ratio:.2f}:1",
        f"**Text Size:** {text_size}",
        "",
        f"### WCAG 2.2 Results:",
        f"  1.4.3 Contrast (Minimum) – AA  ({aa_threshold}:1 required): {'✅ PASS' if aa_pass else '❌ FAIL'}",
        f"  1.4.6 Contrast (Enhanced) – AAA ({aaa_threshold}:1 required): {'✅ PASS' if aaa_pass else '❌ FAIL'}",
        f"  1.4.11 Non-text Contrast    – AA  (3:1 required):             {'✅ PASS' if non_text_pass else '❌ FAIL'}",
    ]

    if not aa_pass:
        needed = aa_threshold
        result.append(f"\n⚠️  To pass AA, you need a ratio of at least {needed}:1.")
        result.append("   Try darkening the foreground color or lightening the background.")

    return "\n".join(result)


# ─────────────────────────────────────────────
# TOOL 4: Audit HTML snippet
# ─────────────────────────────────────────────
@mcp.tool()
def audit_html(html: str) -> str:
    """
    Audit an HTML snippet for common WCAG 2.2 Level A and AA violations.
    Returns a list of detected issues with criterion IDs and suggested fixes.
    """
    issues = []

    # 1.1.1 – Images without alt
    imgs_no_alt = re.findall(r'<img(?![^>]*\balt=)[^>]*>', html, re.IGNORECASE)
    for img in imgs_no_alt:
        issues.append({
            "criterion": "1.1.1",
            "level": "A",
            "issue": f"Image missing alt attribute: {img[:80]}",
            "fix": 'Add alt="descriptive text" or alt="" for decorative images.',
        })

    # 1.1.1 – Empty/missing alt on input[type=image]
    input_imgs = re.findall(r'<input[^>]+type=["\']image["\'][^>]*>', html, re.IGNORECASE)
    for inp in input_imgs:
        if 'alt=' not in inp.lower():
            issues.append({
                "criterion": "1.1.1",
                "level": "A",
                "issue": f"Input type=image missing alt: {inp[:80]}",
                "fix": 'Add alt="Submit" or descriptive text.',
            })

    # 2.4.2 – Missing page title
    if re.search(r'<html', html, re.IGNORECASE) and not re.search(r'<title[^>]*>.+</title>', html, re.IGNORECASE):
        issues.append({
            "criterion": "2.4.2",
            "level": "A",
            "issue": "Page appears to be missing a <title> element.",
            "fix": "Add <title>Page Name | Site Name</title> inside <head>.",
        })

    # 3.1.1 – Missing lang on html
    if re.search(r'<html', html, re.IGNORECASE) and not re.search(r'<html[^>]+lang=', html, re.IGNORECASE):
        issues.append({
            "criterion": "3.1.1",
            "level": "A",
            "issue": "<html> element is missing lang attribute.",
            "fix": 'Add lang="en" (or correct language code) to <html>.',
        })

    # 1.3.1 – Form inputs without labels
    input_types = re.findall(r'<input[^>]+>', html, re.IGNORECASE)
    for inp in input_types:
        type_match = re.search(r'type=["\'](\w+)["\']', inp, re.IGNORECASE)
        input_type = type_match.group(1).lower() if type_match else "text"
        if input_type in ["text", "email", "password", "number", "tel", "search", "url", "date"]:
            id_match = re.search(r'\bid=["\']([^"\']+)["\']', inp, re.IGNORECASE)
            aria_label = re.search(r'aria-label(ledby)?=', inp, re.IGNORECASE)
            if not aria_label:
                if id_match:
                    field_id = id_match.group(1)
                    label_pattern = rf'<label[^>]+for=["\'][^"\']*{re.escape(field_id)}[^"\']*["\']'
                    if not re.search(label_pattern, html, re.IGNORECASE):
                        issues.append({
                            "criterion": "1.3.1",
                            "level": "A",
                            "issue": f"Input #{field_id} has no associated <label>.",
                            "fix": f'Add <label for="{field_id}">Label text</label> before the input.',
                        })
                else:
                    issues.append({
                        "criterion": "1.3.1",
                        "level": "A",
                        "issue": f"Input field has no id, label, or aria-label: {inp[:80]}",
                        "fix": "Add an id and an associated <label for='...'>, or add aria-label.",
                    })

    # 2.4.7 – Detecting outline: none
    if re.search(r'outline\s*:\s*none|outline\s*:\s*0', html, re.IGNORECASE):
        issues.append({
            "criterion": "2.4.7",
            "level": "AA",
            "issue": "CSS contains 'outline: none' or 'outline: 0' which removes focus indicator.",
            "fix": "Replace with a custom focus style: :focus { outline: 2px solid #005fcc; outline-offset: 2px; }",
        })

    # 2.4.4 – Generic link text
    generic_links = re.findall(
        r'<a[^>]*>\s*(click here|here|read more|more|learn more|link)\s*</a>',
        html, re.IGNORECASE
    )
    for link in generic_links:
        issues.append({
            "criterion": "2.4.4",
            "level": "A",
            "issue": f"Generic/uninformative link text: '{link}'",
            "fix": "Use descriptive link text like 'Read the 2024 Annual Report'.",
        })

    # 4.1.2 – Clickable divs/spans with no role
    clickable_divs = re.findall(r'<(?:div|span)[^>]+onclick=[^>]*>', html, re.IGNORECASE)
    for el in clickable_divs:
        if 'role=' not in el.lower():
            issues.append({
                "criterion": "4.1.2",
                "level": "A",
                "issue": f"Clickable <div>/<span> missing role and keyboard support: {el[:80]}",
                "fix": "Use <button> instead, or add role='button' tabindex='0' and keyboard event handlers.",
            })

    # 1.3.5 – Form fields with personal data, check for autocomplete
    personal_fields = re.findall(
        r'<input[^>]+(?:name|id|placeholder)=["\'][^"\']*(?:email|phone|address|zip|postal|name|birth|dob|credit|card)[^"\']*["\'][^>]*>',
        html, re.IGNORECASE
    )
    for field in personal_fields:
        if 'autocomplete=' not in field.lower():
            issues.append({
                "criterion": "1.3.5",
                "level": "AA",
                "issue": f"Personal data field may be missing autocomplete attribute: {field[:80]}",
                "fix": "Add autocomplete='email', autocomplete='tel', autocomplete='name', etc.",
            })

    # 3.3.2 – Placeholder-only inputs (no label)
    placeholder_only = re.findall(r'<input[^>]+placeholder=[^>]*>', html, re.IGNORECASE)
    for inp in placeholder_only:
        if 'aria-label' not in inp.lower() and 'id=' not in inp.lower():
            issues.append({
                "criterion": "3.3.2",
                "level": "A",
                "issue": f"Input uses only placeholder as label (no visible label): {inp[:80]}",
                "fix": "Add a visible <label> element. Placeholder disappears on input and is low-contrast.",
            })

    # Build report
    if not issues:
        return "✅ No automated issues detected. Note: automated scanning catches ~30-40% of WCAG issues. Manual testing is still required."

    report = [f"## WCAG 2.2 Audit Report — {len(issues)} issue(s) found\n"]
    for i, issue in enumerate(issues, 1):
        report.append(f"### Issue {i} — {issue['criterion']} (Level {issue['level']})")
        report.append(f"**Problem:** {issue['issue']}")
        report.append(f"**Fix:** {issue['fix']}")
        report.append("")

    report.append("---")
    report.append("⚠️  Automated tools detect ~30-40% of WCAG issues. Also test with:")
    report.append("  • Keyboard navigation (Tab, Enter, Escape, arrow keys)")
    report.append("  • Screen reader (NVDA, VoiceOver, JAWS)")
    report.append("  • 200% browser zoom")
    report.append("  • Color contrast checker")

    return "\n".join(report)


# ─────────────────────────────────────────────
# TOOL 5: Generate accessible component
# ─────────────────────────────────────────────
ACCESSIBLE_COMPONENTS = {
    "button": """<!-- Accessible Button -->
<button type="button" class="btn">
  Click Me
</button>

<!-- Icon-only Button -->
<button type="button" aria-label="Close dialog">
  <svg aria-hidden="true" focusable="false">...</svg>
</button>

<!-- Loading Button -->
<button type="button" aria-busy="true" aria-live="polite">
  <span aria-hidden="true">⏳</span> Saving...
</button>""",

    "modal": """<!-- Accessible Modal Dialog -->
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title" id="my-modal" tabindex="-1">
  <h2 id="dialog-title">Confirm Action</h2>
  <p>Are you sure you want to delete this item?</p>
  <button type="button" id="confirm-btn">Delete</button>
  <button type="button" id="cancel-btn" aria-label="Cancel, close dialog">Cancel</button>
</div>

<script>
// Trap focus inside modal
const modal = document.getElementById('my-modal');
const focusableElements = modal.querySelectorAll('button, [href], input, [tabindex]:not([tabindex="-1"])');
const firstEl = focusableElements[0];
const lastEl = focusableElements[focusableElements.length - 1];

modal.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
  if (e.key === 'Tab') {
    if (e.shiftKey && document.activeElement === firstEl) { e.preventDefault(); lastEl.focus(); }
    else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); firstEl.focus(); }
  }
});
modal.focus(); // Set initial focus
</script>""",

    "form": """<!-- Accessible Form -->
<form novalidate>
  <div class="field">
    <label for="email">
      Email address
      <span aria-hidden="true" class="required">*</span>
    </label>
    <input 
      type="email" 
      id="email" 
      name="email"
      autocomplete="email"
      aria-required="true"
      aria-describedby="email-hint email-error"
    />
    <span id="email-hint" class="hint">We'll never share your email.</span>
    <span id="email-error" role="alert" class="error" hidden>
      Please enter a valid email address (e.g., name@example.com).
    </span>
  </div>

  <fieldset>
    <legend>Preferred contact method</legend>
    <label><input type="radio" name="contact" value="email"> Email</label>
    <label><input type="radio" name="contact" value="phone"> Phone</label>
  </fieldset>

  <button type="submit">Submit</button>
  <p>Fields marked <span aria-hidden="true">*</span><span class="sr-only">with an asterisk</span> are required.</p>
</form>""",

    "navigation": """<!-- Accessible Navigation -->
<a href="#main" class="skip-link">Skip to main content</a>

<header>
  <nav aria-label="Main navigation">
    <button 
      aria-expanded="false" 
      aria-controls="nav-menu"
      class="nav-toggle"
      type="button"
    >
      <span aria-hidden="true">☰</span>
      <span class="sr-only">Toggle navigation menu</span>
    </button>
    <ul id="nav-menu">
      <li><a href="/" aria-current="page">Home</a></li>
      <li><a href="/about">About</a></li>
      <li>
        <!-- Dropdown -->
        <button aria-expanded="false" aria-haspopup="true" type="button">
          Services <span aria-hidden="true">▾</span>
        </button>
        <ul role="menu">
          <li role="menuitem"><a href="/services/design">Design</a></li>
          <li role="menuitem"><a href="/services/dev">Development</a></li>
        </ul>
      </li>
    </ul>
  </nav>
</header>

<main id="main" tabindex="-1">
  <!-- Page content -->
</main>""",

    "table": """<!-- Accessible Data Table -->
<table>
  <caption>Q4 Sales by Region — October to December 2024</caption>
  <thead>
    <tr>
      <th scope="col">Region</th>
      <th scope="col">October</th>
      <th scope="col">November</th>
      <th scope="col">December</th>
      <th scope="col">Total</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">North</th>
      <td>$12,400</td>
      <td>$15,200</td>
      <td>$18,900</td>
      <td>$46,500</td>
    </tr>
  </tbody>
</table>""",

    "alert": """<!-- Accessible Status Messages -->

<!-- Non-urgent status (polite) -->
<div role="status" aria-live="polite" aria-atomic="true" class="status-msg">
  Your changes have been saved.
</div>

<!-- Urgent alert (assertive) -->
<div role="alert" aria-live="assertive" aria-atomic="true" class="alert-msg">
  Error: Could not save your changes. Please try again.
</div>

<!-- Progress indicator -->
<div aria-live="polite" aria-atomic="true">
  <progress aria-label="Uploading file" value="60" max="100">60%</progress>
  <span class="sr-only">Upload 60% complete</span>
</div>""",

    "tabs": """<!-- Accessible Tabs (ARIA Pattern) -->
<div class="tabs">
  <div role="tablist" aria-label="Content sections">
    <button role="tab" id="tab-1" aria-controls="panel-1" aria-selected="true" tabindex="0">Overview</button>
    <button role="tab" id="tab-2" aria-controls="panel-2" aria-selected="false" tabindex="-1">Details</button>
    <button role="tab" id="tab-3" aria-controls="panel-3" aria-selected="false" tabindex="-1">Reviews</button>
  </div>

  <div role="tabpanel" id="panel-1" aria-labelledby="tab-1">
    Overview content here.
  </div>
  <div role="tabpanel" id="panel-2" aria-labelledby="tab-2" hidden>
    Details content here.
  </div>
  <div role="tabpanel" id="panel-3" aria-labelledby="tab-3" hidden>
    Reviews content here.
  </div>
</div>

<script>
// Arrow key navigation for tabs
document.querySelector('[role="tablist"]').addEventListener('keydown', (e) => {
  const tabs = [...e.currentTarget.querySelectorAll('[role="tab"]')];
  const current = tabs.indexOf(document.activeElement);
  if (e.key === 'ArrowRight') tabs[(current + 1) % tabs.length].focus();
  if (e.key === 'ArrowLeft') tabs[(current - 1 + tabs.length) % tabs.length].focus();
});
</script>""",
}


@mcp.tool()
def generate_accessible_component(component_type: str) -> str:
    """
    Generate accessible HTML markup for common UI components.
    component_type options: button, modal, form, navigation, table, alert, tabs
    Returns production-ready accessible HTML with ARIA attributes and notes.
    """
    comp = component_type.lower().strip()
    code = ACCESSIBLE_COMPONENTS.get(comp)
    if not code:
        available = ", ".join(ACCESSIBLE_COMPONENTS.keys())
        return f"Component '{component_type}' not found.\nAvailable: {available}"

    wcag_notes = {
        "button": ["1.1.1 (icon alt)", "2.1.1 (keyboard)", "4.1.2 (name/role/value)"],
        "modal": ["2.1.1 (keyboard)", "2.1.2 (no trap)", "4.1.2 (dialog role)", "3.2.1 (focus management)"],
        "form": ["1.3.1 (labels)", "3.3.1 (error ID)", "3.3.2 (instructions)", "1.3.5 (autocomplete)"],
        "navigation": ["2.4.1 (skip link)", "2.4.4 (link purpose)", "4.1.2 (roles)", "2.4.3 (focus order)"],
        "table": ["1.3.1 (headers)", "1.3.2 (sequence)"],
        "alert": ["4.1.3 (status messages)", "2.1.1 (keyboard accessible)"],
        "tabs": ["2.1.1 (keyboard)", "4.1.2 (ARIA roles)", "2.4.3 (focus order)"],
    }

    result = [
        f"## Accessible {component_type.title()} Component",
        f"**WCAG Criteria addressed:** {', '.join(wcag_notes.get(comp, []))}",
        "\n```html",
        code,
        "```",
    ]
    return "\n".join(result)


# ─────────────────────────────────────────────
# TOOL 6: Suggest fixes for a described issue
# ─────────────────────────────────────────────
FIX_PATTERNS = {
    "contrast": "1.4.3",
    "color": "1.4.1",
    "alt text": "1.1.1",
    "alt": "1.1.1",
    "image": "1.1.1",
    "keyboard": "2.1.1",
    "focus": "2.4.7",
    "label": "1.3.1",
    "form": "3.3.2",
    "error": "3.3.1",
    "skip": "2.4.1",
    "title": "2.4.2",
    "lang": "3.1.1",
    "link": "2.4.4",
    "modal": "2.1.2",
    "video": "1.2.2",
    "caption": "1.2.2",
    "transcript": "1.2.1",
    "zoom": "1.4.4",
    "resize": "1.4.4",
    "role": "4.1.2",
    "aria": "4.1.2",
    "autocomplete": "1.3.5",
    "status": "4.1.3",
    "notification": "4.1.3",
    "outline": "2.4.7",
    "tap": "2.5.8",
    "target": "2.5.8",
    "touch": "2.5.8",
    "drag": "2.5.7",
    "animation": "2.2.2",
    "flash": "2.3.1",
    "timeout": "2.2.1",
    "session": "2.2.1",
    "orientation": "1.3.4",
    "reflow": "1.4.10",
    "spacing": "1.4.12",
    "tooltip": "1.4.13",
    "hover": "1.4.13",
    "authentication": "3.3.8",
    "captcha": "3.3.8",
    "login": "3.3.8",
    "password": "3.3.8",
    "redundant": "3.3.7",
}


@mcp.tool()
def suggest_fix(issue_description: str) -> str:
    """
    Describe an accessibility issue in plain English and get WCAG criterion(a)
    and specific fix suggestions. E.g. 'my button has no keyboard support'
    or 'image missing alt text'.
    """
    desc_lower = issue_description.lower()
    matched_criteria = set()

    for keyword, cid in FIX_PATTERNS.items():
        if keyword in desc_lower:
            matched_criteria.add(cid)

    if not matched_criteria:
        return (
            "Could not automatically match this to a specific criterion. "
            "Try describing the issue using terms like: contrast, keyboard, focus, label, alt text, "
            "link, modal, video, zoom, aria, autocomplete, etc.\n\n"
            "You can also use list_criteria() to browse all A/AA criteria."
        )

    result = [f"## Suggested Fixes for: \"{issue_description}\"\n"]
    result.append(f"Matched {len(matched_criteria)} WCAG criterion/criteria:\n")

    for cid in sorted(matched_criteria):
        crit = WCAG_CRITERIA.get(cid)
        if crit:
            result.append(f"### {cid} – {crit['title']} (Level {crit['level']})")
            result.append(f"{crit['description']}\n")
            result.append("**How to fix:**")
            for tip in crit["how_to_meet"]:
                result.append(f"  • {tip}")
            result.append(f"\n📖 {crit['wcag_url']}\n")

    return "\n".join(result)


# ─────────────────────────────────────────────
# TOOL 7: Full page checklist
# ─────────────────────────────────────────────
@mcp.tool()
def get_audit_checklist(category: str = "all") -> str:
    """
    Get a manual testing checklist for WCAG 2.2 Level A and AA.
    category options: 'all', 'keyboard', 'screen_reader', 'visual', 'forms', 'media'
    """
    checklists = {
        "keyboard": [
            "[ ] Tab through entire page — every interactive element reachable",
            "[ ] Focus indicator always visible (never disappears)",
            "[ ] Focus not obscured by sticky header/footer",
            "[ ] No keyboard traps (can always Tab out)",
            "[ ] Modal dialogs trap focus and close with Escape",
            "[ ] Custom widgets use correct arrow key navigation",
            "[ ] Skip navigation link present and functional",
            "[ ] No single-character shortcuts interfere with AT",
        ],
        "screen_reader": [
            "[ ] All images have descriptive alt text",
            "[ ] Icon-only buttons have aria-label",
            "[ ] Page has a logical heading structure (h1→h2→h3)",
            "[ ] Landmark regions present: <header>, <nav>, <main>, <footer>",
            "[ ] Form fields have associated labels",
            "[ ] Error messages linked to fields via aria-describedby",
            "[ ] Status messages announced via aria-live or role='alert'",
            "[ ] Tables have <th> with scope and a <caption>",
            "[ ] <html> has correct lang attribute",
            "[ ] Dropdown/accordion state changes announced (aria-expanded)",
        ],
        "visual": [
            "[ ] Text contrast ≥ 4.5:1 (use contrast checker)",
            "[ ] Large text contrast ≥ 3:1",
            "[ ] UI component contrast ≥ 3:1 (input borders, icons)",
            "[ ] Focus indicator has sufficient contrast",
            "[ ] Information not conveyed by color alone",
            "[ ] Text readable at 200% browser zoom (no overflow/clipping)",
            "[ ] No horizontal scroll at 320px viewport width",
            "[ ] No text in images (except logos)",
            "[ ] No content lost when text spacing is increased",
        ],
        "forms": [
            "[ ] Every input has a visible <label>",
            "[ ] Placeholder text is supplemental, not the only label",
            "[ ] Required fields clearly indicated",
            "[ ] Error messages describe what went wrong and how to fix",
            "[ ] Error messages are associated with the relevant field",
            "[ ] Personal data fields have autocomplete attribute",
            "[ ] Paste is not blocked in form fields",
            "[ ] Multi-step forms don't require re-entry of already-provided info",
            "[ ] Transactions have a review/confirmation step",
        ],
        "media": [
            "[ ] Videos have captions",
            "[ ] Audio-only content has a transcript",
            "[ ] Video-only content has a text description",
            "[ ] Videos with visual information have audio descriptions",
            "[ ] Auto-playing audio has stop/pause control",
            "[ ] Animations can be paused or stopped",
            "[ ] No content flashes more than 3 times per second",
        ],
    }

    if category == "all":
        result = ["# WCAG 2.2 Manual Testing Checklist (Level A + AA)\n"]
        for cat, items in checklists.items():
            result.append(f"## {cat.replace('_', ' ').title()}")
            result.extend(items)
            result.append("")
    else:
        items = checklists.get(category.lower())
        if not items:
            return f"Category '{category}' not found. Options: {', '.join(checklists.keys())}, all"
        result = [f"# {category.replace('_', ' ').title()} Checklist\n"]
        result.extend(items)

    return "\n".join(result)


# ─────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
