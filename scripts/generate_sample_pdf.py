"""Generate a minimal test resume PDF using raw PDF syntax."""
from pathlib import Path

content = """JANE DOE
jane.doe@email.com | (555) 123-4567 | linkedin.com/in/janedoe

PROFESSIONAL SUMMARY
Senior software engineer with 6 years of experience building scalable web applications and REST APIs. Passionate about clean code and mentoring junior developers.

SKILLS
Python, Django, PostgreSQL, AWS (EC2, S3, Lambda), Docker, Kubernetes, REST APIs, GraphQL, CI/CD Pipelines, Redis, MongoDB, TypeScript, React

WORK EXPERIENCE

Senior Backend Engineer | Acme Corp | 2022 - Present
- Designed and built microservices handling 50M+ daily requests
- Migrated monolith to Django REST Framework, reducing latency by 40%
- Led team of 4 engineers on B2B SaaS platform serving 200+ enterprise clients
- Implemented CI/CD pipelines with GitHub Actions and Docker

Software Engineer | TechStart Inc | 2020 - 2022
- Built REST APIs with Django and PostgreSQL for fintech platform
- Managed AWS infrastructure (ECS, RDS, ElastiCache)
- Reduced database query times by 60% through indexing and query optimization

Junior Developer | WebCo | 2018 - 2020
- Developed internal tools with Python and React
- Wrote unit and integration tests achieving 90% code coverage

EDUCATION
Bachelor of Science in Computer Science | State University | 2018

CERTIFICATIONS
AWS Solutions Architect Associate | 2022
Docker Certified Associate | 2021
"""


def build_pdf(text: str) -> bytes:
    lines = text.split("\n")

    streams = []
    # Page content stream
    text_ops = b"BT\n/F1 10 Tf\n"
    y = 750
    for line in lines[:60]:
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        text_ops += f"1 0 0 1 50 {y} Tm ({escaped}) Tj\n".encode()
        y -= 13
    text_ops += b"ET"
    streams.append(text_ops)

    objects = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    stream_data = streams[0]
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode()
        + stream_data
        + b"\nendstream\nendobj\n"
    )
    objects.append(
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    offsets = []
    pdf = b"%PDF-1.4\n"
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj

    xref_offset = len(pdf)
    pdf += b"xref\n"
    pdf += f"0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()

    pdf += b"trailer\n<< /Size " + f"{len(objects) + 1}".encode() + b" /Root 1 0 R >>\n"
    pdf += b"startxref\n"
    pdf += f"{xref_offset}\n".encode()
    pdf += b"%%EOF\n"
    return pdf


if __name__ == "__main__":
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    pdf_bytes = build_pdf(content)
    out_path = data_dir / "sample_resume.pdf"
    out_path.write_bytes(pdf_bytes)
    print(f"Created {out_path} ({len(pdf_bytes)} bytes)")
