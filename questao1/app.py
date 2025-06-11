from flask import Flask, render_template, request, jsonify
import json
import uuid
from datetime import datetime
import redis
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-heredddddd'

load_dotenv()

r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    decode_responses=True,
    username=os.getenv('REDIS_USERNAME'),
    password=os.getenv('REDIS_PASSWORD'),
)

success = r.set('foo', 'bar')
result = r.get('foo')
print(result)

redis_client = r

TASKS_KEY = "todo_tasks"

def get_tasks():
    try:
        dados_tarefas = redis_client.get(TASKS_KEY)
        if dados_tarefas:
            return json.loads(dados_tarefas)
    except Exception as ex:
        print('Erro ao buscar tarefas, {ex}')
    return []

def save_tasks(tasks):
    try:
        redis_client.set(TASKS_KEY, json.dumps(tasks))
        return True
    except Exception as ex:
        print('Erro ao salvaras tarefas, {ex}')
        return False

def get_pending_count():
    tasks = get_tasks()
    return len([task for task in tasks if not task['completed']])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    try:
        tasks = get_tasks()
        tasks.sort(key=lambda x: x.get('order', 0))
        pending_count = get_pending_count()
        return jsonify({
            'success': True,
            'tasks': tasks,
            'pending_count': pending_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Texto da tarefa é obrigatório'
            }), 400
        
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
            return jsonify({
                'success': True,
                'task': new_task
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao salvar tarefa - Redis não implementado'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    try:
        tasks = get_tasks()
        tasks = [task for task in tasks if task['id'] != task_id]
        
        if save_tasks(tasks):
            return jsonify({
                'success': True,
                'message': 'Tarefa removida com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao remover tarefa - Redis não implementado'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/toggle', methods=['PUT'])
def api_toggle_task(task_id):
    try:
        tasks = get_tasks()
        
        for task in tasks:
            if task['id'] == task_id:
                task['completed'] = not task['completed']
                break
        
        if save_tasks(tasks):
            return jsonify({
                'success': True,
                'message': 'Status da tarefa atualizado'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao atualizar tarefa - Redis não implementado'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/reorder', methods=['PUT'])
def api_reorder_tasks():
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        tasks = get_tasks()
        
        task_map = {task['id']: task for task in tasks}
        
        reordered_tasks = []
        for i, task_id in enumerate(task_ids):
            if task_id in task_map:
                task = task_map[task_id]
                task['order'] = i
                reordered_tasks.append(task)
        
        if save_tasks(reordered_tasks):
            return jsonify({
                'success': True,
                'message': 'Ordem das tarefas atualizada'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao reordenar tarefas - Redis não implementado'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
