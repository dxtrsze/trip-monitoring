Project Overview
The Trip Monitoring Database is a web application designed to manage vehicle trips, schedules, and delivery data. It allows users to upload CSV files containing delivery information, view and edit data, and manage vehicle schedules with associated manpower assignments.

Features
CSV file upload for importing delivery data
View, add, and edit delivery data
View, add, and edit vehicle schedules
Manage vehicle and manpower information
Track delivery quantities and statuses
Generate trip schedules with assigned drivers and assistants

Technology Stack
Backend: Flask
Database: SQLAlchemy (ORM)
Frontend: Vanilla HTML, CSS, JavaScript
Database: SQLite (development), PostgreSQL (production)

Project Structure
trip-monitoring/
├── app.py                  # Main Flask application
├── models.py               # SQLAlchemy models
├── requirements.txt        # Dependencies
├── static/
│   └── style.css           # Basic styling
├── templates/
│   ├── base.html           # Base layout
│   ├── view_data.html      # View all shipment records
│   ├── add_data.html       # Upload CSV form
│   ├── edit_data.html      # Edit individual shipment
│   ├── view_schedule.html  # View all delivery schedules
│   ├── add_schedule.html   # Create new schedule
│   └── edit_schedule.html  # Edit schedule & assign resources
└── uploads/                # Temp directory for CSV uploads (optional)



Database Schema
Models

Vehicles
id (Primary Key)
plate_number (String, unique)
Manpower
id (Primary Key)
name (String)
role (String: e.g., "Driver", "Assistant")

Model
id (Primary Key)
model (String: product model name)
cbu (Float: Cubic Units)

Data (Shipment Records)
id (Primary Key)
posting_date (Date)
document_number (String)
model → Foreign Key to Model
ordered_qty (Integer)
delivered_qty (Integer)
remaining_open_qty (Integer)
pur_slr_uom_if_base_unit (String)
frm_whse_code (String)
to_whse (String)
po_no (String)
special_instructions (Text)
branch_name (String)
document_status (String)
due_date (Date)
user_code (String)
po_number (String)
isms_po_number (String)
total_cbm (Float)
date_created (Date)

Schedule
id (Primary Key)
delivery_schedule (Date)
total_cbm (Float)

Schedule_Detail
id (Primary Key)
schedule_id → Foreign Key to Schedule
branch (String)
area (String)
cbu (Float)
plate_number → Foreign Key to Vehicles
assistant → Foreign Key to Manpower (role=Assistant)
driver → Foreign Key to Manpower (role=Driver)
trip_number (Integer)


Usage
Uploading Data:
Navigate to the Data section
Click "Upload CSV" and select a file with the required format
Review imported data and make any necessary edits
Managing Schedules:
Navigate to the Schedule section
Click "Add Schedule" to create a new delivery schedule
Assign vehicles, drivers, and assistants to each trip
Set delivery dates and trip numbers
Viewing Reports:
Use the view pages to monitor delivery progress
Filter by date, status, or other criteria
Export data for further analysis



class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
 
class Manpower(db.Model):
    __tablename__ = 'manpower'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'Driver', 'Assistant', etc.
 
class ProductModel(db.Model):
    __tablename__ = 'product_models'
    id = db.Column(db.Integer, primary_key=True)
    item_no = db.Column(db.String(50), unique=True, nullable=False)  # e.g., '50QUHW01'
    cbu = db.Column(db.Float, default=0.0)  # Cubic units (can be derived or stored)
 
class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    branch_code = db.Column(db.String(10), unique=True, nullable=False)  # e.g., 'ALS005'
    branch_name = db.Column(db.String(100), nullable=False)  # e.g., 'ALSONS MASBATE'
 
class ShipmentDocument(db.Model):
    __tablename__ = 'shipment_documents'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), unique=True, nullable=False)
    posting_date = db.Column(db.Date, nullable=False)
    document_number = db.Column(db.String(50), unique=True, nullable=False)
    ordered_qty = db.Column(db.Integer, nullable=False)
    delivered_qty = db.Column(db.Float, nullable=False)
    remaining_open_qty = db.Column(db.Float, nullable=True)
    from_warehouse_code = db.Column(db.String(20), nullable=False)
    to_warehouse = db.Column(db.String(20), nullable=False)
    remarks = db.Column(db.Text)
    special_instruction = db.Column(db.Text)
    branch_name = db.Column(db.String(100), nullable=True)
    branch_name_v2 = db.Column(db.String(100), nullable=False)
    document_status = db.Column(db.String(10), nullable=False)  # e.g., 'C' for Closed
    due_date = db.Column(db.Date)
    user_code = db.Column(db.String(50))
    po_number = db.Column(db.String(50), nullable=True)
    isms_so_number = db.Column(db.String(100), nullable=True)  # ISMS SO#
    cbm = db.Column(db.Float, nullable=False)
    customer_vendor_code = db.Column(db.String(50), nullable=True)
    customer_vendor_name = db.Column(db.String(100), nullable=True)
   
class ShipmentLine(db.Model):
    __tablename__ = 'shipment_lines'
    id = db.Column(db.Integer, primary_key=True)
   
    # Foreign Keys
    document_id = db.Column(db.Integer, db.ForeignKey('shipment_documents.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('product_models.id'), nullable=False)
    to_branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
 
    # Line-specific fields
    ordered_qty = db.Column(db.Integer, nullable=False)
    delivered_qty = db.Column(db.Float, nullable=False)
    remaining_open_qty = db.Column(db.Float, nullable=False)
    cbm = db.Column(db.Float, nullable=False)  # Cubic meters for this line
    remarks = db.Column(db.Text)
    special_instruction = db.Column(db.Text)
 
    # Relationships
    document = db.relationship('ShipmentDocument', backref=db.backref('lines', lazy=True))
    product = db.relationship('ProductModel')
    destination_branch = db.relationship('Branch')
 
# Optional: Schedule-related tables (from your original spec)
class DeliverySchedule(db.Model):
    __tablename__ = 'delivery_schedules'
    id = db.Column(db.Integer, primary_key=True)
    delivery_date = db.Column(db.Date, nullable=False)
    total_cbm = db.Column(db.Float, default=0.0) # this should sum the cbu of all the items in the ScheduleDetail
 
class ScheduleDetail(db.Model):
    __tablename__ = 'schedule_details'
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('delivery_schedules.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    area = db.Column(db.String(100))
    cbu = db.Column(db.Float)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('manpower.id'))
    assistant_id = db.Column(db.Integer, db.ForeignKey('manpower.id'))
    trip_number = db.Column(db.Integer)
 
    schedule = db.relationship('DeliverySchedule', backref=db.backref('details', lazy=True))
    branch = db.relationship('Branch')
    vehicle = db.relationship('Vehicle')
    driver = db.relationship('Manpower', foreign_keys=[driver_id])
    assistant = db.relationship('Manpower', foreign_keys=[assistant_id])




# Features to add:`1.
1. class TripDetail should not save all the document row in class Data, should save the grouped document number only. (done)
2. class TripDetail should have a status "Delivered", "Cancelled" default "Delivered" if trip is saved. (done)
3. if TripDetail is cancelled, the data.status should be updated to "Not Scheduled" (done)
4. validate class data posting_date & document_number & model upon upload (wish list)
5. when a schedule is saved, class Data.delivered_qty should be updated same to data.ordered_qty
    added data.delivered_qty = data.ordered_qty or 0.0 in add_schedule():
6. 
7. cancelled trip_details should have remarks
8. trip printing
9. report
    a. date, total trips
    b. date, per trip, count of total document, count of cancelled document
