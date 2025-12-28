"""
PDF Generation for CV Export (WeasyPrint)
"""

from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings


def generate_cv_pdf(cv_data, template_name="cv_pdf_classic.html"):
    """
    Generates PDF bytes from a CV template and data.

    Returns:
        (pdf_content, error_message)
    """

    # 1. Lazy import WeasyPrint
    try:
        import weasyprint
    except ImportError as e:
        return None, (
            "WeasyPrint is not installed. Install it using:\n"
            "pip install weasyprint\n"
            f"Details: {e}"
        )
    except Exception as e:
        return None, f"Unexpected WeasyPrint import error: {e}"

    # 2. Render HTML template
    try:
        html_string = render_to_string(
            template_name,
            {
                "cv_data": cv_data,
                "static_url": settings.STATIC_URL,
            },
        )

        if not html_string.strip():
            return None, f"Template '{template_name}' rendered empty output."

    except Exception as e:
        return None, f"Template rendering error: {e}"

    # 3. Base URL for loading CSS and images
    try:
        base_url = (
            str(settings.STATIC_ROOT)
            if getattr(settings, "STATIC_ROOT", None)
            else str(settings.BASE_DIR)
        )
    except Exception:
        base_url = None

    # 4. Generate PDF
    try:
        html = weasyprint.HTML(string=html_string, base_url=base_url)
        buffer = BytesIO()
        html.write_pdf(buffer)

        buffer.seek(0)
        pdf_content = buffer.read()

        if not pdf_content:
            return None, "PDF buffer is empty."

        return pdf_content, None

    except Exception as e:
        import traceback
        return None, (
            f"PDF generation failed: {e}\n"
            f"{traceback.format_exc()}"
        )


def cv_pdf_response(cv_data, filename="cv.pdf", template_name="cv_pdf_classic.html"):
    """
    Returns HttpResponse containing a downloadable PDF.
    """

    pdf_content, error_message = generate_cv_pdf(cv_data, template_name)

    if pdf_content:
        response = HttpResponse(
            pdf_content,
            content_type="application/pdf"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    # Show readable error to the user
    short_error = (
        error_message.split("\n")[0]
        if error_message
        else "Unknown error"
    )

    return HttpResponse(
        f"Error generating PDF: {short_error}\nCheck server logs for details.",
        status=500,
        content_type="text/plain"
    )
