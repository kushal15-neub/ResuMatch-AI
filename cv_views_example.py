"""
Example Django views for CV PDF generation
Add these to your existing views.py file
"""

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .pdf_generator import cv_pdf_response
import json


def cv_builder(request, template_id):
    """
    CV Builder view - handles form submission
    """
    if request.method == "POST":
        # Process form data
        cv_data = {
            "personal_info": {
                "full_name": request.POST.get("full_name"),
                "email": request.POST.get("email"),
                "phone": request.POST.get("phone"),
                "location": request.POST.get("location"),
                "summary": request.POST.get("summary"),
            },
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
        }

        # Process experience data
        experience_titles = request.POST.getlist("experience_title")
        experience_companies = request.POST.getlist("experience_company")
        experience_locations = request.POST.getlist("experience_location")
        experience_starts = request.POST.getlist("experience_start")
        experience_ends = request.POST.getlist("experience_end")
        experience_descriptions = request.POST.getlist("experience_description")

        for i in range(len(experience_titles)):
            if experience_titles[i]:  # Only add if title exists
                cv_data["experience"].append(
                    {
                        "title": experience_titles[i],
                        "company": (
                            experience_companies[i]
                            if i < len(experience_companies)
                            else ""
                        ),
                        "location": (
                            experience_locations[i]
                            if i < len(experience_locations)
                            else ""
                        ),
                        "start": (
                            experience_starts[i] if i < len(experience_starts) else ""
                        ),
                        "end": experience_ends[i] if i < len(experience_ends) else "",
                        "description": (
                            experience_descriptions[i]
                            if i < len(experience_descriptions)
                            else ""
                        ),
                    }
                )

        # Process education data
        education_degrees = request.POST.getlist("education_degree")
        education_institutions = request.POST.getlist("education_institution")
        education_locations = request.POST.getlist("education_location")
        education_starts = request.POST.getlist("education_start")
        education_ends = request.POST.getlist("education_end")
        education_details = request.POST.getlist("education_details")

        for i in range(len(education_degrees)):
            if education_degrees[i]:  # Only add if degree exists
                cv_data["education"].append(
                    {
                        "degree": education_degrees[i],
                        "institution": (
                            education_institutions[i]
                            if i < len(education_institutions)
                            else ""
                        ),
                        "location": (
                            education_locations[i]
                            if i < len(education_locations)
                            else ""
                        ),
                        "start": (
                            education_starts[i] if i < len(education_starts) else ""
                        ),
                        "end": education_ends[i] if i < len(education_ends) else "",
                        "details": (
                            education_details[i] if i < len(education_details) else ""
                        ),
                    }
                )

        # Process skills
        skills_text = request.POST.get("skills", "")
        if skills_text:
            cv_data["skills"] = [
                skill.strip() for skill in skills_text.split(",") if skill.strip()
            ]

        # Process projects
        project_names = request.POST.getlist("project_name")
        project_links = request.POST.getlist("project_link")
        project_descriptions = request.POST.getlist("project_description")

        for i in range(len(project_names)):
            if project_names[i]:  # Only add if name exists
                cv_data["projects"].append(
                    {
                        "name": project_names[i],
                        "link": project_links[i] if i < len(project_links) else "",
                        "description": (
                            project_descriptions[i]
                            if i < len(project_descriptions)
                            else ""
                        ),
                    }
                )

        # Store CV data in session for preview
        request.session["cv_data"] = cv_data
        request.session["template_id"] = template_id

        return redirect("cv_preview", template_id=template_id)

    # GET request - show form
    template = get_template_by_id(template_id)  # Your template fetching logic
    return render(request, "cv-builder.html", {"template": template})


def cv_preview(request, template_id):
    """
    CV Preview view
    """
    cv_data = request.session.get("cv_data")
    if not cv_data:
        messages.error(request, "No CV data found. Please build your CV first.")
        return redirect("cv_builder", template_id=template_id)

    return render(
        request, "cv-preview.html", {"cv_data": cv_data, "template_id": template_id}
    )


def cv_download_pdf(request):
    """
    Download CV as PDF
    """
    cv_data = request.session.get("cv_data")
    if not cv_data:
        messages.error(request, "No CV data found. Please build your CV first.")
        return redirect("cv_templates")

    # Generate filename
    name = cv_data.get("personal_info", {}).get("full_name", "CV")
    filename = f"{name.replace(' ', '_')}_CV.pdf"

    # Return PDF response
    template_choice = cv_data.get("template_choice", "classic")
    pdf_template = (
        "cv_pdf_modern.html" if template_choice == "modern" else "cv_pdf_classic.html"
    )
    return cv_pdf_response(cv_data, filename, template_name=pdf_template)


def get_template_by_id(template_id):
    """
    Helper function to get template by ID
    Replace with your actual template fetching logic
    """
    # This is a placeholder - implement based on your template model
    return {"id": template_id, "name": "Professional Template"}
