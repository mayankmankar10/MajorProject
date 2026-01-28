"""
Professional PDF Generator with Diagrams
Includes visual diagrams at appropriate sections
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
                                Table, TableStyle, Preformatted, Image, KeepTogether)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import re
import os
import glob

def find_diagram_image(diagram_name):
    """Find the most recent diagram image"""
    pattern = f"C:/Users/91983/.gemini/antigravity/brain/410f4c05-74d7-4d60-9e2a-55639684fbc6/{diagram_name}_*.png"
    files = glob.glob(pattern)
    if files:
        # Return most recent
        return max(files, key=os.path.getctime)
    return None

def create_professional_pdf_with_diagrams(md_file, pdf_file):
    """Create a professional PDF from markdown with diagrams"""
    
    # Read markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(
        pdf_file,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMarent=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Define styles (same as before)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22,
        textColor=colors.HexColor('#1a1a1a'), spaceAfter=24, alignment=TA_CENTER,
        fontName='Helvetica-Bold', leading=26)
    
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16,
        textColor=colors.HexColor('#2563eb'), spaceAfter=12, spaceBefore=20,
        fontName='Helvetica-Bold')
    
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13,
        textColor=colors.HexColor('#1e40af'), spaceAfter=10, spaceBefore=15,
        fontName='Helvetica-Bold')
    
    h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=11,
        textColor=colors.HexColor('#374151'), spaceAfter=8, spaceBefore=12,
        fontName='Helvetica-Bold')
    
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
        spaceAfter=6, alignment=TA_JUSTIFY, leading=14,
        textColor=colors.HexColor('#374151'))
    
    bullet_style = ParagraphStyle('Bullet', parent=body_style, leftIndent=20,
        bulletIndent=10, spaceAfter=4)
    
    code_style = ParagraphStyle('Code', parent=styles['Code'], fontSize=8,
        fontName='Courier', textColor=colors.HexColor('#1f2937'),
        backColor=colors.HexColor('#f3f4f6'), leftIndent=15, rightIndent=15,
        spaceBefore=8, spaceAfter=8, borderPadding=8, borderWidth=0.5,
        borderColor=colors.HexColor('#d1d5db'))
    
    # Diagram mapping
    diagram_map = {
        'graph LR': 'hybrid_analyzer_flow',
        'sequenceDiagram': None,  # Will determine by context
    }
    
    diagram_counter = 0
    diagram_files = [
        find_diagram_image('hybrid_analyzer_flow'),
        find_diagram_image('batch_processing_flow'),
        find_diagram_image('cache_lifecycle_state'),
        find_diagram_image('employee_registration_flow'),
        find_diagram_image('job_matching_flow'),
    ]
    
    # Parse markdown and build story
    story = []
    lines = content.split('\n')
    i = 0
    first_h1 = True
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Handle Mermaid diagrams - insert image
        if '```mermaid' in line:
            # Skip mermaid content
            while i < len(lines) and '```' not in lines[i+1]:
                i += 1
            i += 2
            
            # Insert corresponding diagram
            if diagram_counter < len(diagram_files) and diagram_files[diagram_counter]:
                img = Image(diagram_files[diagram_counter], width=5*inch, height=3.5*inch)
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
                diagram_counter += 1
            continue
        
        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                if code_lines:
                    formatted_lines = []
                    for cline in code_lines:
                        if len(cline) > 80:
                            while len(cline) > 80:
                                formatted_lines.append(cline[:80])
                                cline = '  ' + cline[80:]
                            if cline:
                                formatted_lines.append(cline)
                        else:
                            formatted_lines.append(cline)
                    
                    code_text = '\n'.join(formatted_lines)
                    pre = Preformatted(code_text, code_style)
                    story.append(pre)
                    story.append(Spacer(1, 0.1*inch))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
        
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
        
        # Handle tables
        if line.startswith('|') and not in_table:
            in_table = True
            table_lines = []
        
        if in_table:
            if line.startswith('|'):
                table_lines.append(line)
                i += 1
                continue
            else:
                if table_lines:
                    rows = []
                    for tline in table_lines:
                        if '---' in tline:
                            continue
                        cells = [cell.strip() for cell in tline.split('|')[1:-1]]
                        if cells:
                            rows.append(cells)
                    
                    if rows:
                        t = Table(rows, hAlign='LEFT')
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 0.15*inch))
                in_table = False
                table_lines = []
                continue
        
        # Title (first H1)
        if line.startswith('# ') and first_h1:
            story.append(Paragraph(line[2:], title_style))
            story.append(Spacer(1, 0.4*inch))
            first_h1 = False
        elif line.startswith('# '):
            story.append(PageBreak())
            story.append(Paragraph(line[2:], h1_style))
        elif line.startswith('## '):
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(line[3:], h2_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], h3_style))
        elif line.startswith('#### '):
            story.append(Paragraph(f'<b>{line[5:]}</b>', body_style))
        elif line == '---':
            story.append(Spacer(1, 0.15*inch))
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:]
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'`(.+?)`', r'<font name="Courier" size="8">\1</font>', text)
            story.append(Paragraph(f'• {text}', bullet_style))
        elif re.match(r'^\d+\.', line):
            text = re.sub(r'^\d+\.\s*', '', line)
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'`(.+?)`', r'<font name="Courier" size="8">\1</font>', text)
            story.append(Paragraph(f'  {text}', bullet_style))
        elif line.strip():
            text = line
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'`(.+?)`', r'<font name="Courier" size="8" color="#1f2937">\1</font>', text)
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            try:
                story.append(Paragraph(text, body_style))
            except:
                pass
        else:
            story.append(Spacer(1, 0.08*inch))
        
        i += 1
    
    # Build PDF
    doc.build(story)
    print(f"PDF created successfully: {pdf_file}")
    print(f"Diagrams included: {diagram_counter}")

if __name__ == "__main__":
    md_file = r"C:\Users\91983\.gemini\antigravity\brain\410f4c05-74d7-4d60-9e2a-55639684fbc6\profile_analysis_architecture.md"
    pdf_file = r"C:\manpower_connector\profile_analysis_architecture.pdf"
    
    try:
        create_professional_pdf_with_diagrams(md_file, pdf_file)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
