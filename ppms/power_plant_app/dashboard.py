import copy
import csv
from io import StringIO
from flask import Blueprint, jsonify, render_template, request, g, make_response, redirect, url_for, flash, Response
from .simulation import PowerPlantSimulator
from .models import PlantReport
from .auth import login_required, role_required
from .models import User, MaintenanceSchedule, Notification
from . import db 
from datetime import datetime


bp = Blueprint('dashboard', __name__)

simulator = PowerPlantSimulator()

@bp.route('/api/plant_data')
@login_required
def get_plant_data_api():
    simulator.update() # Run one simulation step
    return jsonify(simulator.state)

@bp.route('/')
@bp.route('/nuclear_dashboard')
@login_required
def nuclear_dashboard():
    full_state = copy.deepcopy(simulator.state)
    role = getattr(g, 'user', None).role if getattr(g, 'user', None) else 'operator'

    def filter_by_role(state, role_name):
        if role_name == 'admin':
            return state
        filtered = {}
        for category, modules in state.items():
            if role_name == 'operator' and category != 'Operation Module':
                continue
            if role_name == 'safety' and category != 'Safety Module':
                continue
            if role_name == 'environment' and category != 'Environmental & Compliance Module':
                continue
            filtered[category] = modules
        return filtered

    categorized = filter_by_role(full_state, role)
    return render_template('nuclear_dashboard.html', categorized_modules=categorized)

@bp.route('/module_action', methods=['POST'])
@login_required
def module_action():
    data = request.get_json()
    module_id = data.get('module_id')
    action = data.get('action')
    
    # Tell the simulator to handle the user's action
    message = simulator.handle_action(module_id, action)
    
    return jsonify({"status": "success", "message": message})

@bp.route('/reports')
@login_required
def reports():
    all_reports = PlantReport.query.order_by(PlantReport.timestamp.desc()).limit(100).all()
    grouped_reports = {}
    
    all_reports = PlantReport.query.filter(         #only reactor
        PlantReport.module_name.like('%Reactor%')
    ).order_by(PlantReport.timestamp.desc()).limit(500).all()
    
    for report in all_reports:
        if report.module_name not in grouped_reports:
            grouped_reports[report.module_name] = []
        grouped_reports[report.module_name].append(report)

    return render_template('reports.html', grouped_reports=grouped_reports)


@bp.route('/reports/export.csv')
@login_required
def export_reports_csv():
    reports = PlantReport.query.filter(
        PlantReport.module_name.like('%Reactor%')
    ).order_by(PlantReport.timestamp.asc()).all()

    si = StringIO()
    cw = csv.writer(si)

    cw.writerow(['Timestamp (UTC)', 'Module Name', 'Status', 'Power (MW)', 'Temp (°C)'])

    for report in reports:
        cw.writerow([
            report.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            report.module_name,
            report.status,
            report.power_output_mw,
            report.temperature_c
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=reactor_reports.csv"})

@bp.route('/notifications')
@login_required
def notifications():
    # Mark all notifications as read when the user visits this page
    all_notifs = Notification.query.order_by(Notification.timestamp.desc()).all()
    for notif in all_notifs:
        if g.user not in notif.read_by_users:
            notif.read_by_users.append(g.user)
    db.session.commit()
    
    return render_template('notifications.html', notifications=all_notifs)

@bp.app_context_processor
def inject_notifications():
    if g.user:
        unread_count = db.session.query(Notification).filter(~Notification.read_by_users.any(id=g.user.id)).count()
        return {'unread_notification_count': unread_count}
    return {'unread_notification_count': 0}

@bp.route('/schedule_maintenance', methods=['GET', 'POST'])
@login_required
@role_required('safety')
def schedule_maintenance():
    if request.method == 'POST':
        module_name = request.form.get('module_name')
        schedule_str = request.form.get('schedule_datetime')
        
        try:
            schedule_dt = datetime.strptime(schedule_str, '%Y-%m-%dT%H:%M')
            
            # 1. Create the maintenance schedule entry
            new_schedule = MaintenanceSchedule(
                module_name=module_name,
                scheduled_for_datetime=schedule_dt,
                scheduled_by_username=g.user.username
            )
            db.session.add(new_schedule)
            
            # 2. Create a notification for everyone
            notif_message = f"Maintenance for '{module_name}' scheduled for {schedule_dt.strftime('%Y-%m-%d %H:%M')} by {g.user.username}."
            new_notification = Notification(message=notif_message)
            db.session.add(new_notification)
            
            db.session.commit()
            flash('Maintenance scheduled successfully and notification sent.', 'success')
            return redirect(url_for('dashboard.nuclear_dashboard'))
            
        except ValueError:
            flash('Invalid date/time format.', 'error')

    # For the GET request, get a list of all module names for the dropdown
    all_modules = []
    for category in simulator.state.values():
        all_modules.extend(category.keys())
        
    return render_template('schedule_maintenance.html', modules=sorted(all_modules))