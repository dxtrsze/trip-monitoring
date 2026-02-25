from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Vehicle {self.plate_number}>'

class Manpower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # "Driver", "Assistant"

    def __repr__(self):
        return f'<Manpower {self.name} - {self.role}>'

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # "ITR", "SO"
    posting_date = db.Column(db.Date, nullable=False)
    document_number = db.Column(db.String(100), nullable=False)
    item_number = db.Column(db.String(100), nullable=False)
    ordered_qty = db.Column(db.Integer, nullable=False)
    delivered_qty = db.Column(db.Float, nullable=False)
    remaining_open_qty = db.Column(db.Float)
    from_whse_code = db.Column(db.String(50))
    to_whse = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    special_instructions = db.Column(db.Text)
    branch_name = db.Column(db.String(100))
    branch_name_v2 = db.Column(db.String(100))
    document_status = db.Column(db.String(50))  # "O", "C"
    original_due_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    user_code = db.Column(db.String(50))
    po_number = db.Column(db.String(100))
    isms_so_number = db.Column(db.String(100))
    cbm = db.Column(db.Float)
    total_cbm = db.Column(db.Float, default=0.0)  # should be computed (cbm * ordered_qty)
    customer_vendor_code = db.Column(db.String(50))
    customer_vendor_name = db.Column(db.String(100))
    status = db.Column(db.String(50)) # "Not Scheduled", "Scheduled", "Cancelled"

    def __repr__(self):
        return f'<Data {self.document_number}>'

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    delivery_schedule = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Schedule {self.id} - {self.delivery_schedule}>'

# Association tables for many-to-many relationships
trip_driver = db.Table('trip_driver',
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True),
    db.Column('manpower_id', db.Integer, db.ForeignKey('manpower.id'), primary_key=True)
)

trip_assistant = db.Table('trip_assistant',
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True),
    db.Column('manpower_id', db.Integer, db.ForeignKey('manpower.id'), primary_key=True)
)

class Trip(db.Model):
    __tablename__ = 'trip'
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    schedule = db.relationship('Schedule', backref=db.backref('trips', lazy=True))

    trip_number = db.Column(db.Integer, nullable=False) # e.g., Trip 1, Trip 2 on same day
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    vehicle = db.relationship('Vehicle')

    # ✅ Keep ONLY the many-to-many relationships
    drivers = db.relationship('Manpower', secondary=trip_driver, 
                              backref=db.backref('trips_as_driver', lazy='dynamic'))
    assistants = db.relationship('Manpower', secondary=trip_assistant,
                                backref=db.backref('trips_as_assistant', lazy='dynamic'))

    total_cbm = db.Column(db.Float, default=0.0)  # Optional: can be computed

class TripDetail(db.Model):
    __tablename__ = 'trip_detail'
    id = db.Column(db.Integer, primary_key=True)
    document_number = db.Column(db.String(100), nullable=False)  # Store document number directly
    data_ids = db.Column(db.Text)  # Store comma-separated list of data IDs for this document
    area = db.Column(db.String(100))

    # Aggregated values
    total_cbm = db.Column(db.Float, nullable=False, default=0.0)  # Sum of all CBM for this document
    total_ordered_qty = db.Column(db.Integer, nullable=False, default=0)  # Sum of ordered quantities

    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    trip = db.relationship('Trip', backref=db.backref('details', lazy=True))

    status = db.Column(db.String(50))  # "Delivered", "Cancelled" default "Delivered"
    cancel_reason = db.Column(db.String(255))  # Reason for cancellation if status is "Cancelled"
    cause_department = db.Column(db.String(255))  # Department responsible for the cause

    def __repr__(self):
        return f'<TripDetail {self.id} - Document {self.document_number} - Trip {self.trip_id}>' 