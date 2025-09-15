import random
from . import db  # Import the db instance
from .models import PlantReport 

class PowerPlantSimulator:
    def __init__(self):
        """Initializes the plant state with the full data set."""
        self.state = {
            "Operation Module": {
                'Reactor 1': {'status': 'Online', 'power_output_mw': 950, 'temp_c': 320},
                'Reactor 2': {'status': 'Online', 'power_output_mw': 945, 'temp_c': 318},
                'Reactor 3': {'status': 'Standby', 'power_output_mw': 0, 'temp_c': 45},
                'Turbine 1': {'status': 'Online', 'rpm': 1800},
                'Turbine 2': {'status': 'Online', 'rpm': 1800},
                'Boiler 1': {'status': 'Online', 'pressure_psi': 2200, 'temp_c': 350},
                'Boiler 2': {'status': 'Online', 'pressure_psi': 2205, 'temp_c': 352},
                'Cooling Tower 1': {'status': 'Active', 'flow_rate_gpm': 500000, 'water_temp_c': 28},
                'Cooling Tower 2': {'status': 'Active', 'flow_rate_gpm': 500000, 'water_temp_c': 29},
            },
            "Safety Module": {
                'Safety Gen 1': {'status': 'Standby', 'fuel_level': '100%', 'last_test': '2025-08-25'},
                'Safety Gen 2': {'status': 'Standby', 'fuel_level': '100%', 'last_test': '2025-08-25'},
                'Fire Safety System': {'status': 'Active', 'pressure': 'Normal', 'alarms': 0},
                'Cooling Safety Backup': {'status': 'Ready', 'reservoir_level': 'Full'},
            },
            "Environmental & Compliance Module": {
                'Emission Control Unit 1': {'status': 'Active', 'filter_status': 'OK'},
                'Emission Control Unit 2': {'status': 'Active', 'filter_status': 'OK'},
                'Waste Treatment Plant': {'status': 'Operational', 'processing_load': '75%'},
                'Water Recycling Unit': {'status': 'Operational', 'flow_rate': 'High'},
            }
        }

    def update(self):
        """
        The core simulation loop. Updates values for operational modules
        while skipping specified modules and categories.
        """
        # A set of specific modules to exclude from any updates
        excluded_modules = {'Fire Safety System', 'Cooling Safety Backup'}

        for category, modules in self.state.items():
            # RULE: Skip the entire Environmental & Compliance Module
            if category == "Environmental & Compliance Module":
                continue

            for name, data in modules.items():
                # RULE: Skip the specific safety modules
                if name in excluded_modules:
                    continue

                status = data.get('status', 'Offline')

                # Apply fluctuations only to modules that are 'Online' or 'Active'
                if status in ['Online', 'Active']:
                    if 'power_output_mw' in data:
                        data['power_output_mw'] = max(0, data['power_output_mw'] + random.uniform(-5, 5))
                    if 'temp_c' in data:
                        data['temp_c'] += random.uniform(-0.5, 0.5)
                    if 'rpm' in data:
                        data['rpm'] += random.randint(-5, 5)
                    if 'pressure_psi' in data:
                        data['pressure_psi'] += random.uniform(-1, 1)
                    if 'flow_rate_gpm' in data:
                        data['flow_rate_gpm'] += random.randint(-100, 100)
                    if 'water_temp_c' in data:
                        data['water_temp_c'] += random.uniform(-0.1, 0.1)

                # Handle gradual shutdown logic
                elif status == 'shutting_down':
                    power = data.get('power_output_mw', 0)
                    if power > 0:
                        data['power_output_mw'] = max(0, power * 0.8 - random.uniform(0, 20))
                    else:
                        data['status'] = 'Offline'
                        if 'temp_c' in data: data['temp_c'] = 25
                        if 'rpm' in data: data['rpm'] = 0

                # Handle gradual startup logic
                elif status == 'starting_up':
                    power = data.get('power_output_mw', 0)
                    if power < 800:
                        data['power_output_mw'] += random.uniform(50, 80)
                    else:
                        data['status'] = 'Online'
                
                new_report = PlantReport(
                    module_name=name,
                    status=data.get('status'),
                    power_output_mw=data.get('power_output_mw'),
                    temperature_c=data.get('temp_c')
                )
                db.session.add(new_report)


        db.session.commit()

    def handle_action(self, module_id, action):
        """Receives an action from the user and changes the module's target state."""
        for category, modules in self.state.items():
            for name, data in modules.items():
                if name.lower().replace(' ', '_') == module_id:
                    if action == 'stop' and data['status'] in ['Online', 'Active']:
                        # For modules with power, start a shutdown. For others, just stop them.
                        if 'power_output_mw' in data:
                            data['status'] = 'shutting_down'
                        else:
                            data['status'] = 'Offline'
                        return f"{name} is stopping."
                    if action == 'start' and data['status'] in ['Offline', 'Standby']:
                        if 'power_output_mw' in data:
                            data['status'] = 'starting_up'
                        else:
                            data['status'] = 'Active' # or 'Online' for non-power modules
                        return f"{name} is starting."
        return f"Action '{action}' on '{module_id}' could not be completed."