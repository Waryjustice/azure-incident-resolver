from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import deque
from threading import Thread
import time

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage for incidents and metrics
incidents = deque(maxlen=100)
logs = deque(maxlen=500)
agent_status = {
    'detection': {'status': 'idle', 'last_check': None, 'incidents_detected': 0},
    'diagnosis': {'status': 'idle', 'last_check': None, 'analyses_completed': 0},
    'resolution': {'status': 'idle', 'last_check': None, 'issues_resolved': 0},
    'communication': {'status': 'idle', 'last_check': None, 'notifications_sent': 0}
}
metrics = {
    'avg_mttr': 300,
    'incidents_this_week': 0,
    'resolution_rate': 85,
    'false_positive_rate': 5
}


@app.route('/')
def index():
    """Render the dashboard home page."""
    return render_template('index.html')


@app.route('/api/incidents')
def get_incidents():
    """Get all incidents."""
    return jsonify(list(incidents))


@app.route('/api/agents/status')
def get_agent_status():
    """Get current status of all agents."""
    return jsonify(agent_status)


@app.route('/api/metrics')
def get_metrics():
    """Get system metrics."""
    return jsonify(metrics)


@app.route('/api/logs')
def get_logs():
    """Get all logs."""
    return jsonify(list(logs))


def add_log(agent_name, message):
    """Add a log entry and broadcast to clients."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'agent': agent_name,
        'message': message
    }
    logs.append(log_entry)
    socketio.emit('new_log', log_entry)


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connection_response', {'data': 'Connected to dashboard'})
    emit_current_state()


def emit_current_state():
    """Emit current state to all connected clients."""
    socketio.emit('agent_status', agent_status)
    socketio.emit('incidents_update', list(incidents))
    socketio.emit('metrics_update', metrics)
    socketio.emit('logs_update', list(logs))


@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client."""
    emit_current_state()


def add_incident(incident_data):
    """Add a new incident to the dashboard."""
    incident = {
        'id': len(incidents) + 1,
        'timestamp': datetime.utcnow().isoformat(),
        'title': incident_data.get('title', 'Unknown Incident'),
        'severity': incident_data.get('severity', 'medium'),
        'status': incident_data.get('status', 'detecting'),
        'description': incident_data.get('description', ''),
        'affected_resource': incident_data.get('affected_resource', ''),
        'mttr': 0,
        'timeline': [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'agent': 'detection',
                'action': 'Incident detected',
                'icon': '🔍'
            }
        ]
    }
    incidents.append(incident)
    socketio.emit('new_incident', incident)
    return incident


def update_agent_status(agent_name, status, data=None):
    """Update agent status and broadcast to clients."""
    if agent_name in agent_status:
        agent_status[agent_name]['status'] = status
        agent_status[agent_name]['last_check'] = datetime.utcnow().isoformat()
        if data:
            agent_status[agent_name].update(data)
        socketio.emit('agent_status_update', {agent_name: agent_status[agent_name]})


def update_incident_status(incident_id, status, mttr=None, action=None):
    """Update incident status and add timeline entry."""
    agent_map = {
        'diagnosing': ('diagnosis', '🧠', 'Running root cause analysis'),
        'resolving': ('resolution', '🔧', 'Executing automated fixes'),
        'communicating': ('communication', '💬', 'Sending notifications and post-mortem'),
        'resolved': ('communication', '✅', 'Incident resolved')
    }
    
    for incident in incidents:
        if incident['id'] == incident_id:
            incident['status'] = status
            if mttr is not None:
                incident['mttr'] = mttr
            
            if status in agent_map:
                agent_name, icon, default_action = agent_map[status]
                incident['timeline'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'agent': agent_name,
                    'action': action or default_action,
                    'icon': icon
                })
            
            socketio.emit('incident_update', incident)
            break


def update_metrics(new_metrics):
    """Update system metrics."""
    metrics.update(new_metrics)
    socketio.emit('metrics_update', metrics)


def create_demo_scenarios():
    """Define available demo scenarios."""
    return {
        'database-spike': {
            'title': 'Database Connection Pool Exhausted',
            'severity': 'critical',
            'description': 'Connection pool at 95% capacity, API requests timing out',
            'affected_resource': 'prod-db-01',
            'duration': 8
        },
        'memory-leak': {
            'title': 'Memory Leak Detected',
            'severity': 'high',
            'description': 'Service memory usage at 95%, OOM imminent',
            'affected_resource': 'prod-api-service-03',
            'duration': 6
        },
        'rate-limit': {
            'title': 'API Rate Limit Breach',
            'severity': 'high',
            'description': 'Third-party API throttling, 42% error rate',
            'affected_resource': 'payment-api-gateway',
            'duration': 10
        },
        'failed-deployment': {
            'title': 'Failed Deployment v2.4.1',
            'severity': 'critical',
            'description': 'New deployment causes 15% error rate, 25K failed requests',
            'affected_resource': 'api-prod-cluster',
            'duration': 8
        },
        'disk-space': {
            'title': 'Disk Space Critical',
            'severity': 'critical',
            'description': 'Disk 95% full, logs consuming 450GB, only 2GB free',
            'affected_resource': 'prod-disk-001',
            'duration': 7
        },
        'ssl-expiring': {
            'title': 'SSL Certificate Expiring',
            'severity': 'high',
            'description': 'SSL cert expires in 5 days for api.prod.azureincidents.com',
            'affected_resource': 'cert-prod-01',
            'duration': 9
        },
        'cpu-spike': {
            'title': 'Sustained High CPU Load',
            'severity': 'critical',
            'description': 'CPU 98%, response times 8500ms, 15K users affected',
            'affected_resource': 'aks-prod-api',
            'duration': 8
        },
        'database-deadlock': {
            'title': 'Database Deadlock',
            'severity': 'critical',
            'description': '42 transactions deadlocked, payment processing halted',
            'affected_resource': 'db-prod-payment',
            'duration': 5
        },
        'cache-down': {
            'title': 'Redis Cache Down',
            'severity': 'critical',
            'description': '100% cache miss, API latency 3500ms, 12K users affected',
            'affected_resource': 'redis-prod-01',
            'duration': 7
        },
        'slow-query': {
            'title': 'Slow Database Query',
            'severity': 'critical',
            'description': 'Query 35s (normally 0.8s), missing index on 50M row table',
            'affected_resource': 'db-prod-analytics',
            'duration': 9
        },
        'new-feature-bug': {
            'title': 'New Feature Bug - No Rollback Available',
            'severity': 'critical',
            'description': 'User Dashboard v2.0 NullPointerException, 25K failed requests, no rollback',
            'affected_resource': 'user-dashboard-v2',
            'duration': 10
        }
    }


@app.route('/api/demo/scenarios')
def get_demo_scenarios():
    """Get available demo scenarios."""
    scenarios = create_demo_scenarios()
    return jsonify({key: {k: v for k, v in value.items() if k != 'duration'} 
                   for key, value in scenarios.items()})


@app.route('/api/demo/trigger-incident/<scenario_type>', methods=['POST'])
def trigger_demo_incident(scenario_type):
    """Trigger a demo incident for testing."""
    try:
        scenarios = create_demo_scenarios()
        
        if scenario_type not in scenarios:
            return jsonify({'error': f'Invalid scenario type: {scenario_type}. Valid types: {list(scenarios.keys())}'}), 400
        
        scenario = scenarios[scenario_type]
        incident = add_incident({
            'title': scenario['title'],
            'severity': scenario['severity'],
            'description': scenario['description'],
            'affected_resource': scenario['affected_resource']
        })
        
        def simulate_workflow():
            try:
                duration = scenario['duration']
                
                # Detection phase
                add_log('Detection', f'Starting real-time anomaly detection for {scenario["affected_resource"]}...')
                update_agent_status('detection', 'working')
                time.sleep(1)
                add_log('Detection', f'✓ Detected {scenario["title"]}')
                add_log('Detection', f'Severity: {scenario["severity"].upper()} | Resource: {scenario["affected_resource"]}')
                
                # Special handling for new feature bug scenario
                is_new_feature_bug = scenario_type == 'new-feature-bug'
                if is_new_feature_bug:
                    add_log('Detection', '⚠️  NOTE: New feature deployment - rollback NOT available')
                
                update_agent_status('detection', 'idle', {'incidents_detected': agent_status['detection']['incidents_detected'] + 1})
                update_incident_status(incident['id'], 'diagnosing', int(duration * 0.15))
                
                # Diagnosis phase
                add_log('Diagnosis', 'Starting root cause analysis...')
                add_log('Diagnosis', 'Correlating logs and metrics across 12 systems...')
                update_agent_status('diagnosis', 'working')
                time.sleep(2)
                add_log('Diagnosis', '✓ Root cause identified with 87% confidence')
                
                if is_new_feature_bug:
                    add_log('Diagnosis', 'Root cause: NullPointerException in UserProfileComponent.js line 42')
                    add_log('Diagnosis', 'Issue: Missing null check before accessing userData.firstName')
                else:
                    add_log('Diagnosis', 'Probable cause: Connection pool exhaustion due to leak in connection manager')
                
                update_agent_status('diagnosis', 'idle', {'analyses_completed': agent_status['diagnosis']['analyses_completed'] + 1})
                update_incident_status(incident['id'], 'resolving', int(duration * 0.4))
                
                # Resolution phase
                add_log('Resolution', 'Requesting fix from GitHub Copilot Agent Mode...')
                
                if is_new_feature_bug:
                    add_log('Resolution', '⚠️  Rollback NOT available (new feature v2.0 has no previous version)')
                    add_log('Resolution', 'Generating null-safe code fix via GitHub Copilot...')
                    time.sleep(1)
                    add_log('Resolution', '✓ Copilot generated null safety fix with 96% code quality')
                    add_log('Resolution', 'Generated: const displayName = (userData && userData.firstName) ? userData.firstName + \' \' + userData.lastName : \'User Profile\';')
                    add_log('Resolution', 'Creating automated PR for UserProfileComponent.js...')
                    time.sleep(1)
                    add_log('Resolution', '✓ PR created: https://github.com/azure-incident-resolver/pull/2847')
                    add_log('Resolution', 'Running 847 automated tests...')
                    add_log('Resolution', '✓ All tests passed - 98.2% code coverage maintained')
                    add_log('Resolution', 'Deploying fix to production...')
                else:
                    add_log('Resolution', 'Generating code for connection pooling optimization...')
                    time.sleep(2)
                    add_log('Resolution', '✓ Copilot generated fix with 92% code quality')
                    add_log('Resolution', 'PR created: https://github.com/azure-incident-resolver/pull/1247')
                    add_log('Resolution', 'Auto-scaling database from S1 → S3 tier...')
                    add_log('Resolution', '✓ Database scaled successfully')
                
                update_agent_status('resolution', 'working')
                time.sleep(2)
                update_agent_status('resolution', 'idle', {'issues_resolved': agent_status['resolution']['issues_resolved'] + 1})
                update_incident_status(incident['id'], 'communicating', int(duration * 0.7))
                
                # Communication phase
                add_log('Communication', 'Sending Teams notification to General channel...')
                update_agent_status('communication', 'working')
                time.sleep(1)
                add_log('Communication', '✓ Teams notification sent to General channel')
                add_log('Communication', 'Generating post-mortem report...')
                
                if is_new_feature_bug:
                    add_log('Communication', '✓ Resolution: Copilot-generated code fix deployed')
                    add_log('Communication', '✓ User Dashboard v2.0 now has null safety checks')
                else:
                    add_log('Communication', '✓ Post-mortem available at https://kb.internal/incidents/INC-2026-0451')
                add_log('Communication', f'✓ Incident resolved in {duration} seconds | 89% reduction vs manual MTTR')
                update_agent_status('communication', 'idle', {'notifications_sent': agent_status['communication']['notifications_sent'] + 1})
                update_incident_status(incident['id'], 'resolved', duration)
                
                # Update metrics
                new_avg = int((metrics['avg_mttr'] + duration) / 2)
                update_metrics({
                    'incidents_this_week': metrics['incidents_this_week'] + 1,
                    'avg_mttr': new_avg
                })
            except Exception as e:
                print(f"Error in workflow simulation: {str(e)}")
                add_log('Error', f'Workflow failed: {str(e)}')
                update_incident_status(incident['id'], 'error')
        
        thread = Thread(target=simulate_workflow)
        thread.daemon = True
        thread.start()
        
        return jsonify(incident), 201
    except Exception as e:
        print(f"Error triggering incident: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
