/**
 * Google Apps Script Web App for MedFlow AI
 * 
 * Instructions:
 * 1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1hmkeJ7b5YPmUNnxqn36q8B4XBpdO8FVS9hsBe-vvIKU/edit?usp=sharing
 * 2. In the top menu, go to: Extensions -> Apps Script
 * 3. Delete any default code in Code.gs, paste this script below, and save.
 * 4. Click "Deploy" (top-right) -> "New deployment"
 * 5. Under Select type, click the Gear icon -> "Web app"
 * 6. Set:
 *    - Description: MedFlow Triage Logger, Emailer & SMS
 *    - Execute as: "Me" (your email)
 *    - Who has access: "Anyone"
 * 7. Click Deploy, authorize permissions, and copy the generated "Web app URL" (ends with /exec).
 * 8. Paste the Web app URL in your backend/.env as GOOGLE_SHEET_WEBHOOK_URL.
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // Parse patient payload
    var data = JSON.parse(e.postData.contents);
    
    // Set headers in Row 1 if sheet is empty
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        "Timestamp",
        "Patient ID",
        "Patient Name",
        "Age",
        "Patient Email",
        "Patient Mobile",
        "Symptoms / Query",
        "Ward Classification",
        "Reasoning / Notes",
        "Assigned Doctor",
        "Booking Slot Time"
      ]);
      // Format headers bold and frozen
      sheet.getRange(1, 1, 1, 11).setFontWeight("bold");
      sheet.setFrozenRows(1);
    }
    
    // Append patient triage data row
    sheet.appendRow([
      new Date().toLocaleString(),
      data.patient_id || "N/A",
      data.name || "N/A",
      data.age || "N/A",
      data.email || "N/A",
      data.mobile || "N/A",
      data.query || "N/A",
      data.ward ? data.ward.toUpperCase() : "N/A",
      data.reasoning || "N/A",
      data.assigned_doctor || "N/A",
      data.assigned_slot || "N/A"
    ]);
    
    // Send email to patient if email is provided and matches format
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (data.email && data.email !== "N/A" && emailRegex.test(data.email)) {
      // Build QR Code image url
      var qrContent = "MedFlow AI Triage Ticket\n" + 
                       "---------------------------\n" +
                       "Patient ID: " + (data.patient_id || "N/A") + "\n" +
                       "Patient: " + (data.name || "N/A") + "\n" +
                       "Age: " + (data.age || "N/A") + "\n" +
                       "Mobile: " + (data.mobile || "N/A") + "\n" +
                       "Ward: " + (data.ward ? data.ward.toUpperCase() : "N/A") + "\n" +
                       "Doctor: " + (data.assigned_doctor || "N/A") + "\n" +
                       "Slot Time: " + (data.assigned_slot || "N/A");
      
      var qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=" + encodeURIComponent(qrContent);
      
      var subject = "MedFlow AI Admission Ticket - " + (data.name || "Patient");
      var body = "Hello " + (data.name || "Patient") + ",\n\n" +
                 "Your clinical triage evaluation is complete. Here are your booking details:\n\n" +
                 "• Patient ID: " + (data.patient_id || "N/A") + "\n" +
                 "• Assigned Ward: " + (data.ward ? data.ward.toUpperCase() : "N/A") + "\n" +
                 "• Assigned Specialist: " + (data.assigned_doctor || "N/A") + "\n" +
                 "• Scheduled Time Slot: " + (data.assigned_slot || "N/A") + "\n\n" +
                 "Please check in at the ward entrance gate.\n\n" +
                 "Get well soon,\n" +
                 "MedFlow Clinical Admissions Team";
                 
      var htmlBody = "<div style='font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 12px; background-color: #fafcf8;'>" +
                     "<div style='background: linear-gradient(135deg, #C44A3A, #D97A2B); padding: 15px; border-radius: 8px 8px 0 0; text-align: center; color: #fff;'>" +
                     "<h2 style='margin: 0;'>MedFlow AI Admission Ticket</h2>" +
                     "</div>" +
                     "<div style='padding: 20px; background: #fff; border: 1px solid #eee; border-radius: 0 0 8px 8px;'>" +
                     "<p>Hello <strong>" + (data.name || "Patient") + "</strong>,</p>" +
                     "<p>Your clinical triage evaluation is complete. Here is your admission ticket details:</p>" +
                     "<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>" +
                     "<tr style='background-color: #f9f9f9;'><td style='padding: 10px; border: 1px solid #ddd;'><strong>Patient ID</strong></td><td style='padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #C44A3A;'>" + (data.patient_id || "N/A") + "</td></tr>" +
                     "<tr><td style='padding: 10px; border: 1px solid #ddd;'><strong>Patient Name</strong></td><td style='padding: 10px; border: 1px solid #ddd;'>" + (data.name || "N/A") + "</td></tr>" +
                     "<tr style='background-color: #f9f9f9;'><td style='padding: 10px; border: 1px solid #ddd;'><strong>Age</strong></td><td style='padding: 10px; border: 1px solid #ddd;'>" + (data.age || "N/A") + "</td></tr>" +
                     "<tr><td style='padding: 10px; border: 1px solid #ddd;'><strong>Patient Email</strong></td><td style='padding: 10px; border: 1px solid #ddd;'>" + (data.email || "N/A") + "</td></tr>" +
                     "<tr style='background-color: #f9f9f9;'><td style='padding: 10px; border: 1px solid #ddd;'><strong>Patient Mobile</strong></td><td style='padding: 10px; border: 1px solid #ddd;'>" + (data.mobile || "N/A") + "</td></tr>" +
                     "<tr><td style='padding: 10px; border: 1px solid #ddd;'><strong>Assigned Ward</strong></td><td style='padding: 10px; border: 1px solid #ddd;'>" + (data.ward ? data.ward.toUpperCase() : "N/A") + "</td></tr>" +
                     "<tr style='background-color: #f9f9f9;'><td style='padding: 10px; border: 1px solid #ddd;'><strong>Assigned Doctor</strong></td><td style='padding: 10px; border: 1px solid #ddd;'>" + (data.assigned_doctor || "N/A") + "</td></tr>" +
                     "<tr style='background-color: #f9f9f9;'><td style='padding: 10px; border: 1px solid #ddd;'><strong>Time Slot</strong></td><td style='padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #C44A3A;'>" + (data.assigned_slot || "N/A") + "</td></tr>" +
                     "</table>" +
                     "<div style='text-align: center; margin: 30px 0;'>" +
                     "<img src='" + qrUrl + "' alt='Admission QR Code' style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; width: 150px; height: 150px;' />" +
                     "<p style='font-size: 0.85em; color: #666; margin-top: 10px;'>Scan this QR Code at the entrance gate to check in.</p>" +
                     "</div>" +
                     "<hr style='border: 0; border-top: 1px solid #eee;' />" +
                     "<p style='font-size: 0.85em; color: #888;'>This is an automated notification from the MedFlow Clinical Admissions Team.</p>" +
                     "</div>" +
                     "</div>";
                     
      GmailApp.sendEmail(data.email, subject, body, {
        htmlBody: htmlBody
      });
    }
    
    // Return success response
    return ContentService.createTextOutput(JSON.stringify({ "status": "success" }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": error.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
