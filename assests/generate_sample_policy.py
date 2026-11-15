from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


OUTPUT_PATH = Path(__file__).with_name("sample_policy_short.pdf")


def add_policy_header(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#0B3D91"))
    canvas.rect(0, doc.height + 10, doc.width, 30, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(18 * mm, doc.height + 16 * mm, "Mock LIC / Paytm Style Insurance Policy")
    canvas.restoreState()


def build_story():
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0B3D91"),
        spaceAfter=12,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=8,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        alignment=1,
        spaceAfter=6,
    )

    story = []
    story.append(Paragraph("Policy Summary for Testing / Demo Use", title))
    story.append(
        Paragraph(
            "This document is a mock sample and is not an official LIC or Paytm insurance policy. It is intended for BimaLens demo and document-processing testing only.",
            body,
        )
    )

    table_data = [
        [Paragraph("Field", heading), Paragraph("Details", heading)],
        ["Policy No.", "LIC-TEST-2026-45671 / PAYTM-INS-AX-0140"],
        ["Plan Name", "Smart Secure Life Protect"],
        ["Insured Name", "Aarav Sharma"],
        ["Date of Issue", "15 Nov 2026"],
        ["Policy Term", "15 years"],
        ["Sum Insured", "₹ 10,00,000"],
        ["Premium Amount", "₹ 7,500 / year"],
        ["Mode", "Annual"],
        ["Nominee", "Priya Sharma"],
    ]
    policy_table = Table(table_data, colWidths=[55 * mm, 100 * mm])
    policy_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEAF7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0B3D91")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
            ]
        )
    )
    story.append(policy_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Coverage Details", heading))
    story.append(
        Paragraph(
            "- Death benefit: ₹ 10,00,000 payable to the nominee in case of death due to any covered cause.\n"
            "- Accidental death cover: additional benefit up to ₹ 2,00,000.\n"
            "- Critical illness cover: reimbursement up to ₹ 1,00,000 subject to policy terms.\n"
            "- Maturity benefit: if policy remains active until completion of term, the accumulated amount is paid as per the plan schedule.",
            body,
        )
    )

    story.append(Paragraph("2. Key Exclusions", heading))
    story.append(
        Paragraph(
            "- Death or disability caused by self-inflicted injury, intoxication, or illegal activity is excluded.\n"
            "- Claims arising from pre-existing illness within the waiting period are not payable.\n"
            "- Any fraudulent, concealed, or misrepresented information may lead to claim rejection.\n"
            "- War, nuclear events, and participation in hazardous adventure sports are outside the scope of coverage.",
            body,
        )
    )

    story.append(Paragraph("3. Claim Procedure", heading))
    story.append(
        Paragraph(
            "- Notify the insurer within 30 days of a claim event.\n"
            "- Submit the claim form, policy document, medical records, and identity proof.\n"
            "- In case of accidental death, a police report and FIR copy may be required.\n"
            "- Claims are reviewed within 15 to 30 working days after document verification.",
            body,
        )
    )

    story.append(Paragraph("4. Declaration", heading))
    story.append(
        Paragraph(
            "I, Aarav Sharma, declare that the information provided above is accurate to the best of my knowledge and I agree to comply with the policy terms, premium schedule, and claim guidelines. This sample policy is intended solely for educational and testing use in document extraction systems.",
            body,
        )
    )

    return story


def generate_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
    )

    story = build_story()
    doc.build(story)
    print(f"Created: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_pdf()
