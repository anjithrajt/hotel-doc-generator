from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from docxtpl import DocxTemplate
import shutil
import os
from datetime import datetime

app = FastAPI()

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# 🔹 Home Page
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 🔹 Generate PDF
@app.post("/generate")
async def generate(
    request: Request,
    file: UploadFile = File(...),
    booking_id: str = Form(...),
    guest_name: str = Form(...),
    checkin: str = Form(...),
    checkout: str = Form(...),
    nights: str = Form(None)
):
    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, "input.docx")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Load template
        doc = DocxTemplate(file_path)

        # 🔥 Date processing
        checkin_dt = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_dt = datetime.strptime(checkout, "%Y-%m-%d")

        booking_date = datetime.now().strftime("%d %b %Y")
        cancel_time = datetime.now().strftime("%d %b %Y %H:%M")

        # Check-in breakdown
        checkin_day = checkin_dt.strftime("%d")
        checkin_month = checkin_dt.strftime("%B").upper()
        checkin_weekday = checkin_dt.strftime("%A")

        # Check-out breakdown
        checkout_day = checkout_dt.strftime("%d")
        checkout_month = checkout_dt.strftime("%B").upper()
        checkout_weekday = checkout_dt.strftime("%A")

        # Nights
        if not nights:
            nights = str((checkout_dt - checkin_dt).days)

        # 🔥 TEMPLATE DATA
        context = {
            "name": guest_name,
            "title": "MR",  # you can change later
            "booking_id": booking_id,
            "booking_date": booking_date,
            "cancel_time": cancel_time,

            "checkin_day": checkin_day,
            "checkin_month": checkin_month,
            "checkin_weekday": checkin_weekday,

            "checkout_day": checkout_day,
            "checkout_month": checkout_month,
            "checkout_weekday": checkout_weekday,

            "nights": nights
        }

        # Render template
        doc.render(context)

        # Save DOCX
        output_docx = os.path.join(OUTPUT_DIR, "output.docx")
        doc.save(output_docx)

        # Convert to PDF
        os.system(f'libreoffice --headless --invisible --norestore --convert-to pdf --outdir {OUTPUT_DIR} {output_docx}')

        pdf_path = os.path.join(OUTPUT_DIR, "output.pdf")

        if not os.path.exists(pdf_path):
            return {"error": "PDF not generated. Install LibreOffice."}

        return FileResponse(pdf_path, media_type='application/pdf', filename="booking.pdf")

    except Exception as e:
        return {"error": str(e)}