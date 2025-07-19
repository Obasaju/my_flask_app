from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_scss import Scss
from datetime import datetime, timezone
import uuid
import os
import boto3

app = Flask(__name__)
app.debug = True
Scss(app, static_dir='static', asset_dir='assets')

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Tasks')

# ===== HTML Routes =====

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        content = request.form['content']
        task_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        table.put_item(
            Item={
                'id': task_id,
                'content': content,
                'created_at': created_at
            }
        )
        return redirect('/')

    response = table.scan()
    tasks = response.get('Items', [])
    return render_template('index.html', tasks=tasks)

@app.route('/edit/<string:id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        new_content = request.form['task']
        response = table.get_item(Key={'id': id})
        task = response.get('Item')

        if not task:
            return "Task not found", 404

        # Keep original 'created_at'
        table.put_item(
            Item={
                'id': id,
                'content': new_content,
                'created_at': task.get('created_at', datetime.now(timezone.utc).isoformat())
            }
        )
        return redirect('/')

    response = table.get_item(Key={'id': id})
    task = response.get('Item')
    if not task:
        return "Task not found", 404
    return render_template('edit.html', task=task)

@app.route('/delete/<string:id>')
def delete_task(id):
    table.delete_item(Key={'id': id})
    return redirect('/')


# ===== API Routes =====

@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    response = table.scan()
    tasks = response.get('Items', [])
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(tasks)

@app.route('/api/tasks/<string:id>', methods=['GET'])
def api_get_task(id):
    response = table.get_item(Key={'id': id})
    task = response.get('Item')
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    data = request.get_json()
    task_content = data.get('task')
    if not task_content:
        return jsonify({'error': 'Task content is required'}), 400

    new_task = {
        'id': str(uuid.uuid4()),
        'content': task_content,
        'complete': 0,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    table.put_item(Item=new_task)
    return jsonify(new_task), 201

@app.route('/api/tasks/<string:id>', methods=['PUT'])
def api_update_task(id):
    data = request.get_json()
    task_content = data.get('task')
    if not task_content:
        return jsonify({'error': 'Task content is required'}), 400

    # preserve created_at
    response = table.get_item(Key={'id': id})
    existing = response.get('Item', {})
    table.put_item(Item={
        'id': id,
        'content': task_content,
        'created_at': existing.get('created_at', datetime.now(timezone.utc).isoformat())
    })

    updated = table.get_item(Key={'id': id}).get('Item')
    return jsonify(updated)

@app.route('/api/tasks/<string:id>', methods=['DELETE'])
def api_delete_task(id):
    table.delete_item(Key={'id': id})
    return jsonify({'message': 'Task deleted'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
