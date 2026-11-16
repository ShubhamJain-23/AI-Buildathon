import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

HEX_WHITE = colors.HexColor('#FFFFFF')
HEX_DARK = colors.HexColor('#0F172A')
HEX_MUTED = colors.HexColor('#475569')
HEX_LIGHT_BG = colors.HexColor('#F8FAFC')
HEX_BORDER = colors.HexColor('#CBD5E1')

class SinglePageNumberedCanvas(canvas.Canvas):
    """Adds formal running footer and border."""
    def __init__(self, *args, **kwargs):
        super(SinglePageNumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer_and_frame(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_footer_and_frame(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(HEX_MUTED)
        
        # Outer border / accent line
        self.setStrokeColor(HEX_BORDER)
        self.setLineWidth(0.5)
        self.line(28, 22, A4[0] - 28, 22)
        
        # Left footer: Compliance notice
        self.setFont("Helvetica", 6.5)
        self.drawString(28, 12, "Certified Institutional Bid | Generated strictly in accordance with statutory GST Rules & Public Procurement Norms")
        # Right footer: Page info
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 28, 12, page_str)
        self.restoreState()


def build_quotation_pdf(qdata, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Page setup: A4 (595.27 x 841.89 pt), margins 28 pt (0.39 in)
    # Usable width = 595.27 - 56 = 539.27 pt
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=28,
        rightMargin=28,
        topMargin=22,
        bottomMargin=26
    )

    primary_color = colors.HexColor(qdata.get('primary_color', '#1E40AF'))
    secondary_color = colors.HexColor(qdata.get('secondary_color', '#DBEAFE'))
    
    styles = getSampleStyleSheet()
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=HEX_DARK
    )
    
    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    body_small = ParagraphStyle(
        'DocBodySmall',
        parent=body_style,
        fontSize=6.5,
        leading=8.5,
        textColor=HEX_MUTED
    )
    
    quote_badge_style = ParagraphStyle(
        'QuoteBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=13,
        textColor=colors.HexColor('#FFFFFF'),
        alignment=1
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#FFFFFF'),
        alignment=1
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=HEX_DARK
    )
    
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )

    table_cell_right = ParagraphStyle(
        'TableCellRight',
        parent=table_cell_style,
        alignment=2
    )
    
    table_cell_right_bold = ParagraphStyle(
        'TableCellRightBold',
        parent=table_cell_bold,
        alignment=2
    )

    story = []

    comp = qdata['company']
    client = qdata['client']
    meta = qdata['meta']

    # 1. Header Table (Left: Company Details, Right: Quotation Badge + Meta Box)
    # Total width: 335 + 204 = 539 pt
    comp_info_text = f"""
    <b><font size="12" color="{qdata['primary_color']}">{comp['name']}</font></b><br/>
    <font size="7.2" color="#475569"><i>{comp.get('tagline', '')}</i></font><br/>
    <font size="6.8" color="#334155">
    <b>CIN/Reg:</b> {comp.get('cin', 'N/A')} &nbsp;|&nbsp; <b>GSTIN:</b> {comp['gstin']} &nbsp;|&nbsp; <b>PAN:</b> {comp['pan']}<br/>
    <b>Registered Office:</b> {comp['address']}<br/>
    <b>Email:</b> {comp['email']} &nbsp;|&nbsp; <b>Phone:</b> {comp['phone']} &nbsp;|&nbsp; <b>Web:</b> {comp.get('web', '')}<br/>
    <b>MSME / Udyam Reg:</b> {comp.get('udyam', 'N/A')}
    </font>
    """
    comp_paragraph = Paragraph(comp_info_text, body_style)

    badge_p = Paragraph("<b>COMMERCIAL QUOTATION</b>", quote_badge_style)
    
    meta_details_html = f"""
    <font size="6.8">
    <b>Quote Ref No:</b> <font color="{qdata['primary_color']}"><b>{meta['quote_no']}</b></font><br/>
    <b>Date:</b> {meta['quote_date']}<br/>
    <b>Validity:</b> {meta.get('validity', '30 Days')} (Valid Till: {meta.get('valid_till', 'N/A')})<br/>
    <b>Buyer RFQ Ref:</b> {meta.get('rfq_ref', 'Direct Enquiry')}<br/>
    <b>Place of Supply:</b> {meta.get('place_of_supply', 'Rajasthan (08)')}
    </font>
    """
    meta_p = Paragraph(meta_details_html, body_style)

    header_table_data = [
        [comp_paragraph, Table([
            [badge_p],
            [meta_p]
        ], colWidths=[195], style=[
            ('BACKGROUND', (0, 0), (0, 0), primary_color),
            ('BACKGROUND', (0, 1), (0, 1), HEX_LIGHT_BG),
            ('BOX', (0, 0), (-1, -1), 0.75, primary_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, HEX_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ])]
    ]
    
    header_table = Table(header_table_data, colWidths=[338, 201])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_table)

    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceBefore=3, spaceAfter=4))

    # 2. Client Billing & Delivery Box
    client_box_content = [
        [
            Paragraph(f"<b>BILLED TO (BUYER DETAILS):</b>", body_bold),
            Paragraph(f"<b>CONSIGNEE & DELIVERY SITE:</b>", body_bold)
        ],
        [
            Paragraph(f"""
            <b>{client['org_name']}</b><br/>
            <b>Department:</b> {client['dept_name']}<br/>
            <b>Attention:</b> {client.get('contact_person', 'Purchase Committee')}<br/>
            <b>Address:</b> {client['address']}<br/>
            <b>GSTIN:</b> {client.get('gstin', '08AAATA8899K1Z5')} &nbsp;|&nbsp; <b>State:</b> Rajasthan (08)
            """, body_style),
            Paragraph(f"""
            <b>Consignee:</b> {client.get('ship_to', client['org_name'])}<br/>
            <b>Department:</b> {client['dept_name']}<br/>
            <b>Delivery Site:</b> {client.get('ship_location', client['address'])}<br/>
            <b>Mode of Dispatch:</b> Doorstep Road Freight (Transit Insured)
            """, body_style)
        ]
    ]
    
    client_table = Table(client_box_content, colWidths=[269, 270])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('BACKGROUND', (0, 1), (-1, 1), HEX_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, HEX_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HEX_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 4))

    # 3. Subject Header
    subj_text = f"<b>Subject:</b> Commercial Quotation for <b>{qdata['subject']}</b> against RFQ: <b>{meta.get('rfq_ref', 'N/A')}</b>"
    story.append(Paragraph(subj_text, body_style))
    story.append(Spacer(1, 4))

    # 4. Itemized Supplies / Services Table
    # Widths sum = 539 pt: S.No (20), Description (264), HSN (48), Qty (32), Unit (32), Rate (70), Taxable (73)
    items_header = [
        Paragraph("#", table_header_style),
        Paragraph("Item & Detailed Technical Specifications", table_header_style),
        Paragraph("HSN/SAC", table_header_style),
        Paragraph("Qty", table_header_style),
        Paragraph("Unit", table_header_style),
        Paragraph("Unit Rate (₹)", table_header_style),
        Paragraph("Taxable Amt (₹)", table_header_style),
    ]

    items_data = [items_header]
    
    subtotal = 0.0
    for idx, itm in enumerate(qdata['items'], start=1):
        amt = itm['qty'] * itm['rate']
        subtotal += amt
        
        desc_p = Paragraph(f"<b>{itm['name']}</b><br/><font size='6.3' color='#475569'>{itm['specs']}</font>", table_cell_style)
        hsn_p = Paragraph(str(itm.get('hsn', '-')), ParagraphStyle('Cen', parent=table_cell_style, alignment=1))
        qty_p = Paragraph(str(itm['qty']), ParagraphStyle('Cen', parent=table_cell_style, alignment=1))
        unit_p = Paragraph(itm.get('unit', 'Nos'), ParagraphStyle('Cen', parent=table_cell_style, alignment=1))
        rate_p = Paragraph(f"{itm['rate']:,.2f}", table_cell_right)
        amt_p = Paragraph(f"{amt:,.2f}", table_cell_right_bold)
        
        items_data.append([
            Paragraph(str(idx), ParagraphStyle('Cen', parent=table_cell_style, alignment=1)),
            desc_p,
            hsn_p,
            qty_p,
            unit_p,
            rate_p,
            amt_p
        ])

    items_table = Table(items_data, colWidths=[20, 264, 48, 32, 32, 70, 73])
    
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HEX_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 3.5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3.5),
    ]
    
    for r in range(1, len(items_data)):
        if r % 2 == 0:
            t_style.append(('BACKGROUND', (0, r), (-1, r), HEX_LIGHT_BG))
            
    items_table.setStyle(TableStyle(t_style))
    story.append(items_table)
    story.append(Spacer(1, 3))

    # 5. Calculation / Tax Summary Table
    tax_info = qdata['tax']
    is_igst = tax_info.get('is_igst', False)
    tax_rate = tax_info.get('rate_pct', 18.0)
    
    if is_igst:
        igst_amt = subtotal * (tax_rate / 100.0)
        cgst_amt = 0.0
        sgst_amt = 0.0
        tax_total = igst_amt
    else:
        half_rate = tax_rate / 2.0
        cgst_amt = subtotal * (half_rate / 100.0)
        sgst_amt = subtotal * (half_rate / 100.0)
        igst_amt = 0.0
        tax_total = cgst_amt + sgst_amt

    grand_total = subtotal + tax_total

    calc_rows = [
        [Paragraph("<b>Taxable Subtotal (INR):</b>", table_cell_right), Paragraph(f"<b>₹ {subtotal:,.2f}</b>", table_cell_right_bold)]
    ]
    
    if is_igst:
        calc_rows.append([
            Paragraph(f"Integrated GST (IGST @ {tax_rate:.0f}%):", table_cell_right),
            Paragraph(f"₹ {igst_amt:,.2f}", table_cell_right)
        ])
    else:
        calc_rows.append([
            Paragraph(f"Central GST (CGST @ {half_rate:.1f}%):", table_cell_right),
            Paragraph(f"₹ {cgst_amt:,.2f}", table_cell_right)
        ])
        calc_rows.append([
            Paragraph(f"State GST (SGST @ {half_rate:.1f}%):", table_cell_right),
            Paragraph(f"₹ {sgst_amt:,.2f}", table_cell_right)
        ])

    calc_rows.append([
        Paragraph("<b>FINAL TOTAL (INCL. GST):</b>", table_cell_right_bold),
        Paragraph(f"<b><font size='8.5' color='{qdata['primary_color']}'>₹ {grand_total:,.2f}</font></b>", table_cell_right_bold)
    ])

    calc_table = Table(calc_rows, colWidths=[396, 143])
    calc_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HEX_BORDER),
        ('BACKGROUND', (0, -1), (-1, -1), secondary_color),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(calc_table)
    story.append(Spacer(1, 3))

    # Words representation
    words_p = Paragraph(f"<b>Amount in Words:</b> <i>{qdata['total_in_words']}</i>", body_style)
    story.append(words_p)
    story.append(Spacer(1, 4))

    # 6. Commercial Terms & Bank Settlement Box
    bank = comp.get('bank', {})
    bank_html = f"""
    <b>BANK DETAILS FOR SETTLEMENT:</b><br/>
    <b>A/C Name:</b> {bank.get('holder', comp['name'])}<br/>
    <b>Bank:</b> {bank.get('name', 'HDFC Bank Ltd')}<br/>
    <b>A/C No:</b> <font color="{qdata['primary_color']}"><b>{bank.get('account', '50200012345678')}</b></font><br/>
    <b>IFSC:</b> <b>{bank.get('ifsc', 'HDFC0000123')}</b> &nbsp;|&nbsp; <b>Branch:</b> {bank.get('branch', 'Jaipur')}<br/>
    <b>Account Type:</b> Current Account
    """
    bank_p = Paragraph(bank_html, body_style)

    terms_list = qdata.get('terms', [])
    terms_html = "<b>COMMERCIAL TERMS & REGULATORY CONDITIONS:</b><br/>"
    for t_idx, t in enumerate(terms_list, 1):
        terms_html += f"<b>{t_idx}.</b> {t} "
    terms_p = Paragraph(terms_html, body_small)

    terms_table = Table([
        [bank_p, terms_p]
    ], colWidths=[200, 339])
    terms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), HEX_LIGHT_BG),
        ('BACKGROUND', (1, 0), (1, 0), HEX_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, HEX_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, HEX_BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    # 7. Signature & Authorization Block
    sign_block = [
        [
            Paragraph("""
            <b>UNDERTAKING & BID DECLARATION:</b><br/>
            <font size="6.2" color="#475569">
            We confirm that this commercial quotation is submitted in strict accordance with the buyer's technical schedule and tender requirements. Prices are firm and valid for the entire validity duration. Deliverables will be provided in pristine OEM sealed condition with authorized test certificates and warranty guarantees.
            </font>
            """, body_style),
            Paragraph(f"""
            <div align="center">
            <b>For {comp['name']}</b><br/><br/>
            <b>Authorized Signatory</b><br/>
            <font size="6.2" color="#475569">{comp.get('signatory_title', 'Head of Corporate Sales')}</font><br/>
            <font size="5.8" color="#94A3B8">[Digitally Signed & Validated]</font>
            </div>
            """, body_style)
        ]
    ]
    sign_table = Table(sign_block, colWidths=[355, 184])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, HEX_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), HEX_WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(KeepTogether([
        terms_table,
        Spacer(1, 4),
        sign_table
    ]))

    doc.build(story, canvasmaker=SinglePageNumberedCanvas)
    print(f"Generated: {output_path}")
