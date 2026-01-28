"""
Generate PDF from Employee Tools Theoretical Guide Markdown
Uses markdown2 + weasyprint for PDF generation
"""
import os
import sys

# Check for required libraries
try:
    import markdown2
    print("[OK] markdown2 available")
except ImportError:
    print("[INSTALL] Installing markdown2...")
    os.system("pip install markdown2")
    import markdown2

try:
    from weasyprint import HTML, CSS
    print("[OK] weasyprint available")
except ImportError:
    print("[INSTALL] Installing weasyprint...")
    os.system("pip install weasyprint")
    from weasyprint import HTML, CSS

# Paths
markdown_file = r"C:\Users\91983\.gemini\antigravity\brain\59255269-2180-4c70-8331-388d9749f181\employee_tools_theoretical_guide.md"
pdf_file = r"C:\Users\91983\.gemini\antigravity\brain\59255269-2180-4c70-8331-388d9749f181\employee_tools_theoretical_guide.pdf"

print(f"\nConverting:\n  From: {markdown_file}\n  To: {pdf_file}\n")

# Read markdown
with open(markdown_file, 'r', encoding='utf-8') as f:
    markdown_content = f.read()

# Convert markdown to HTML
html_content = markdown2.markdown(
    markdown_content,
    extras=[
        "tables",
        "fenced-code-blocks",
        "header-ids",
        "toc",
        "code-friendly",
        "markdown-in-html"
    ]
)

# Add CSS styling for professional PDF
css_style = """
<style>
    @page {
        size: A4;
        margin: 1in;
    }
    body {
        font-family: 'Georgia', serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    h1 {
        color: #2c3e50;
        font-size: 24pt;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.3em;
        page-break-after: avoid;
    }
    h2 {
        color: #34495e;
        font-size: 18pt;
        margin-top: 1.5em;
        page-break-after: avoid;
    }
    h3 {
        color: #555;
        font-size: 14pt;
        margin-top: 1.2em;
        page-break-after: avoid;
    }
    h4 {
        color: #666;
        font-size: 12pt;
        font-weight: bold;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
        font-size: 10pt;
    }
    th {
        background-color: #3498db;
        color: white;
        padding: 8px;
        text-align: left;
        font-weight: bold;
    }
    td {
        border: 1px solid #ddd;
        padding: 6px;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
    }
    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-left: 3px solid #3498db;
        padding: 10px;
        overflow-x: auto;
        font-size: 9pt;
        page-break-inside: avoid;
    }
    pre code {
        background-color: transparent;
        padding: 0;
    }
    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 1em;
        margin-left: 0;
        color: #555;
        font-style: italic;
    }
    hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 2em 0;
    }
    .page-break {
        page-break-after: always;
    }
    p {
        margin: 0.8em 0;
        text-align: justify;
    }
    ul, ol {
        margin: 0.5em 0;
        padding-left: 2em;
    }
    li {
        margin: 0.3em 0;
    }
    .formula {
        background-color: #f0f8ff;
        border: 1px solid #3498db;
        border-radius: 4px;
        padding: 10px;
        margin: 1em 0;
        font-family: 'Courier New', monospace;
        page-break-inside: avoid;
    }
</style>
"""

# Build complete HTML
full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Employee Tools: Theoretical Framework & Mathematical Models</title>
    {css_style}
</head>
<body>
    {html_content}
</body>
</html>
"""

# Generate PDF
print("Generating PDF...")
HTML(string=full_html).write_pdf(pdf_file)

print(f"\n[SUCCESS] PDF generated successfully!")
print(f"   Location: {pdf_file}")
print(f"   Size: {os.path.getsize(pdf_file) / 1024:.1f} KB")
