import copy
from flask import Blueprint, jsonify, render_template, request
from .simulation import PowerPlantSimulator
from .models import PlantReport

bp = Blueprint('dashboard', __name__)

simulator = PowerPlantSimulator()

@bp.route('/api/plant_data')
def get_plant_data_api():
    simulator.update() # Run one simulation step
    return jsonify(simulator.state)

@bp.route('/')
@bp.route('/nuclear_dashboard')
def nuclear_dashboard():
    return render_template('nuclear_dashboard.html', categorized_modules=copy.deepcopy(simulator.state))

@bp.route('/module_action', methods=['POST'])
def module_action():
    data = request.get_json()
    module_id = data.get('module_id')
    action = data.get('action')
    
    # Tell the simulator to handle the user's action
    message = simulator.handle_action(module_id, action)
    
    return jsonify({"status": "success", "message": message})

@bp.route('/reports')
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