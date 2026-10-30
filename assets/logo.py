"""
Professional Vector Branding for FollowUp
Clinical continuity-of-care logo and typography badge.
"""

def get_logo_svg(width: int = 38, height: int = 38) -> str:
    """Return inline SVG vector logo featuring healthcare continuity geometry."""
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" rx="10" fill="#1e3a8a"/>
  <!-- Continuity Orbit -->
  <circle cx="24" cy="24" r="16" stroke="#93c5fd" stroke-width="2.5" stroke-dasharray="3 3"/>
  <!-- Care Cross Geometry -->
  <path d="M24 13V35M13 24H35" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round"/>
  <!-- Vitality Pulse Trace -->
  <path d="M16 24L20 24L22 18L26 30L28 24L32 24" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <!-- Focal Point -->
  <circle cx="24" cy="24" r="2.5" fill="#ffffff"/>
</svg>"""

def render_brand_header_html() -> str:
    """Render the top banner branding with vector mark and clinical typography."""
    svg = get_logo_svg(36, 36)
    return f"""
    <div style="display: flex; align-items: center; gap: 14px; padding: 6px 0 16px 0; border-bottom: 1px solid #cbd5e1; margin-bottom: 20px;">
        <div style="flex-shrink: 0;">
            {svg}
        </div>
        <div style="display: flex; flex-direction: column;">
            <div style="font-size: 1.45rem; font-weight: 700; color: #1e3a8a; line-height: 1.15; letter-spacing: -0.02em;">
                Follow<span style="color: #0284c7;">Up</span>
            </div>
            <div style="font-size: 0.8rem; font-weight: 500; color: #475569; letter-spacing: 0.01em;">
                Patient Continuity-of-Care and Follow-Up Management System
            </div>
        </div>
    </div>
    """

def render_sidebar_brand_html() -> str:
    """Render the sidebar brand heading."""
    svg = get_logo_svg(30, 30)
    return f"""
    <div style="display: flex; align-items: center; gap: 10px; padding: 4px 0 12px 0; border-bottom: 1px solid #cbd5e1; margin-bottom: 14px;">
        <div style="flex-shrink: 0;">
            {svg}
        </div>
        <div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #1e3a8a; line-height: 1.1;">
                Follow<span style="color: #0284c7;">Up</span>
            </div>
            <div style="font-size: 0.72rem; color: #64748b; font-weight: 500;">
                Clinical Continuity
            </div>
        </div>
    </div>
    """
