from flask import Flask, render_template, request, jsonify
import redis
import json
import uuid
from datetime import datetime
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Gerson'

redis_client = redis.Redis(
    host='redis-19444.c336.samerica-east1-1.gce.redns.redis-cloud.com',
    port=19444,
    decode_responses=True,
    username="default",
    password="Em1iQAulxiTFo9NvbzCiIsF4cfbtiVPO",
)

TASKS_KEY = "todo_tasks"

def get_tasks():
    try:
        tasks_json = redis_client.get(TASKS_KEY)
        return json.loads(tasks_json) if tasks_json else []
    except Exception as e:
        print(f'Erro ao buscar tarefas no Redis: {e}')
        return []

def save_tasks(tasks):
    try:
        redis_client.set(TASKS_KEY, json.dumps(tasks))
        return True
    except Exception as e:
        print(f'Erro ao salvar tarefas no Redis: {e}')
        return False

def get_pending_count():
    tasks = get_tasks()
    return sum(not task['completed'] for task in tasks)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    try:
        tasks = get_tasks()
        tasks.sort(key=lambda t: t.get('order', 0))
        return jsonify({
            'success': True,
            'tasks': tasks,
            'pending_count': get_pending_count()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'success': False, 'error': 'Texto da tarefa é obrigatório'}), 400

        tasks = get_tasks()
        new_task = {
            'id': str(uuid.uuid4()),
            'text': text,
            'completed': False,
            'order': len(tasks),
            'created_at': datetime.now().isoformat()
        }
        tasks.append(new_task)

        if save_tasks(tasks):
            return jsonify({'success': True, 'task': new_task})
        else:
            return jsonify({'success': False, 'error': 'Erro ao salvar tarefa'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    try:
        tasks = [t for t in get_tasks() if t['id'] != task_id]
        if save_tasks(tasks):
            return jsonify({'success': True, 'message': 'Tarefa removida com sucesso'})
        else:
            return jsonify({'success': False, 'error': 'Erro ao remover tarefa'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/toggle', methods=['PUT'])
def api_toggle_task(task_id):
    try:
        tasks = get_tasks()
        for t in tasks:
            if t['id'] == task_id:
                t['completed'] = not t['completed']
                break
        if save_tasks(tasks):
            return jsonify({'success': True, 'message': 'Status da tarefa atualizado'})
        else:
            return jsonify({'success': False, 'error': 'Erro ao atualizar tarefa'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/reorder', methods=['PUT'])
def api_reorder_tasks():
    try:
        task_ids = request.get_json().get('task_ids', [])
        tasks = get_tasks()
        task_map = {t['id']: t for t in tasks}

        reordered = []
        for i, tid in enumerate(task_ids):
            if tid in task_map:
                task_map[tid]['order'] = i
                reordered.append(task_map[tid])

        if save_tasks(reordered):
            return jsonify({'success': True, 'message': 'Ordem das tarefas atualizada'})
        else:
            return jsonify({'success': False, 'error': 'Erro ao reordenar tarefas'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def find_free_port(start=5001, end=5010):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                return port
    return None

if __name__ == '__main__':
    port = find_free_port()
    if port is None:
        print("Não há portas livres entre 5001 e 5010")
    else:
        print(f"Rodando na porta {port}")
        app.run(debug=True, port=port)
