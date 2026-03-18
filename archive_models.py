"""
Archive Models Module

These models use the same SQLAlchemy instance as the main app but are bound to the archive database.
All models mirror the main database models for archiving purposes.
"""
from models import db
from datetime import datetime


class Vehicle(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'vehicle'

    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Active')
    capacity = db.Column(db.Float, nullable=True)
    dept = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Vehicle {self.plate_number}>'


class Manpower(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'manpower'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
        return f'<Manpower {self.name} - {self.role}>'


class Data(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'data'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
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
    document_status = db.Column(db.String(50))
    original_due_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    user_code = db.Column(db.String(50))
    po_number = db.Column(db.String(100))
    isms_so_number = db.Column(db.String(100))
    cbm = db.Column(db.Float)
    total_cbm = db.Column(db.Float, default=0.0)
    customer_vendor_code = db.Column(db.String(50))
    customer_vendor_name = db.Column(db.String(100))
    status = db.Column(db.String(50))
    delivery_type = db.Column(db.String(100), nullable=True)
    delete_remarks = db.Column(db.String(255), nullable=True)
    detailed_remarks = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Data {self.document_number}>'


class Schedule(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'schedule'

    id = db.Column(db.Integer, primary_key=True)
    delivery_schedule = db.Column(db.Date, nullable=False)
    plate_number = db.Column(db.String(50), nullable=True)
    capacity = db.Column(db.Float, nullable=True)
    actual = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Schedule {self.id} - {self.delivery_schedule}>'


# Association tables for many-to-many relationships
# These have different names to avoid conflicts with main database tables
trip_driver = db.Table('archive_trip_driver',
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True),
    db.Column('manpower_id', db.Integer, db.ForeignKey('manpower.id'), primary_key=True),
    info={'bind_key': 'archive'}
)

trip_assistant = db.Table('archive_trip_assistant',
    db.Column('trip_id', db.Integer, db.ForeignKey('trip.id'), primary_key=True),
    db.Column('manpower_id', db.Integer, db.ForeignKey('manpower.id'), primary_key=True),
    info={'bind_key': 'archive'}
)


class Trip(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'trip'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)
    trip_number = db.Column(db.Integer, nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    total_cbm = db.Column(db.Float, default=0.0)


class TripDetail(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'trip_detail'

    id = db.Column(db.Integer, primary_key=True)
    document_number = db.Column(db.String(100), nullable=True)
    branch_name_v2 = db.Column(db.String(100), nullable=False)
    data_ids = db.Column(db.Text)
    area = db.Column(db.String(100))
    total_cbm = db.Column(db.Float, nullable=False, default=0.0)
    total_ordered_qty = db.Column(db.Integer, nullable=False, default=0)
    total_delivered_qty = db.Column(db.Integer, nullable=False, default=0)
    backload_qty = db.Column(db.Integer, nullable=True, default=0)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    status = db.Column(db.String(50))
    cancel_reason = db.Column(db.String(255))
    cause_department = db.Column(db.String(255))
    arrive = db.Column(db.DateTime)
    departure = db.Column(db.DateTime)
    reason = db.Column(db.Text)
    delivery_type = db.Column(db.String(100), nullable=True)
    delivery_order = db.Column(db.Integer, nullable=True)
    original_due_date = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<TripDetail {self.id} - Branch {self.branch_name_v2}>'


class Cluster(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'cluster'

    id = db.Column(db.Integer, primary_key=True)
    no = db.Column(db.String(50), nullable=False)
    weekly_schedule = db.Column(db.String(100))
    delivered_by = db.Column(db.String(100))
    location = db.Column(db.String(100))
    category = db.Column(db.String(100))
    area = db.Column(db.String(100))
    branch = db.Column(db.String(100))
    frequency = db.Column(db.String(100))
    frequency_count = db.Column(db.String(50))
    tl = db.Column(db.String(100))
    delivery_mode = db.Column(db.String(100))
    active_branches = db.Column(db.Text)

    def __repr__(self):
        return f'<Cluster {self.no} - {self.branch}>'


class Odo(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'odo'

    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(50), db.ForeignKey('vehicle.plate_number'), nullable=False)
    odometer_reading = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.now)
    created_by = db.Column(db.String(100), nullable=False)
    litters = db.Column(db.Float, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    price_per_litter = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Odo {self.id} - {self.plate_number}>'


class User(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(50), nullable=False, default='user')
    status = db.Column(db.String(50), nullable=False, default='active')
    daily_rate = db.Column(db.Float, nullable=True)
    sched_start = db.Column(db.String(10), nullable=True)
    sched_end = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f'<User {self.email} - {self.position}>'


class TimeLog(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'time_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_in = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime, nullable=True)
    hrs_rendered = db.Column(db.Float, nullable=True)
    daily_rate = db.Column(db.Float, nullable=True)
    over_time = db.Column(db.Float, nullable=True, default=0.0)
    pay = db.Column(db.Float, nullable=True)
    ot_pay = db.Column(db.Float, nullable=True, default=0.0)
    sched_start = db.Column(db.String(10), nullable=True)
    sched_end = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<TimeLog {self.id} - User {self.user_id}>'


class DailyVehicleCount(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'daily_vehicle_count'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    qty = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<DailyVehicleCount {self.date} - {self.qty}>'


class Backload(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'backload'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
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
    document_status = db.Column(db.String(50))
    original_due_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    user_code = db.Column(db.String(50))
    po_number = db.Column(db.String(100))
    isms_so_number = db.Column(db.String(100))
    cbm = db.Column(db.Float)
    total_cbm = db.Column(db.Float, default=0.0)
    customer_vendor_code = db.Column(db.String(50))
    customer_vendor_name = db.Column(db.String(100))
    status = db.Column(db.String(50))
    delivery_type = db.Column(db.String(100), nullable=True)
    backload_qty = db.Column(db.Integer, nullable=False, default=0)
    backload_remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f'<Backload {self.document_number}>'


class LCLSummary(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'lcl_summary'

    id = db.Column(db.Integer, primary_key=True)
    posting_date = db.Column(db.Date, nullable=False)
    company = db.Column(db.String(100), nullable=False, default='FINDEN')
    dept = db.Column(db.String(100), nullable=False, default='LOGISTICS')
    branch_name = db.Column(db.String(100), nullable=False)
    tot_qty = db.Column(db.Integer, nullable=False, default=0)
    tot_cbm = db.Column(db.Float, nullable=False, default=0.0)
    prep_date = db.Column(db.Date, nullable=True)
    waybill_no = db.Column(db.String(100), nullable=True)
    pl_3pl = db.Column('3pl', db.String(100), nullable=True)
    ref_docs = db.Column(db.String(200), nullable=True)
    freight_category = db.Column(db.String(100), nullable=True)
    shipping_line = db.Column(db.String(100), nullable=True)
    container_no = db.Column(db.String(100), nullable=True)
    seal_no = db.Column(db.String(100), nullable=True)
    tot_boxes = db.Column(db.Integer, nullable=True)
    declared_value = db.Column(db.Float, nullable=True)
    freight_charge = db.Column(db.Float, nullable=True)
    length_width_height = db.Column(db.String(100), nullable=True)
    total_kg = db.Column(db.Float, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    port_of_destination = db.Column(db.String(100), nullable=True)
    order_date = db.Column(db.Date, nullable=True)
    booked_date = db.Column(db.Date, nullable=True)
    actual_pickup_date = db.Column(db.Date, nullable=True)
    etd = db.Column(db.Date, nullable=True)
    atd = db.Column(db.Date, nullable=True)
    eta = db.Column(db.Date, nullable=True)
    ata = db.Column(db.Date, nullable=True)
    actual_delivered_date = db.Column(db.Date, nullable=True)
    received_by = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    detailed_remarks = db.Column(db.Text, nullable=True)
    actual_delivery_leadtime = db.Column(db.Integer, nullable=True)
    received_date_to_pick_up_date = db.Column(db.Integer, nullable=True)
    year = db.Column(db.Integer, nullable=True)
    pick_up_month = db.Column(db.String(20), nullable=True)
    total_freight_charge = db.Column(db.Float, nullable=True)
    billing_date = db.Column(db.Date, nullable=True)
    billing_no = db.Column(db.String(100), nullable=True)
    billing_status = db.Column(db.String(50), nullable=True)
    team_lead = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('posting_date', 'branch_name', name='uix_lcl_summary_date_branch'),
    )

    def __repr__(self):
        return f'<LCLSummary {self.posting_date} - {self.branch_name}>'


class LCLDetail(db.Model):
    __bind_key__ = 'archive'
    __tablename__ = 'lcl_detail'

    id = db.Column(db.Integer, primary_key=True)
    sap_upload_date = db.Column(db.Date, nullable=False)
    isms_upload_date = db.Column(db.Date, nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)
    doc_type = db.Column(db.String(50), nullable=True)
    dr_number = db.Column(db.String(100), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=0)
    fr_whse = db.Column(db.String(100), nullable=True)
    to_whse = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=False)
    itr_so = db.Column(db.String(100), nullable=True)
    dr_it = db.Column(db.String(100), nullable=True)
    cbm = db.Column(db.Float, nullable=False, default=0.0)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('sap_upload_date', 'customer_name', 'serial_number', name='uix_lcl_detail_unique'),
    )

    def __repr__(self):
        return f'<LCLDetail {self.sap_upload_date} - {self.customer_name}>'
