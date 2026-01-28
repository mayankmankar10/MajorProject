"""
PDF Generator for Database Schema Analysis
Converts markdown to a professionally formatted PDF document
"""

import markdown2
from weasyprint import HTML
from pathlib import Path

def generate_pdf():
    # Paths
    artifact_dir = Path(r"C:\Users\91983\.gemini\antigravity\brain\2ccd6b31-0ed5-4722-b043-00ee4e41f495")
    md_file = artifact_dir / "database_schema_analysis.md"
    pdf_file = artifact_dir / "database_schema_analysis.pdf"
    
    # Read markdown
    print(f"Reading markdown from: {md_file}")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    print("Converting markdown to HTML...")
    html_content = markdown2.markdown(
        md_content,
        extras=[
            'tables',
            'fenced-code-blocks',
            'header-ids',
            'code-friendly',
            'cuddled-lists',
            'nofollow'
        ]
    )
    
    # Create full HTML document with styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>CafeHire AI - Database Schema Analysis</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm 1.5cm;
                @top-center {{
                    content: "CafeHire AI - Database Schema Analysis";
                    font-size: 10pt;
                    color: #666;
                }}
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }}
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                font-size: 10pt;
            }}
            
            h1 {{
                color: #1a1a1a;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
                margin-top: 30px;
                margin-bottom: 20px;
                font-size: 22pt;
                page-break-before: auto;
            }}
            
            h2 {{
                color: #2c3e50;
                border-bottom: 2px solid #3498db;
                padding-bottom: 8px;
                margin-top: 25px;
                margin-bottom: 15px;
                font-size: 16pt;
                page-break-after: avoid;
            }}
            
            h3 {{
                color: #34495e;
                margin-top: 20px;
                margin-bottom: 12px;
                font-size: 13pt;
                page-break-after: avoid;
            }}
            
            h4 {{
                color: #555;
                margin-top: 15px;
                margin-bottom: 10px;
                font-size: 11pt;
            }}
            
            p {{
                margin-bottom: 10px;
                text-align: justify;
            }}
            
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', Courier, monospace;
                font-size: 9pt;
                color: #c7254e;
            }}
            
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-left: 4px solid #4CAF50;
                padding: 10px;
                overflow-x: auto;
                border-radius: 4px;
                margin: 12px 0;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background: none;
                padding: 0;
                font-size: 8pt;
                color: #333;
                line-height: 1.3;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12px 0;
                font-size: 8.5pt;
                background-color: white;
                page-break-inside: auto;
            }}
            
            th {{
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                text-align: left;
                font-weight: bold;
                border: 1px solid #ddd;
                font-size: 9pt;
            }}
            
            td {{
                padding: 6px 8px;
                border: 1px solid #ddd;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            tr {{
                page-break-inside: avoid;
            }}
            
            ul, ol {{
                margin: 8px 0;
                padding-left: 25px;
            }}
            
            li {{
                margin-bottom: 6px;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 15px;
                margin: 12px 0;
                color: #555;
                font-style: italic;
                background-color: #f0f8ff;
                padding: 8px 15px;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #ddd;
                margin: 25px 0;
            }}
            
            strong {{
                color: #2c3e50;
                font-weight: 600;
            }}
            
            em {{
                color: #555;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generate PDF
    print(f"Generating PDF: {pdf_file}")
    HTML(string=full_html).write_pdf(
        pdf_file,
        presentational_hints=True
    )
    
    print(f"PDF generated successfully!")
    print(f"Location: {pdf_file}")
    print(f"File size: {pdf_file.stat().st_size / 1024:.1f} KB")
    
    return pdf_file

if __name__ == "__main__":
    pdf_path = generate_pdf()
