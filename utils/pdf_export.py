"""Renders a generated cover letter to a downloadable PDF."""

from fpdf import FPDF

# fpdf2's core Helvetica font is latin-1 only. LLM output routinely contains
# "smart" Unicode punctuation Helvetica can't render — normalise the common
# ones to ASCII equivalents before falling back to errors="replace" for
# anything genuinely exotic, so the PDF doesn't fill up with "?" characters.
_UNICODE_REPLACEMENTS = {
    "‘": "'", "’": "'",       # curly single quotes
    "“": '"', "”": '"',       # curly double quotes
    "–": "-", "—": "-",       # en/em dash
    "…": "...",                    # ellipsis
    " ": " ",                      # non-breaking space
}


def _sanitize_for_pdf(text: str) -> str:
    for unicode_char, ascii_equivalent in _UNICODE_REPLACEMENTS.items():
        text = text.replace(unicode_char, ascii_equivalent)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def cover_letter_to_pdf(candidate: dict, job_title: str, company: str, cover_letter: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _sanitize_for_pdf(candidate.get("name", "")), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    contact_line = " | ".join(
        v for v in [candidate.get("email"), candidate.get("phone"), candidate.get("location")] if v
    )
    if contact_line:
        pdf.cell(0, 6, _sanitize_for_pdf(contact_line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _sanitize_for_pdf(f"Re: {job_title} at {company}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, _sanitize_for_pdf(cover_letter))

    return bytes(pdf.output())
