"""
Archive Service Module

Handles archiving of old trip monitoring data from the main database to a separate archive database.
Archive logic: Calendar years - all records where year <= (current_year - 2)
"""
from datetime import datetime
from sqlalchemy import extract, Table
from flask import current_app
import json
import os

# Import main database and models
from models import db, Vehicle, Manpower, Data, Schedule, Trip, TripDetail, Cluster, User, Odo, DailyVehicleCount, Backload, TimeLog, LCLSummary, LCLDetail, trip_driver, trip_assistant

# Import archive models (they use __bind_key__ = 'archive')
from archive_models import (
    Vehicle as ArchiveVehicle,
    Manpower as ArchiveManpower,
    Data as ArchiveData,
    Schedule as ArchiveSchedule,
    Trip as ArchiveTrip,
    TripDetail as ArchiveTripDetail,
    Cluster as ArchiveCluster,
    User as ArchiveUser,
    Odo as ArchiveOdo,
    DailyVehicleCount as ArchiveDailyVehicleCount,
    Backload as ArchiveBackload,
    TimeLog as ArchiveTimeLog,
    LCLSummary as ArchiveLCLSummary,
    LCLDetail as ArchiveLCLDetail,
    trip_driver as archive_trip_driver,
    trip_assistant as archive_trip_assistant
)


def get_archive_cutoff_year():
    """Return the year cutoff for archiving (current_year - 2)"""
    current_year = datetime.now().year
    return current_year - 2


def init_archive_database():
    """Initialize archive database and create all tables if they don't exist"""
    archive_db_path = os.path.join(current_app.root_path, 'instance', 'trip_archive.db')

    # Create instance directory if it doesn't exist
    instance_dir = os.path.dirname(archive_db_path)
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

    # Create all tables including archive bind tables
    # This creates tables for all configured binds
    db.create_all()

    return archive_db_path


def identify_records_to_archive():
    """
    Identify all records to archive by calendar year.
    Returns dict with table names and counts of records to archive.
    """
    cutoff_year = get_archive_cutoff_year()

    counts = {
        'Data': Data.query.filter(extract('year', Data.due_date) <= cutoff_year).count(),
        'LCLDetail': LCLDetail.query.filter(extract('year', LCLDetail.sap_upload_date) <= cutoff_year).count(),
        'LCLSummary': LCLSummary.query.filter(extract('year', LCLSummary.posting_date) <= cutoff_year).count(),
        'Odo': Odo.query.filter(extract('year', Odo.datetime) <= cutoff_year).count(),
        'Schedule': Schedule.query.filter(extract('year', Schedule.delivery_schedule) <= cutoff_year).count(),
        'TimeLog': TimeLog.query.filter(extract('year', TimeLog.time_in) <= cutoff_year).count(),
        'DailyVehicleCount': DailyVehicleCount.query.filter(extract('year', DailyVehicleCount.date) <= cutoff_year).count(),
    }

    # For Trip, TripDetail, Vehicle, Manpower - they're archived through Schedule relationships
    schedules_to_archive = Schedule.query.filter(extract('year', Schedule.delivery_schedule) <= cutoff_year).all()
    trip_count = Trip.query.filter(Trip.schedule_id.in_([s.id for s in schedules_to_archive])).count()
    trip_detail_count = TripDetail.query.filter(TripDetail.trip_id.in_([t.id for t in Trip.query.filter(Trip.schedule_id.in_([s.id for s in schedules_to_archive])).all()])).count()

    counts['Trip'] = trip_count
    counts['TripDetail'] = trip_detail_count

    # Count unique vehicles and manpower referenced by archived trips
    trips_to_archive = Trip.query.filter(Trip.schedule_id.in_([s.id for s in schedules_to_archive])).all()
    vehicle_ids = set([t.vehicle_id for t in trips_to_archive])

    # Get driver and assistant IDs from association tables
    driver_ids = set()
    assistant_ids = set()
    for trip in trips_to_archive:
        for driver in trip.drivers:
            driver_ids.add(driver.id)
        for assistant in trip.assistants:
            assistant_ids.add(assistant.id)

    counts['Vehicle'] = len(vehicle_ids)
    counts['Manpower'] = len(driver_ids.union(assistant_ids))

    return counts


def archive_data_records():
    """Archive Data table records by due_date"""
    cutoff_year = get_archive_cutoff_year()
    records_to_archive = Data.query.filter(extract('year', Data.due_date) <= cutoff_year).all()

    archived_count = 0
    for record in records_to_archive:
        # Create archive record
        archive_record = ArchiveData(
            id=record.id,
            type=record.type,
            posting_date=record.posting_date,
            document_number=record.document_number,
            item_number=record.item_number,
            ordered_qty=record.ordered_qty,
            delivered_qty=record.delivered_qty,
            remaining_open_qty=record.remaining_open_qty,
            from_whse_code=record.from_whse_code,
            to_whse=record.to_whse,
            remarks=record.remarks,
            special_instructions=record.special_instructions,
            branch_name=record.branch_name,
            branch_name_v2=record.branch_name_v2,
            document_status=record.document_status,
            original_due_date=record.original_due_date,
            due_date=record.due_date,
            user_code=record.user_code,
            po_number=record.po_number,
            isms_so_number=record.isms_so_number,
            cbm=record.cbm,
            total_cbm=record.total_cbm,
            customer_vendor_code=record.customer_vendor_code,
            customer_vendor_name=record.customer_vendor_name,
            status=record.status,
            delivery_type=record.delivery_type,
            delete_remarks=record.delete_remarks,
            detailed_remarks=record.detailed_remarks
        )
        db.session.add(archive_record)
        archived_count += 1

    # Delete from main database
    for record in records_to_archive:
        db.session.delete(record)

    return archived_count


def archive_lcl_detail_records():
    """Archive LCLDetail records by sap_upload_date"""
    cutoff_year = get_archive_cutoff_year()
    records_to_archive = LCLDetail.query.filter(extract('year', LCLDetail.sap_upload_date) <= cutoff_year).all()

    archived_count = 0
    for record in records_to_archive:
        archive_record = ArchiveLCLDetail(
            id=record.id,
            sap_upload_date=record.sap_upload_date,
            isms_upload_date=record.isms_upload_date,
            delivery_date=record.delivery_date,
            doc_type=record.doc_type,
            dr_number=record.dr_number,
            customer_name=record.customer_name,
            qty=record.qty,
            fr_whse=record.fr_whse,
            to_whse=record.to_whse,
            model=record.model,
            serial_number=record.serial_number,
            itr_so=record.itr_so,
            dr_it=record.dr_it,
            cbm=record.cbm,
            email=record.email,
            created_at=record.created_at
        )
        db.session.add(archive_record)
        archived_count += 1

    # Delete from main database
    for record in records_to_archive:
        db.session.delete(record)

    return archived_count


def archive_lcl_summary_records():
    """Archive LCLSummary records by posting_date"""
    cutoff_year = get_archive_cutoff_year()
    records_to_archive = LCLSummary.query.filter(extract('year', LCLSummary.posting_date) <= cutoff_year).all()

    archived_count = 0
    for record in records_to_archive:
        archive_record = ArchiveLCLSummary(
            id=record.id,
            posting_date=record.posting_date,
            company=record.company,
            dept=record.dept,
            branch_name=record.branch_name,
            tot_qty=record.tot_qty,
            tot_cbm=record.tot_cbm,
            prep_date=record.prep_date,
            waybill_no=record.waybill_no,
            pl_3pl=record.pl_3pl,
            ref_docs=record.ref_docs,
            freight_category=record.freight_category,
            shipping_line=record.shipping_line,
            container_no=record.container_no,
            seal_no=record.seal_no,
            tot_boxes=record.tot_boxes,
            declared_value=record.declared_value,
            freight_charge=record.freight_charge,
            length_width_height=record.length_width_height,
            total_kg=record.total_kg,
            remarks=record.remarks,
            port_of_destination=record.port_of_destination,
            order_date=record.order_date,
            booked_date=record.booked_date,
            actual_pickup_date=record.actual_pickup_date,
            etd=record.etd,
            atd=record.atd,
            eta=record.eta,
            ata=record.ata,
            actual_delivered_date=record.actual_delivered_date,
            received_by=record.received_by,
            status=record.status,
            detailed_remarks=record.detailed_remarks,
            actual_delivery_leadtime=record.actual_delivery_leadtime,
            received_date_to_pick_up_date=record.received_date_to_pick_up_date,
            year=record.year,
            pick_up_month=record.pick_up_month,
            total_freight_charge=record.total_freight_charge,
            billing_date=record.billing_date,
            billing_no=record.billing_no,
            billing_status=record.billing_status,
            team_lead=record.team_lead,
            email=record.email,
            created_at=record.created_at,
            updated_at=record.updated_at
        )
        db.session.add(archive_record)
        archived_count += 1

    # Delete from main database
    for record in records_to_archive:
        db.session.delete(record)

    return archived_count


def archive_odo_records():
    """Archive Odo records by datetime"""
    cutoff_year = get_archive_cutoff_year()
    records_to_archive = Odo.query.filter(extract('year', Odo.datetime) <= cutoff_year).all()

    archived_count = 0
    for record in records_to_archive:
        archive_record = ArchiveOdo(
            id=record.id,
            plate_number=record.plate_number,
            odometer_reading=record.odometer_reading,
            status=record.status,
            datetime=record.datetime,
            created_by=record.created_by,
            litters=record.litters,
            amount=record.amount,
            price_per_litter=record.price_per_litter
        )
        db.session.add(archive_record)
        archived_count += 1

    # Delete from main database
    for record in records_to_archive:
        db.session.delete(record)

    return archived_count


def archive_daily_vehicle_count_records():
    """Archive DailyVehicleCount records by date"""
    cutoff_year = get_archive_cutoff_year()
    records_to_archive = DailyVehicleCount.query.filter(extract('year', DailyVehicleCount.date) <= cutoff_year).all()

    archived_count = 0
    for record in records_to_archive:
        archive_record = ArchiveDailyVehicleCount(
            id=record.id,
            date=record.date,
            qty=record.qty,
            created_at=record.created_at
        )
        db.session.add(archive_record)
        archived_count += 1

    # Delete from main database
    for record in records_to_archive:
        db.session.delete(record)

    return archived_count


def archive_time_log_records():
    """Archive TimeLog records by time_in + User references"""
    cutoff_year = get_archive_cutoff_year()
    records_to_archive = TimeLog.query.filter(extract('year', TimeLog.time_in) <= cutoff_year).all()

    archived_count = 0
    for record in records_to_archive:
        archive_record = ArchiveTimeLog(
            id=record.id,
            user_id=record.user_id,
            time_in=record.time_in,
            time_out=record.time_out,
            hrs_rendered=record.hrs_rendered,
            daily_rate=record.daily_rate,
            over_time=record.over_time,
            pay=record.pay,
            ot_pay=record.ot_pay,
            sched_start=record.sched_start,
            sched_end=record.sched_end,
            created_at=record.created_at
        )
        db.session.add(archive_record)
        archived_count += 1

    # Delete from main database
    for record in records_to_archive:
        db.session.delete(record)

    return archived_count


def archive_schedule_and_related_records():
    """
    Archive Schedule + Trip + TripDetail + trip_driver + trip_assistant + Vehicle + Manpower
    This is the most complex archival as it involves multiple related tables.
    """
    cutoff_year = get_archive_cutoff_year()
    schedules_to_archive = Schedule.query.filter(extract('year', Schedule.delivery_schedule) <= cutoff_year).all()

    archived_counts = {
        'Schedule': 0,
        'Trip': 0,
        'TripDetail': 0,
        'Vehicle': 0,
        'Manpower': 0
    }

    vehicle_ids_seen = set()
    manpower_ids_seen = set()

    for schedule in schedules_to_archive:
        # Archive Schedule
        archive_schedule = ArchiveSchedule(
            id=schedule.id,
            delivery_schedule=schedule.delivery_schedule,
            plate_number=schedule.plate_number,
            capacity=schedule.capacity,
            actual=schedule.actual
        )
        db.session.add(archive_schedule)
        archived_counts['Schedule'] += 1

        # Get related Trips
        trips = Trip.query.filter_by(schedule_id=schedule.id).all()

        for trip in trips:
            # Archive Vehicle if not already archived
            if trip.vehicle_id and trip.vehicle_id not in vehicle_ids_seen:
                vehicle = Vehicle.query.get(trip.vehicle_id)
                if vehicle:
                    archive_vehicle = ArchiveVehicle(
                        id=vehicle.id,
                        plate_number=vehicle.plate_number,
                        status=vehicle.status,
                        capacity=vehicle.capacity,
                        dept=vehicle.dept
                    )
                    db.session.add(archive_vehicle)
                    vehicle_ids_seen.add(vehicle.id)
                    archived_counts['Vehicle'] += 1

            # Archive Trip (without many-to-many relationships first)
            archive_trip = ArchiveTrip(
                id=trip.id,
                schedule_id=trip.schedule_id,
                trip_number=trip.trip_number,
                vehicle_id=trip.vehicle_id,
                total_cbm=trip.total_cbm
            )
            db.session.add(archive_trip)
            archived_counts['Trip'] += 1

            # Archive drivers (manpower) through association table
            for driver in trip.drivers:
                if driver.id not in manpower_ids_seen:
                    archive_manpower = ArchiveManpower(
                        id=driver.id,
                        name=driver.name,
                        role=driver.role,
                        user_id=driver.user_id
                    )
                    db.session.add(archive_manpower)
                    manpower_ids_seen.add(driver.id)
                    archived_counts['Manpower'] += 1

                # Insert into archive association table
                db.session.execute(
                    archive_trip_driver.insert().values(trip_id=trip.id, manpower_id=driver.id)
                )

            # Archive assistants (manpower) through association table
            for assistant in trip.assistants:
                if assistant.id not in manpower_ids_seen:
                    archive_manpower = ArchiveManpower(
                        id=assistant.id,
                        name=assistant.name,
                        role=assistant.role,
                        user_id=assistant.user_id
                    )
                    db.session.add(archive_manpower)
                    manpower_ids_seen.add(assistant.id)
                    archived_counts['Manpower'] += 1

                # Insert into archive association table
                db.session.execute(
                    archive_trip_assistant.insert().values(trip_id=trip.id, manpower_id=assistant.id)
                )

            # Archive TripDetails
            trip_details = TripDetail.query.filter_by(trip_id=trip.id).all()
            for detail in trip_details:
                archive_detail = ArchiveTripDetail(
                    id=detail.id,
                    document_number=detail.document_number,
                    branch_name_v2=detail.branch_name_v2,
                    data_ids=detail.data_ids,
                    area=detail.area,
                    total_cbm=detail.total_cbm,
                    total_ordered_qty=detail.total_ordered_qty,
                    total_delivered_qty=detail.total_delivered_qty,
                    backload_qty=detail.backload_qty,
                    trip_id=detail.trip_id,
                    status=detail.status,
                    cancel_reason=detail.cancel_reason,
                    cause_department=detail.cause_department,
                    arrive=detail.arrive,
                    departure=detail.departure,
                    reason=detail.reason,
                    delivery_type=detail.delivery_type,
                    delivery_order=detail.delivery_order,
                    original_due_date=detail.original_due_date
                )
                db.session.add(archive_detail)
                archived_counts['TripDetail'] += 1

    # Delete from main database (in correct order due to foreign keys)
    # First delete TripDetails
    for schedule in schedules_to_archive:
        trips = Trip.query.filter_by(schedule_id=schedule.id).all()
        for trip in trips:
            TripDetail.query.filter_by(trip_id=trip.id).delete()

    # Then delete Trips (association table entries will be deleted by cascade)
    for schedule in schedules_to_archive:
        Trip.query.filter_by(schedule_id=schedule.id).delete()

    # Finally delete Schedules
    for schedule in schedules_to_archive:
        db.session.delete(schedule)

    return archived_counts


def execute_archive():
    """
    Main orchestration function to execute the archive operation.
    - Begins transaction on both databases
    - Copies records to archive database
    - Deletes from main database
    - Commits both transactions
    - Rolls back both on any error

    Returns: dict with counts, status, and execution details
    """
    start_time = datetime.now()
    result = {
        'success': False,
        'cutoff_year': get_archive_cutoff_year(),
        'tables_affected': {},
        'total_records_archived': 0,
        'error': None,
        'execution_time_seconds': 0
    }

    # Initialize archive database if needed
    try:
        init_archive_database()
    except Exception as e:
        result['error'] = f"Failed to initialize archive database: {str(e)}"
        return result

    # Begin transactions
    try:
        # Archive each table type
        data_count = archive_data_records()
        result['tables_affected']['Data'] = data_count
        result['total_records_archived'] += data_count

        lcl_detail_count = archive_lcl_detail_records()
        result['tables_affected']['LCLDetail'] = lcl_detail_count
        result['total_records_archived'] += lcl_detail_count

        lcl_summary_count = archive_lcl_summary_records()
        result['tables_affected']['LCLSummary'] = lcl_summary_count
        result['total_records_archived'] += lcl_summary_count

        odo_count = archive_odo_records()
        result['tables_affected']['Odo'] = odo_count
        result['total_records_archived'] += odo_count

        daily_vehicle_count_count = archive_daily_vehicle_count_records()
        result['tables_affected']['DailyVehicleCount'] = daily_vehicle_count_count
        result['total_records_archived'] += daily_vehicle_count_count

        time_log_count = archive_time_log_records()
        result['tables_affected']['TimeLog'] = time_log_count
        result['total_records_archived'] += time_log_count

        schedule_counts = archive_schedule_and_related_records()
        for table, count in schedule_counts.items():
            if count > 0:
                result['tables_affected'][table] = count
                result['total_records_archived'] += count

        # Commit both transactions (main and archive databases)
        db.session.commit()

        result['success'] = True

    except Exception as e:
        # Rollback both transactions on error (main and archive databases)
        db.session.rollback()
        result['error'] = str(e)

    # Calculate execution time
    end_time = datetime.now()
    result['execution_time_seconds'] = (end_time - start_time).total_seconds()

    return result
