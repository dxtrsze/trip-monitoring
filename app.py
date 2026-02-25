import os
import csv
from dateutil import parser as date_parser
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import pandas as pd
from models import db, Vehicle, Manpower, Data, Schedule, Trip, TripDetail
from sqlalchemy import func



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trip_monitoring.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv'}

# Helper function to parse date
def parse_date_flexible(date_str):
    """Parse common date formats like '10/2/25', '10/02/2025', '2025-10-02'."""
    if not date_str or date_str.strip() == '':
        return None
    try:
        # Parse and ensure it's a date (not datetime)
        parsed = date_parser.parse(date_str.strip(), dayfirst=False)
        return parsed.date()
    except (ValueError, TypeError):
        raise ValueError(f"Unable to parse date: '{date_str}'")

# Home page
@app.route('/')
def index():
    return render_template('base.html')

# Data management routes
@app.route('/data')
def view_data():
   # ✅ Only fetch records with status = 'Not Scheduled'
    not_scheduled_data = Data.query.filter_by(status='Not Scheduled').all()
    return render_template('view_data.html', data=not_scheduled_data)

@app.route('/data/scheduled')
def view_scheduled_data():
    # This page will use JavaScript to fetch scheduled data via API
    return render_template('view_scheduled_data.html')
 
@app.route('/data/download_template')
def download_csv_template():
    from io import StringIO
    from flask import Response

    # Create an in-memory CSV
    template = StringIO()
    writer = csv.writer(template)

    # Write headers matching Data model fields (in order)
    writer.writerow([
        "Type",
        "Posting Date",
        "Document Number",
        "Item No.",
        "Ordered Quantity",
        "Delivered Quantity",
        "Remaining Open Qty",
        "From Warehouse Code",
        "To Warehouse",
        "Remarks",
        "Special Instruction",
        "Branch Name",
        "Branch Name v2",
        "Document Status",
        "Due Date",
        "User_Code",
        "PO Number",
        "ISMS SO#",
        "CBM",
        "Customer/Vendor Code",
        "Customer/Vendor Name"
    ])

    # Write one sample row for guidance (based on your data)
    writer.writerow([
        "ITR",
        "2025-10-02",
        "345709",
        "50QUHW01",
        "5",
        "5.00",
        "0.00",
        "FWH14P1F",
        "ALS005",
        "",
        "",
        "ALSONS MASBATE",
        "",
        "C",
        "2025-10-04",
        "rexconde",
        "916253958",
        "202509-0020594",
        "0.09",
        "",
        ""
    ])

    template.seek(0)

    # Return as downloadable CSV file
    return Response(
        template.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=data_upload_template.csv'}
    )

@app.route('/data/upload', methods=['GET', 'POST'])
def upload_data():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if not file.filename.lower().endswith('.csv'):
            flash('Only CSV files are allowed', 'error')
            return redirect(request.url)

        try:
            stream = file.stream.read().decode("utf-8-sig").splitlines()
            csv_reader = csv.DictReader(stream)

            expected_headers = {
                "Type", "Posting Date", "Document Number", "Item No.",
                "Ordered Quantity", "Delivered Quantity", "Remaining Open Qty",
                "From Warehouse Code", "To Warehouse", "Remarks",
                "Special Instruction", "Branch Name", "Branch Name v2",
                "Document Status", "Due Date", "User_Code", "PO Number",
                "ISMS SO#", "CBM", "Customer/Vendor Code", "Customer/Vendor Name"
            }

            if set(csv_reader.fieldnames) != expected_headers:
                missing = expected_headers - set(csv_reader.fieldnames)
                extra = set(csv_reader.fieldnames) - expected_headers
                msg = ""
                if missing:
                    msg += f"Missing columns: {', '.join(missing)}. "
                if extra:
                    msg += f"Unexpected columns: {', '.join(extra)}."
                flash(f"Invalid CSV headers. {msg}", 'error')
                return redirect(request.url)

            records_added = 0
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    # ✅ Use ONLY the flexible parser — remove old strptime lines!
                    posting_date = parse_date_flexible(row["Posting Date"])
                    due_date = parse_date_flexible(row["Due Date"])
                    cbm = float(row["CBM"]) if row["CBM"] else 0.0
                    ordered_qty = float(row["Ordered Quantity"]) if row["Ordered Quantity"] else 0

                    # Helper to convert empty strings to None
                    def clean(val):
                        return val if val != '' else None

                    data_entry = Data(
                        type=row["Type"],
                        posting_date=posting_date,
                        document_number=row["Document Number"],
                        item_number=row["Item No."],
                        ordered_qty=int(float(row["Ordered Quantity"])) if row["Ordered Quantity"] else 0,
                        delivered_qty=float(row["Delivered Quantity"]) if row["Delivered Quantity"] else 0.0,
                        remaining_open_qty=float(row["Remaining Open Qty"]) if row["Remaining Open Qty"] else 0.0,
                        from_whse_code=clean(row["From Warehouse Code"]),
                        to_whse=clean(row["To Warehouse"]),
                        remarks=clean(row["Remarks"]),
                        special_instructions=clean(row["Special Instruction"]),
                        branch_name=clean(row["Branch Name"]),
                        branch_name_v2=clean(row["Branch Name v2"]),
                        document_status=clean(row["Document Status"]),
                        original_due_date=due_date,
                        due_date=due_date,
                        user_code=clean(row["User_Code"]),
                        po_number=clean(row["PO Number"]),
                        isms_so_number=clean(row["ISMS SO#"]),
                        cbm=float(row["CBM"]) if row["CBM"] else 0.0,
                        total_cbm = round(cbm * ordered_qty, 2),
                        customer_vendor_code=clean(row["Customer/Vendor Code"]),
                        customer_vendor_name=clean(row["Customer/Vendor Name"]),
                        status="Not Scheduled"
                    )

                    db.session.add(data_entry)
                    records_added += 1

                except ValueError as ve:
                    flash(f"Row {row_num}: Invalid data format – {str(ve)}", 'error')
                    db.session.rollback()
                    return redirect(request.url)
                except Exception as e:
                    flash(f"Row {row_num}: Unexpected error – {str(e)}", 'error')
                    db.session.rollback()
                    return redirect(request.url)

            db.session.commit()
            flash(f"Successfully uploaded {records_added} record(s)!", 'success')
            return redirect(url_for('view_data'))

        except UnicodeDecodeError:
            flash("File encoding error. Please upload a UTF-8 CSV file.", 'error')
            return redirect(request.url)
        except Exception as e:
            flash(f"Failed to process file: {str(e)}", 'error')
            db.session.rollback()
            return redirect(request.url)

    return render_template('add_data.html')


@app.route('/data/<int:id>/edit', methods=['GET', 'POST'])
def edit_data(id):
    data = Data.query.get_or_404(id)

    if request.method == 'POST':
        try:
            # Helper to safely get form values (empty string → None for optional fields)
            def get_form_value(key, default=None):
                val = request.form.get(key, '').strip()
                return val if val != '' else default

            # Update string fields
            data.type = request.form['type']
            data.document_number = request.form['document_number']
            data.item_number = request.form['item_number']
            data.from_whse_code = get_form_value('from_whse_code')
            data.to_whse = get_form_value('to_whse')
            data.pur_slr_uom_if_base_unit = get_form_value('pur_slr_uom_if_base_unit')
            data.branch_name = get_form_value('branch_name')
            data.branch_name_v2 = get_form_value('branch_name_v2')
            data.document_status = get_form_value('document_status')
            data.po_number = get_form_value('po_number')
            data.isms_so_number = get_form_value('isms_so_number')
            data.customer_vendor_code = get_form_value('customer_vendor_code')
            data.customer_vendor_name = get_form_value('customer_vendor_name')
            data.user_code = get_form_value('user_code')
            data.special_instructions = get_form_value('special_instructions')
            data.remarks = get_form_value('remarks')
            data.status = request.form['status']  # Required (dropdown)

            # Handle dates
            posting_date_str = request.form.get('posting_date')
            data.posting_date = datetime.strptime(posting_date_str, '%Y-%m-%d').date() if posting_date_str else None

            due_date_str = request.form.get('due_date')
            data.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

            # Handle numeric fields
            data.ordered_qty = int(request.form['ordered_qty'])
            data.delivered_qty = float(request.form['delivered_qty'])
            data.remaining_open_qty = float(request.form['remaining_open_qty']) if request.form['remaining_open_qty'] else 0.0
            data.cbm = float(request.form['cbm']) if request.form['cbm'] else 0.0

            # Save to DB
            db.session.commit()
            flash('Record updated successfully!', 'success')
            return redirect(url_for('view_data'))

        except ValueError as ve:
            flash(f'Invalid input: {str(ve)}', 'error')
            db.session.rollback()
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            db.session.rollback()

    # GET request: render edit form
    return render_template('edit_data.html', data=data)

# Resource management routes
@app.route('/vehicles')
def manage_vehicles():
    vehicles = Vehicle.query.all()
    return render_template('manage_vehicles.html', vehicles=vehicles)

@app.route('/vehicles/add', methods=['POST'])
def add_vehicle():
    plate_number = request.form.get('plate_number')

    if not plate_number:
        flash('Plate number is required')
        return redirect(url_for('manage_vehicles'))

    try:
        vehicle = Vehicle(plate_number=plate_number)
        db.session.add(vehicle)
        db.session.commit()
        flash('Vehicle added successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding vehicle: {str(e)}')

    return redirect(url_for('manage_vehicles'))

@app.route('/vehicles/<int:id>/delete', methods=['POST'])
def delete_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)

    try:
        db.session.delete(vehicle)
        db.session.commit()
        flash('Vehicle deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting vehicle: {str(e)}')

    return redirect(url_for('manage_vehicles'))

@app.route('/manpower')
def manage_manpower():
    manpower = Manpower.query.all()
    return render_template('manage_manpower.html', manpower=manpower)

@app.route('/manpower/add', methods=['POST'])
def add_manpower():
    name = request.form.get('name')
    role = request.form.get('role')

    if not name or not role:
        flash('Name and role are required')
        return redirect(url_for('manage_manpower'))

    try:
        person = Manpower(name=name, role=role)
        db.session.add(person)
        db.session.commit()
        flash('Manpower added successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding manpower: {str(e)}')

    return redirect(url_for('manage_manpower'))

@app.route('/manpower/<int:id>/delete', methods=['POST'])
def delete_manpower(id):
    person = Manpower.query.get_or_404(id)

    try:
        db.session.delete(person)
        db.session.commit()
        flash('Manpower deleted successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting manpower: {str(e)}')

    return redirect(url_for('manage_manpower'))

# API endpoint to fetch documents with specific status and due date
@app.route('/api/documents', methods=['GET'])
def get_documents():
    status = request.args.get('status')
    due_date = request.args.get('due_date')

    query = Data.query

    if status:
        query = query.filter_by(status=status)

    if due_date:
        try:
            # Parse the date string
            date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            query = query.filter_by(due_date=date_obj)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD format.'}), 400

    documents = query.all()
    result = []
    for doc in documents:
        result.append({
            'id': doc.id,
            'document_number': doc.document_number,
            'due_date': doc.due_date.strftime('%Y-%m-%d') if doc.due_date else None,
            'status': doc.status,
            'type': doc.type,
            'branch_name': doc.branch_name,
            'cbm': doc.cbm
        })

    return jsonify(result)

# API endpoint to search scheduled documents and class data
@app.route('/api/search_scheduled', methods=['GET'])
def search_scheduled():
    search_term = request.args.get('search', '').strip()
    search_type = request.args.get('type', 'document')  # 'document' or 'class'
 
    if not search_term:
        return jsonify([])
 
    query = Data.query.filter(Data.status == 'Scheduled')
 
    if search_type == 'document':
        # Search by document number
        query = query.filter(Data.document_number.contains(search_term))
    elif search_type == 'class':
        # Search by class data (branch name)
        query = query.filter(
            db.or_(
                Data.branch_name.contains(search_term),
                Data.branch_name_v2.contains(search_term)
            )
        )
 
    documents = query.all()
    result = []
    for doc in documents:
        result.append({
            'id': doc.id,
            'document_number': doc.document_number,
            'posting_date': doc.posting_date.strftime('%Y-%m-%d') if doc.posting_date else None,
            'item_number': doc.item_number,
            'ordered_qty': doc.ordered_qty,
            'total_cbm': doc.total_cbm,
            'delivered_qty': doc.delivered_qty,
            'branch_name': doc.branch_name or doc.branch_name_v2 or '',
            'status': doc.status,
            'document_status': doc.document_status,
            'due_date': doc.due_date.strftime('%Y-%m-%d') if doc.due_date else None
        })
 
    return jsonify(result)

@app.route('/schedules')
def view_schedule():
    schedules = Schedule.query.order_by(Schedule.delivery_schedule.desc()).all()
    return render_template('view_schedule.html', schedules=schedules)


@app.route('/schedules/add', methods=['GET', 'POST'])
def add_schedule():
    if request.method == 'POST':
        try:
            delivery_date = datetime.strptime(request.form['delivery_schedule'], '%Y-%m-%d').date()
            
            # Create Schedule
            schedule = Schedule(delivery_schedule=delivery_date)
            db.session.add(schedule)
            db.session.flush()  # Get schedule.id

            trip_count = int(request.form.get('trip_count', 0))
            for i in range(1, trip_count + 1):
                vehicle_id = request.form.get(f'vehicle_{i}')
                # ✅ NEW CODE (use this)
                driver_ids = request.form.getlist(f'driver_{i}')
                assistant_ids = request.form.getlist(f'assistant_{i}')

                # Validate: at least one driver and a vehicle
                if not vehicle_id or not driver_ids:
                    continue

                # Convert to integers (filter out empty strings)
                driver_ids = [int(d) for d in driver_ids if d.strip()]
                assistant_ids = [int(a) for a in assistant_ids if a.strip()]

                # Create Trip WITHOUT driver_id/assistant_id
                trip = Trip(
                    schedule_id=schedule.id,
                    trip_number=i,
                    vehicle_id=vehicle_id,
                    total_cbm=0.0
                )
                db.session.add(trip)
                db.session.flush()  # Get trip.id

                # ✅ Assign MULTIPLE drivers
                trip.drivers.clear()  # Optional (new trip, so empty anyway)
                for did in driver_ids:
                    driver = Manpower.query.get(did)
                    if driver:
                        trip.drivers.append(driver)

                # ✅ Assign MULTIPLE assistants
                trip.assistants.clear()
                for aid in assistant_ids:
                    assistant = Manpower.query.get(aid)
                    if assistant:
                        trip.assistants.append(assistant)
                db.session.add(trip)
                db.session.flush()

                # Add all selected drivers and assistants to the trip
                for driver_id in driver_ids:
                    driver = Manpower.query.get(driver_id)
                    if driver and driver not in trip.drivers:
                        trip.drivers.append(driver)

                for assistant_id in assistant_ids:
                    assistant = Manpower.query.get(assistant_id)
                    if assistant and assistant not in trip.assistants:
                        trip.assistants.append(assistant)

                # Get selected data IDs for this trip
                data_ids_str = request.form.get(f'trip_{i}_data_ids', '')
                # Split the comma-separated string into individual IDs
                data_ids = data_ids_str.split(',') if data_ids_str else []

                # Group data by document_number to create aggregated TripDetail entries
                doc_groups = {}
                for data_id in data_ids:
                    if not data_id:
                        continue
                    data = Data.query.get(data_id)
                    if data:
                        doc_num = data.document_number
                        if doc_num not in doc_groups:
                            doc_groups[doc_num] = {
                                'data_ids': [],
                                'total_cbm': 0.0,
                                'total_ordered_qty': 0,
                                'area': data.branch_name or data.branch_name_v2 or ''
                            }

                        doc_groups[doc_num]['data_ids'].append(data.id)
                        doc_groups[doc_num]['total_cbm'] += data.cbm * data.ordered_qty or 0.0
                        doc_groups[doc_num]['total_ordered_qty'] += data.ordered_qty or 0

                        # Mark as Scheduled
                        data.status = "Scheduled"
                        data.delivered_qty = data.ordered_qty or 0.0

                # Create aggregated TripDetail entries
                trip_total_cbm = 0.0
                for doc_num, doc_data in doc_groups.items():
                    detail = TripDetail(
                        document_number=doc_num,
                        data_ids=','.join(str(id) for id in doc_data['data_ids']),
                        trip_id=trip.id,
                        area=doc_data['area'],
                        total_cbm=doc_data['total_cbm'],
                        total_ordered_qty=doc_data['total_ordered_qty'],
                        status="Delivered"
                    )
                    db.session.add(detail)
                    trip_total_cbm += doc_data['total_cbm']

                trip.total_cbm = trip_total_cbm

            db.session.commit()
            flash("Schedule created successfully!", "success")
            return redirect(url_for('view_schedule'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
            return redirect(request.url)

    # GET: Load resources for form
    vehicles = Vehicle.query.all()
    drivers = Manpower.query.filter_by(role='Driver').all()
    assistants = Manpower.query.filter_by(role='Assistant').all()
    return render_template('add_schedule.html',
                         vehicles=vehicles,
                         drivers=drivers,
                         assistants=assistants)


@app.route('/api/not_scheduled')
def api_not_scheduled():
    due_date_str = request.args.get('due_date')
    if not due_date_str:
        return jsonify([])

    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
    # Subquery: Get all "Not Scheduled" data with due_date == selected date
    subq = Data.query.filter(
        Data.status == 'Not Scheduled',
        Data.due_date == due_date
    ).subquery()

    # Group by document_number and aggregate
    results = db.session.query(
        subq.c.document_number,
        func.sum(subq.c.total_cbm).label('total_cbm'),
        func.sum(subq.c.ordered_qty).label('ordered_qty'),
        func.min(subq.c.branch_name).label('branch_name'),
        func.min(subq.c.branch_name_v2).label('branch_name_v2'),
        func.min(subq.c.due_date).label('due_date'),
        func.group_concat(subq.c.id).label('data_ids')  # Collect all IDs for this doc
    ).group_by(subq.c.document_number).all()

    documents = []
    for row in results:
        # Determine branch (prefer branch_name, fallback to v2)
        branch = row.branch_name or row.branch_name_v2 or '—'
        
        documents.append({
            'document_number': row.document_number,
            'total_cbm': float(row.total_cbm) if row.total_cbm else 0.0,
            'branch': branch,
            'due_date': row.due_date.strftime('%Y-%m-%d') if row.due_date else '',
            'data_ids': row.data_ids.split(',')  # List of all Data.id for this doc
        })

    return jsonify(documents)

# view_schedule.html individual delete button for each trip
@app.route('/cancel_trip_detail', methods=['POST'])
def cancel_trip_detail():
    try:
        data = request.get_json()
        document_number = data.get('document_number')
        schedule_id = data.get('schedule_id')
        trip_number = data.get('trip_number')
        cancel_reason = data.get('cancel_reason')
        cancel_department = data.get('cancel_department')
        
        if not document_number or not schedule_id or not trip_number:
            return jsonify({'success': False, 'message': 'Missing required parameters'}), 400
            
        # Find the trip detail with the given document number
        schedule = Schedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'success': False, 'message': 'Schedule not found'}), 404
            
        trip = Trip.query.filter_by(schedule_id=schedule_id, trip_number=trip_number).first()
        if not trip:
            return jsonify({'success': False, 'message': 'Trip not found'}), 404
            
        trip_detail = TripDetail.query.filter_by(trip_id=trip.id, document_number=document_number).first()
        if not trip_detail:
            return jsonify({'success': False, 'message': 'Trip detail not found'}), 404
            
        # Update the status in trip_detail
        trip_detail.status = "Cancelled"
        trip_detail.cancel_reason = cancel_reason
        trip_detail.cause_department = cancel_department
        
        # Also update the status of all associated Data records
        if trip_detail.data_ids:
            data_ids = trip_detail.data_ids.split(',')
            for data_id in data_ids:
                data_record = Data.query.get(data_id)
                if data_record:
                    data_record.status = "Not Scheduled"
                    
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500\
            
            
# Reports page route
@app.route('/reports')
def reports():
    return render_template('reports.html')

# Report generation routes
@app.route('/generate_report')
def generate_report():
    report_type = request.args.get('report_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        if report_type == 'scheduled_trips':
            return generate_scheduled_trips_report(start, end)
        elif report_type == 'cancelled_trips':
            return generate_cancelled_trips_report(start, end)
        elif report_type == 'vehicle_utilization':
            return generate_vehicle_utilization_report(start, end)
        elif report_type == 'driver_performance':
            return generate_driver_performance_report(start, end)
        else:
            return jsonify({'success': False, 'message': 'Invalid report type'})
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid date format: {str(e)}'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error generating report: {str(e)}'})

def generate_scheduled_trips_report(start_date, end_date):
    # Query all scheduled trips within the date range
    schedules = Schedule.query.filter(
        Schedule.delivery_schedule >= start_date,
        Schedule.delivery_schedule <= end_date
    ).all()

    headers = [
        'Schedule Date', 'Trip Number', 'Vehicle', 'Driver', 'Assistant', 
        'Document Number', 'Area', 'Total CBM', 'Total Ordered Qty', 'Status'
    ]

    rows = []
    for schedule in schedules:
        for trip in schedule.trips:
            for detail in trip.details:
                driver_name = trip.driver.name if trip.driver else 'N/A'
                assistant_name = trip.assistant.name if trip.assistant else 'N/A'
                vehicle_plate = trip.vehicle.plate_number if trip.vehicle else 'N/A'

                rows.append([
                    schedule.delivery_schedule.strftime('%Y-%m-%d'),
                    trip.trip_number,
                    vehicle_plate,
                    driver_name,
                    assistant_name,
                    detail.document_number,
                    detail.area or 'N/A',
                    f"{detail.total_cbm:.2f}",
                    detail.total_ordered_qty,
                    detail.status
                ])

    return jsonify({
        'success': True,
        'headers': headers,
        'rows': rows
    })

def generate_cancelled_trips_report(start_date, end_date):
    # Query all cancelled trip details within the date range
    cancelled_details = db.session.query(TripDetail, Trip, Schedule).join(
        Trip, TripDetail.trip_id == Trip.id
    ).join(
        Schedule, Trip.schedule_id == Schedule.id
    ).filter(
        Schedule.delivery_schedule >= start_date,
        Schedule.delivery_schedule <= end_date,
        TripDetail.status == 'Cancelled'
    ).all()

    headers = [
        'Schedule Date', 'Trip Number', 'Vehicle', 'Driver', 
        'Document Number', 'Area', 'Total CBM', 'Cancel Reason', 'Cause Department'
    ]

    rows = []
    for detail, trip, schedule in cancelled_details:
        driver_name = trip.driver.name if trip.driver else 'N/A'
        vehicle_plate = trip.vehicle.plate_number if trip.vehicle else 'N/A'

        rows.append([
            schedule.delivery_schedule.strftime('%Y-%m-%d'),
            trip.trip_number,
            vehicle_plate,
            driver_name,
            detail.document_number,
            detail.area or 'N/A',
            f"{detail.total_cbm:.2f}",
            detail.cancel_reason or 'N/A',
            detail.cause_department or 'N/A'
        ])

    return jsonify({
        'success': True,
        'headers': headers,
        'rows': rows
    })

def generate_vehicle_utilization_report(start_date, end_date):
    # Query all trips within the date range
    trips = db.session.query(Trip, Schedule).join(
        Schedule, Trip.schedule_id == Schedule.id
    ).filter(
        Schedule.delivery_schedule >= start_date,
        Schedule.delivery_schedule <= end_date
    ).all()

    # Group by vehicle
    vehicle_stats = {}
    for trip, schedule in trips:
        vehicle_id = trip.vehicle_id
        vehicle_plate = trip.vehicle.plate_number

        if vehicle_id not in vehicle_stats:
            vehicle_stats[vehicle_id] = {
                'plate_number': vehicle_plate,
                'total_trips': 0,
                'total_cbm': 0.0,
                'dates_used': set()
            }

        vehicle_stats[vehicle_id]['total_trips'] += 1
        vehicle_stats[vehicle_id]['total_cbm'] += trip.total_cbm
        vehicle_stats[vehicle_id]['dates_used'].add(schedule.delivery_schedule)

    headers = [
        'Vehicle Plate Number', 'Total Trips', 'Total CBM', 'Days Used', 'Average CBM per Trip'
    ]

    rows = []
    for vehicle_id, stats in vehicle_stats.items():
        days_used = len(stats['dates_used'])
        avg_cbm = stats['total_cbm'] / stats['total_trips'] if stats['total_trips'] > 0 else 0

        rows.append([
            stats['plate_number'],
            stats['total_trips'],
            f"{stats['total_cbm']:.2f}",
            days_used,
            f"{avg_cbm:.2f}"
        ])

    return jsonify({
        'success': True,
        'headers': headers,
        'rows': rows
    })

def generate_driver_performance_report(start_date, end_date):
    # Query all trips within the date range
    trips = db.session.query(Trip, Schedule).join(
        Schedule, Trip.schedule_id == Schedule.id
    ).filter(
        Schedule.delivery_schedule >= start_date,
        Schedule.delivery_schedule <= end_date
    ).all()

    # Group by driver
    driver_stats = {}
    for trip, schedule in trips:
        driver_id = trip.driver_id
        driver_name = trip.driver.name

        if driver_id not in driver_stats:
            driver_stats[driver_id] = {
                'name': driver_name,
                'total_trips': 0,
                'total_cbm': 0.0,
                'dates_worked': set()
            }

        driver_stats[driver_id]['total_trips'] += 1
        driver_stats[driver_id]['total_cbm'] += trip.total_cbm
        driver_stats[driver_id]['dates_worked'].add(schedule.delivery_schedule)

    headers = [
        'Driver Name', 'Total Trips', 'Total CBM', 'Days Worked', 'Average CBM per Trip'
    ]

    rows = []
    for driver_id, stats in driver_stats.items():
        days_worked = len(stats['dates_worked'])
        avg_cbm = stats['total_cbm'] / stats['total_trips'] if stats['total_trips'] > 0 else 0

        rows.append([
            stats['name'],
            stats['total_trips'],
            f"{stats['total_cbm']:.2f}",
            days_worked,
            f"{avg_cbm:.2f}"
        ])

    return jsonify({
        'success': True,
        'headers': headers,
        'rows': rows
    })

@app.route('/export_report')
def export_report():
    report_type = request.args.get('report_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    try:
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Generate report data
        if report_type == 'scheduled_trips':
            data = generate_scheduled_trips_report(start, end)
            filename = f"scheduled_trips_{start_date}_to_{end_date}.csv"
        elif report_type == 'cancelled_trips':
            data = generate_cancelled_trips_report(start, end)
            filename = f"cancelled_trips_{start_date}_to_{end_date}.csv"
        elif report_type == 'vehicle_utilization':
            data = generate_vehicle_utilization_report(start, end)
            filename = f"vehicle_utilization_{start_date}_to_{end_date}.csv"
        elif report_type == 'driver_performance':
            data = generate_driver_performance_report(start, end)
            filename = f"driver_performance_{start_date}_to_{end_date}.csv"
        else:
            return "Invalid report type", 400

        if not data.get_json().get('success'):
            return "Error generating report", 500

        # Convert JSON to CSV
        df = pd.DataFrame(
            data.get_json().get('rows'),
            columns=data.get_json().get('headers')
        )

        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        # Return as downloadable CSV file
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

    except ValueError as e:
        return f"Invalid date format: {str(e)}", 400
    except Exception as e:
        return f"Error exporting report: {str(e)}", 500

@app.route('/grid')
def grid():
    datas = Data.query.all()
    return render_template('grid_data.html', data=datas)
    
@app.route('/grid-data')
def grid_data():
    datas = Data.query.all()
    grid_data = [[
        data.id,
        data.posting_date.strftime('%Y-%m-%d') if data.posting_date else '',
        data.document_number,
        data.item_number,
        data.ordered_qty,
        data.total_cbm,
        data.delivered_qty,
        data.branch_name,
        data.status,
        data.due_date.strftime('%Y-%m-%d') if data.due_date else ''
    ] for data in datas]
    return jsonify(grid_data)

@app.route('/update-grid', methods=['POST'])
def update_grid():
    full_data = request.json.get('updatedData', [])
    
    for row in full_data:
        if len(row) == 11:  # [id, posting_date, document_number, item_number, ordered_qty, total_cbm, delivered_qty, branch_name, status, due_date]
            data_id, posting_date, document_number, item_number, ordered_qty, total_cbm, delivered_qty, branch_name, status, due_date = row
            
            if data_id:  # Existing data
                data = Data.query.get(data_id)
                if data:
                    data.posting_date = datetime.strptime(posting_date, '%Y-%m-%d').date() if posting_date else None
                    data.document_number = document_number
                    data.item_number = item_number
                    data.ordered_qty = int(ordered_qty) if str(ordered_qty).isdigit() else 0
                    data.total_cbm = float(total_cbm) if total_cbm else 0.0
                    data.delivered_qty = float(delivered_qty) if delivered_qty else 0.0
                    data.branch_name = branch_name
                    data.status = status
                    data.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
                    db.session.add(data)  # Update the existing record
            else:  # New data
                new_data = Data(
                    posting_date=datetime.strptime(posting_date, '%Y-%m-%d').date() if posting_date else None,
                    document_number=document_number,
                    item_number=item_number,
                    ordered_qty=int(ordered_qty) if str(ordered_qty).isdigit() else 0,
                    total_cbm=float(total_cbm) if total_cbm else 0.0,
                    delivered_qty=float(delivered_qty) if delivered_qty else 0.0,
                    branch_name=branch_name,
                    status=status,
                    due_date=datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None,
                    type="ITR"  # You need to set a default type or get it from the row
                )
                db.session.add(new_data)
    
    db.session.commit()
    return jsonify({"status": "success"})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5015)
