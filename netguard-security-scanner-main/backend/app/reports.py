"""
Report generation.

Builds PDF (via ReportLab), CSV, and JSON exports for a completed scan,
covering host summary, port summary, risk summary and recommendations -
matching what a network engineer would hand off as a findings report.
"""
import json
import io
import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)

from app import database as db

RISK_COLORS = {
    "LOW": colors.HexColor("#22c55e"),
    "MEDIUM": colors.HexColor("#eab308"),
    "HIGH": colors.HexColor("#f97316"),
    "CRITICAL": colors.HexColor("#ef4444"),
}


def _gather_scan_data(scan_id: int) -> dict:
    scan = db.get_scan(scan_id)
    if not scan:
        raise ValueError("Scan not found")

    hosts = db.get_hosts_for_scan(scan_id)
    for h in hosts:
        h["ports"] = db.get_ports_for_host(h["id"])
        h["recommendations"] = db.get_recommendations_for_host(h["id"])

    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for h in hosts:
        risk_counts[h["risk_level"]] = risk_counts.get(h["risk_level"], 0) + 1

    return {"scan": scan, "hosts": hosts, "risk_counts": risk_counts}


def generate_json_report(scan_id: int) -> bytes:
    data = _gather_scan_data(scan_id)
    return json.dumps(data, indent=2, default=str).encode("utf-8")


def generate_csv_report(scan_id: int) -> bytes:
    data = _gather_scan_data(scan_id)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "IP Address", "Hostname", "MAC Address", "Vendor", "OS", "Status",
        "Risk Level", "Risk Score", "Open Ports", "Services"
    ])
    for h in data["hosts"]:
        open_ports = [p for p in h["ports"] if p["state"] == "open"]
        port_list = ", ".join(str(p["port_number"]) for p in open_ports)
        service_list = ", ".join(sorted({p["service_name"] for p in open_ports if p["service_name"]}))
        writer.writerow([
            h["ip_address"], h["hostname"] or "", h["mac_address"] or "",
            h["vendor"] or "", h["os_name"] or "Unknown", h["status"],
            h["risk_level"], h["risk_score"], port_list, service_list,
        ])
    return buf.getvalue().encode("utf-8")


def generate_pdf_report(scan_id: int) -> bytes:
    data = _gather_scan_data(scan_id)
    scan = data["scan"]
    hosts = data["hosts"]
    risk_counts = data["risk_counts"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20,
                                  textColor=colors.HexColor("#0f172a"))
    heading_style = ParagraphStyle("HeadingCustom", parent=styles["Heading2"],
                                    textColor=colors.HexColor("#1e293b"), spaceBefore=14, spaceAfter=8)
    normal = styles["Normal"]

    story = []
    story.append(Paragraph("Enterprise Network Discovery &amp; Security Scanner", title_style))
    story.append(Paragraph("Network Security Assessment Report", styles["Heading3"]))
    story.append(Spacer(1, 10))

    meta_table = Table([
        ["Scan Target", scan["target"]],
        ["Scan Type", scan["scan_type"]],
        ["Profile", scan["profile"]],
        ["Started At", scan["started_at"]],
        ["Duration", f'{scan["duration_seconds"]}s' if scan["duration_seconds"] else "-"],
        ["Total Hosts", str(scan["total_hosts"])],
        ["Live Hosts", str(scan["live_hosts"])],
    ], colWidths=[5 * cm, 10 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
    ]))
    story.append(meta_table)

    story.append(Paragraph("Risk Summary", heading_style))
    risk_table_data = [["Risk Level", "Host Count"]] + [[k, str(v)] for k, v in risk_counts.items()]
    risk_table = Table(risk_table_data, colWidths=[7.5 * cm, 7.5 * cm])
    risk_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ]
    for i, level in enumerate(risk_counts.keys(), start=1):
        risk_style.append(("TEXTCOLOR", (0, i), (0, i), RISK_COLORS.get(level, colors.black)))
    risk_table.setStyle(TableStyle(risk_style))
    story.append(risk_table)

    story.append(Paragraph("Host Summary", heading_style))
    host_header = ["IP Address", "Hostname", "OS", "Status", "Risk", "Open Ports"]
    host_rows = [host_header]
    for h in hosts:
        open_ports = [p for p in h["ports"] if p["state"] == "open"]
        host_rows.append([
            h["ip_address"], h["hostname"] or "-", h["os_name"] or "Unknown",
            h["status"], h["risk_level"], str(len(open_ports)),
        ])
    host_table = Table(host_rows, colWidths=[3 * cm, 3.5 * cm, 3.5 * cm, 2 * cm, 2.5 * cm, 2.5 * cm])
    host_table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
    ]
    for i, h in enumerate(hosts, start=1):
        host_table_style.append(("TEXTCOLOR", (4, i), (4, i), RISK_COLORS.get(h["risk_level"], colors.black)))
    host_table.setStyle(TableStyle(host_table_style))
    story.append(host_table)

    story.append(PageBreak())
    story.append(Paragraph("Detailed Findings &amp; Recommendations", heading_style))
    for h in hosts:
        open_ports = [p for p in h["ports"] if p["state"] == "open"]
        if not open_ports and not h["recommendations"]:
            continue
        story.append(Paragraph(
            f'{h["ip_address"]} ({h["hostname"] or "unknown host"}) — Risk: {h["risk_level"]}',
            styles["Heading4"],
        ))
        if open_ports:
            port_rows = [["Port", "Protocol", "Service", "Version"]] + [
                [str(p["port_number"]), p["protocol"], p["service_name"] or "-", p["version"] or "-"]
                for p in open_ports
            ]
            pt = Table(port_rows, colWidths=[2 * cm, 2.5 * cm, 4 * cm, 6.5 * cm])
            pt.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
            ]))
            story.append(pt)
        for rec in h["recommendations"]:
            story.append(Paragraph(
                f'<b>[{rec["severity"]}] {rec["title"]}</b> — {rec["description"]}',
                normal,
            ))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buf.getvalue()
