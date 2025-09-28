import copy
import csv
from io import StringIO
from flask import Blueprint, jsonify, render_template, request, g, make_response
from .simulation import PowerPlantSimulator
from .models import PlantReport
from .auth import login_required, role_required

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
    # Export the latest 1000 rows (or fewer) as CSV
    rows = PlantReport.query.order_by(PlantReport.timestamp.desc()).limit(1000).all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['timestamp_utc', 'module_name', 'status', 'power_output_mw', 'temperature_c'])
    for r in rows:
        writer.writerow([
            r.timestamp.strftime('%Y-%m-%d %H:%M:%S') if r.timestamp else '',
            r.module_name,
            r.status,
            f"{r.power_output_mw:.2f}" if r.power_output_mw is not None else '',
            f"{r.temperature_c:.2f}" if r.temperature_c is not None else '',
        ])
    csv_data = output.getvalue()
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=plant_reports.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response