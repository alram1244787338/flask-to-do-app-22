from app import app, db
from flask import render_template, url_for, flash, get_flashed_messages, redirect, request
from datetime import datetime

import models
import forms

@app.route('/')
@app.route('/index')
def index():
    tasks = models.Task.query.all()
    return render_template('index.html', tasks=tasks)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = forms.AddTaskForm()
    if form.validate_on_submit():
        task = models.Task(title=form.title.data)
        db.session.add(task)
        db.session.commit()
        flash('Task added')
        return redirect(url_for('index'))
    return render_template('add.html', form=form)


@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
def edit(task_id):
    task = models.Task.query.get(task_id)
    if not task:
        flash(f'Task with id {task_id} does not exist')
        return redirect(url_for('index'))
    form = forms.AddTaskForm()
    if form.validate_on_submit():
        task.title = form.title.data
        task.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Task updated')
        return redirect(url_for('index'))
    form.title.data = task.title
    return render_template('edit.html', form=form, task_id=task_id)


@app.route('/delete/<int:task_id>', methods=['GET', 'POST'])
def delete(task_id):
    task = models.Task.query.get(task_id)
    if not task:
        flash(f'Task with id {task_id} does not exist')
        return redirect(url_for('index'))
    form = forms.DeleteTaskForm()
    # The task is removed only on an explicit POST submission coming from the
    # confirmation page. A plain GET just renders the confirmation page and
    # never mutates data, so the homepage button cannot delete on its own.
    if form.validate_on_submit():
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted')
        return redirect(url_for('index'))
    return render_template('delete.html', form=form, task_id=task_id, title=task.title)
