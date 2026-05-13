#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЭДО ЛДПР — PyQt6 + Flask.
- Локально: встроенный Flask + SQLite (как раньше).
- Общая БД для всех ПК: Flask и PostgreSQL на Render; EXE только открывает URL (или задаёт EDO_REMOTE_URL).

Важно: SQLite на Render нельзя «шарить» между компьютерами; данные живут в PostgreSQL на стороне сервера.
"""

import os
import sys
import json
import sqlite3
import secrets
import uuid
from datetime import datetime, timedelta
from functools import wraps

try:
    import psycopg2
    from psycopg2 import errors as pg_errors
    from psycopg2.extras import RealDictCursor
except ImportError:  # локальная сборка без серверных зависимостей
    psycopg2 = None
    pg_errors = None
    RealDictCursor = None

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QMessageBox, QStatusBar,
)
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

from flask import (
    Flask, render_template_string, request, redirect, url_for,
    session, flash, g, send_file,
)
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import DictLoader

from templates_pkg import TEMPLATES

# --- пути ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _app_base_dir():
    """Каталог exe при PyInstaller, иначе каталог скрипта."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return BASE_DIR


def _normalize_postgres_url(url: str) -> str:
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://') :]
    if 'sslmode=' not in url and 'render.com' in url:
        url += ('&' if '?' in url else '?') + 'sslmode=require'
    return url


RAW_DATABASE_URL = (os.environ.get('DATABASE_URL') or '').strip()
POSTGRES_URL = _normalize_postgres_url(RAW_DATABASE_URL) if RAW_DATABASE_URL else None
PSYCOPG2_AVAILABLE = psycopg2 is not None and POSTGRES_URL is not None

app_flask = Flask(__name__)
app_flask.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
DB_PATH = os.path.join(_app_base_dir(), 'edo_ldpr.db')
app_flask.config['DATABASE'] = DB_PATH
app_flask.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app_flask.config.setdefault('FORCE_SQLITE', False)

STATIC_DIR = os.path.join(_app_base_dir(), 'static')
BG_PATH = os.path.join(STATIC_DIR, 'bg.png')

app_flask.jinja_loader = DictLoader(TEMPLATES)


class _CursorShim:
    def __init__(self, raw):
        self._raw = raw

    def fetchone(self):
        return self._raw.fetchone()

    def fetchall(self):
        return self._raw.fetchall()


class DbConnection:
    """Единый интерфейс: execute(...).fetch*(), commit(), close(), executescript()."""

    def __init__(self, raw_conn, dialect: str):
        self._conn = raw_conn
        self.dialect = dialect

    def execute(self, sql: str, params=()):
        if self.dialect == 'postgres':
            sql = sql.replace('?', '%s')
        cur = self._conn.cursor()
        cur.execute(sql, tuple(params) if params is not None else ())
        return _CursorShim(cur)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def executescript(self, script: str):
        if self.dialect == 'sqlite':
            self._conn.executescript(script)
            return
        cleaned = []
        for line in script.splitlines():
            s = line.strip()
            if s.startswith('--') or not s:
                continue
            cleaned.append(line)
        text = '\n'.join(cleaned)
        for part in text.split(';'):
            stmt = part.strip()
            if stmt:
                cur = self._conn.cursor()
                cur.execute(stmt)


def _use_sqlite() -> bool:
    from flask import has_app_context, current_app

    if not has_app_context():
        return not PSYCOPG2_AVAILABLE
    if current_app.config.get('FORCE_SQLITE'):
        return True
    return not PSYCOPG2_AVAILABLE


def get_db():
    if 'db' not in g:
        if _use_sqlite():
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA foreign_keys=ON')
            g.db = DbConnection(conn, 'sqlite')
        else:
            conn = psycopg2.connect(POSTGRES_URL, cursor_factory=RealDictCursor)
            g.db = DbConnection(conn, 'postgres')
    return g.db


@app_flask.teardown_appcontext
def close_db(_error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    if db.dialect == 'postgres':
        db.executescript(
            '''
            CREATE TABLE IF NOT EXISTS users (
                uid TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'executor',
                department_id TEXT,
                avatar_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS departments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                head_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                priority TEXT DEFAULT 'Нормальный',
                status TEXT DEFAULT 'Черновик',
                created_by TEXT NOT NULL,
                creator_name TEXT,
                assigned_department_id TEXT,
                assigned_executor_id TEXT,
                deadline TEXT,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_history (
                id SERIAL PRIMARY KEY,
                order_id TEXT NOT NULL,
                action TEXT NOT NULL,
                user_name TEXT,
                user_role TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            '''
        )
    else:
        db.executescript(
            '''
            CREATE TABLE IF NOT EXISTS users (
                uid TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'executor',
                department_id TEXT,
                avatar_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS departments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                head_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (head_id) REFERENCES users(uid)
            );
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                priority TEXT DEFAULT 'Нормальный',
                status TEXT DEFAULT 'Черновик',
                created_by TEXT NOT NULL,
                creator_name TEXT,
                assigned_department_id TEXT,
                assigned_executor_id TEXT,
                deadline TEXT,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS order_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                action TEXT NOT NULL,
                user_name TEXT,
                user_role TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            '''
        )
    db.commit()


def _is_unique_violation(exc: BaseException) -> bool:
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    if pg_errors and isinstance(exc, pg_errors.UniqueViolation):
        return True
    return False


def seed_database():
    db = get_db()
    row = db.execute('SELECT COUNT(*) AS cnt FROM users').fetchone()
    n = row['cnt'] if hasattr(row, 'keys') else row[0]
    if n > 0:
        return

    departments = [
        ('dept-1', 'Центральный аппарат', None),
        ('dept-2', 'Юридический отдел', None),
        ('dept-3', 'Организационный отдел', None),
        ('dept-4', 'Информационный отдел', None),
        ('dept-5', 'Отдел регионального развития', None),
    ]
    for d in departments:
        if db.dialect == 'postgres':
            db.execute(
                'INSERT INTO departments (id, name, head_id) VALUES (?, ?, ?) ON CONFLICT (id) DO NOTHING',
                d,
            )
        else:
            db.execute('INSERT OR IGNORE INTO departments (id, name, head_id) VALUES (?, ?, ?)', d)
    db.commit()

    users_data = [
        ('u-admin', 'Администратор Системы', 'admin@ldpr.ru', 'admin', 'admin123', 'admin', None),
        ('u-sec', 'Главный Секретарь', 'sec@ldpr.ru', 'secretary', 'sec123', 'secretary', None),
        ('u-head-central', 'Руководитель ЦА', 'headca@ldpr.ru', 'head_central', 'head123', 'head_central', 'dept-1'),
        ('u-head-dept', 'Начальник Юридического Отдела', 'headlaw@ldpr.ru', 'head_department', 'head123', 'head_department', 'dept-2'),
        ('u-ast', 'Помощник Депутата', 'ast@ldpr.ru', 'assistant', 'ast123', 'assistant', None),
        ('u-exec', 'Рядовой Исполнитель', 'exec@ldpr.ru', 'executor', 'exec123', 'executor', 'dept-2'),
        ('u-exec2', 'Специалист ИТ', 'it@ldpr.ru', 'executor_it', 'exec123', 'executor', 'dept-4'),
    ]

    for uid, full_name, email, username, plain_pwd, role, dept_id in users_data:
        hashed = generate_password_hash(plain_pwd)
        try:
            db.execute(
                'INSERT INTO users (uid, full_name, email, username, password, role, department_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (uid, full_name, email, username, hashed, role, dept_id),
            )
        except Exception as e:  # noqa: BLE001
            if _is_unique_violation(e):
                db.rollback()
                db.execute(
                    'UPDATE users SET password = ?, role = ?, department_id = ? WHERE username = ?',
                    (hashed, role, dept_id, username),
                )
            else:
                raise
    db.commit()

    db.execute("UPDATE departments SET head_id = 'u-head-central' WHERE id = 'dept-1'")
    db.execute("UPDATE departments SET head_id = 'u-head-dept' WHERE id = 'dept-2'")
    db.commit()


# --- модели ---
class UserModel:
    @staticmethod
    def get_by_id(uid):
        return get_db().execute('SELECT * FROM users WHERE uid = ?', (uid,)).fetchone()

    @staticmethod
    def get_by_username(username):
        return get_db().execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    @staticmethod
    def create(uid, full_name, email, username, password, role='executor', department_id=None):
        db = get_db()
        try:
            db.execute(
                'INSERT INTO users (uid, full_name, email, username, password, role, department_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (uid, full_name, email, username, password, role, department_id),
            )
            db.commit()
            return True, None
        except Exception as e:  # noqa: BLE001
            if _is_unique_violation(e):
                db.rollback()
                msg = str(e).lower()
                if 'username' in msg or 'users.username' in msg:
                    return False, 'Пользователь с таким логином уже существует'
                if 'email' in msg or 'users.email' in msg:
                    return False, 'Пользователь с таким email уже существует'
                return False, 'Ошибка при создании пользователя'
            raise

    @staticmethod
    def update(uid, **kwargs):
        db = get_db()
        allowed = ['full_name', 'email', 'username', 'role', 'department_id', 'avatar_url']
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return
        set_clause = ', '.join(f'{k} = ?' for k in updates)
        values = list(updates.values()) + [uid]
        db.execute(f'UPDATE users SET {set_clause} WHERE uid = ?', values)
        db.commit()

    @staticmethod
    def update_password(uid, new_password):
        get_db().execute('UPDATE users SET password = ? WHERE uid = ?', (new_password, uid))
        get_db().commit()

    @staticmethod
    def delete(uid):
        get_db().execute('DELETE FROM users WHERE uid = ?', (uid,))
        get_db().commit()

    @staticmethod
    def get_by_department(department_id):
        return get_db().execute('SELECT * FROM users WHERE department_id = ?', (department_id,)).fetchall()

    @staticmethod
    def get_all():
        return get_db().execute('SELECT * FROM users ORDER BY full_name').fetchall()


class DepartmentModel:
    @staticmethod
    def get_all():
        return get_db().execute('SELECT * FROM departments ORDER BY name').fetchall()

    @staticmethod
    def get_by_id(dept_id):
        return get_db().execute('SELECT * FROM departments WHERE id = ?', (dept_id,)).fetchone()

    @staticmethod
    def create(dept_id, name, head_id=None):
        db = get_db()
        try:
            db.execute('INSERT INTO departments (id, name, head_id) VALUES (?, ?, ?)', (dept_id, name, head_id))
            db.commit()
            return True
        except Exception as e:  # noqa: BLE001
            if _is_unique_violation(e):
                db.rollback()
                return False
            raise

    @staticmethod
    def delete(dept_id):
        get_db().execute('DELETE FROM departments WHERE id = ?', (dept_id,))
        get_db().commit()


class OrderModel:
    STATUSES = [
        'Черновик',
        'На утверждении',
        'Утверждено',
        'В отделе',
        'Назначен исполнитель',
        'В работе',
        'Готово к проверке',
        'Подтверждено',
        'На доработке',
        'Закрыто',
        'Отклонено',
    ]
    PRIORITIES = ['Низкий', 'Нормальный', 'Высокий', 'Срочный']

    @staticmethod
    def get_all():
        return get_db().execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()

    @staticmethod
    def get_by_id(order_id):
        order = get_db().execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not order:
            return None
        order = dict(order)
        if order.get('result'):
            try:
                order['result'] = json.loads(order['result'])
            except (json.JSONDecodeError, TypeError):
                pass
        return order

    @staticmethod
    def get_by_department(dept_id):
        return get_db().execute(
            'SELECT * FROM orders WHERE assigned_department_id = ? ORDER BY created_at DESC',
            (dept_id,),
        ).fetchall()

    @staticmethod
    def create(order_id, title, content, priority, status, created_by, creator_name, deadline=None, assigned_department_id=None):
        get_db().execute(
            'INSERT INTO orders (id, title, content, priority, status, created_by, creator_name, deadline, assigned_department_id, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
            (order_id, title, content, priority, status, created_by, creator_name, deadline, assigned_department_id),
        )
        get_db().commit()

    @staticmethod
    def update(order_id, **kwargs):
        db = get_db()
        if 'result' in kwargs and kwargs['result']:
            kwargs['result'] = json.dumps(kwargs['result'], ensure_ascii=False)
        allowed = [
            'title',
            'content',
            'priority',
            'status',
            'assigned_department_id',
            'assigned_executor_id',
            'deadline',
            'result',
        ]
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return
        set_clause = ', '.join(f'{k} = ?' for k in updates) + ', updated_at = CURRENT_TIMESTAMP'
        values = list(updates.values()) + [order_id]
        db.execute(f'UPDATE orders SET {set_clause} WHERE id = ?', values)
        db.commit()

    @staticmethod
    def get_by_user(uid, role, department_id=None):
        db = get_db()
        if role == 'admin':
            return db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
        if role == 'assistant':
            return db.execute('SELECT * FROM orders WHERE created_by = ? ORDER BY created_at DESC', (uid,)).fetchall()
        if role == 'head_department' and department_id:
            return db.execute(
                'SELECT * FROM orders WHERE assigned_department_id = ? ORDER BY created_at DESC',
                (department_id,),
            ).fetchall()
        if role == 'executor':
            return db.execute(
                'SELECT * FROM orders WHERE assigned_executor_id = ? ORDER BY created_at DESC',
                (uid,),
            ).fetchall()
        if role == 'secretary':
            return db.execute(
                """SELECT * FROM orders WHERE status IN (
                    'Утверждено','В отделе','Назначен исполнитель','В работе',
                    'Готово к проверке','На доработке','Закрыто'
                ) ORDER BY created_at DESC"""
            ).fetchall()
        return db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()

    @staticmethod
    def get_stats(uid=None, role=None, department_id=None):
        orders = OrderModel.get_by_user(uid, role, department_id) if uid else OrderModel.get_all()
        return {
            'total': len(orders),
            'pending': sum(1 for o in orders if o['status'] == 'На утверждении'),
            'approved': sum(1 for o in orders if o['status'] == 'Утверждено'),
            'in_work': sum(1 for o in orders if o['status'] == 'В работе'),
        }


class OrderHistoryModel:
    @staticmethod
    def get_by_order(order_id):
        return get_db().execute(
            'SELECT * FROM order_history WHERE order_id = ? ORDER BY created_at DESC',
            (order_id,),
        ).fetchall()

    @staticmethod
    def add(order_id, action, user_name, user_role, details=None):
        get_db().execute(
            'INSERT INTO order_history (order_id, action, user_name, user_role, details) VALUES (?, ?, ?, ?, ?)',
            (order_id, action, user_name, user_role, details),
        )
        get_db().commit()


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def _department_with_head(dept_row):
    d = _row_to_dict(dept_row)
    if not d:
        return None
    hid = d.get('head_id')
    if hid:
        h = UserModel.get_by_id(hid)
        d['head_name'] = h['full_name'] if h else None
    else:
        d['head_name'] = None
    return d


def _departments_list_with_heads():
    out = []
    for row in DepartmentModel.get_all():
        out.append(_department_with_head(row))
    return out


# --- декораторы ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_role' not in session:
                return redirect(url_for('login'))
            if session['user_role'] not in roles:
                flash('Недостаточно прав', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)

        return decorated

    return decorator


@app_flask.context_processor
def inject_user():
    if 'user_id' in session:
        user = UserModel.get_by_id(session['user_id'])
        if user:
            return {'current_user': dict(user)}
    return {'current_user': None}


# --- маршруты ---
@app_flask.route('/static/bg.png')
def serve_bg():
    if os.path.exists(BG_PATH):
        return send_file(BG_PATH, mimetype='image/png')
    return ('', 404)


@app_flask.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = UserModel.get_by_username(username)
        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['uid']
            session['user_name'] = user['full_name']
            session['user_role'] = user['role']
            session['department_id'] = user['department_id']
            flash(f'Добро пожаловать, {user["full_name"]}!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Неверный логин или пароль', 'danger')
    return render_template_string(TEMPLATES['login.html'], bg_url='/static/bg.png')


@app_flask.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app_flask.route('/')
@login_required
def dashboard():
    stats = OrderModel.get_stats(
        uid=session['user_id'],
        role=session['user_role'],
        department_id=session.get('department_id'),
    )
    orders = OrderModel.get_by_user(
        uid=session['user_id'],
        role=session['user_role'],
        department_id=session.get('department_id'),
    )[:5]
    return render_template_string(TEMPLATES['dashboard.html'], stats=stats, orders=orders)


@app_flask.route('/orders')
@login_required
def orders_list():
    all_orders = OrderModel.get_by_user(
        uid=session['user_id'],
        role=session['user_role'],
        department_id=session.get('department_id'),
    )
    status_filter = request.args.get('status', 'Все')
    search = request.args.get('search', '').lower()
    priority_filter = request.args.get('priority', 'Все')
    filtered = list(all_orders)
    if status_filter != 'Все':
        filtered = [o for o in filtered if o['status'] == status_filter]
    if priority_filter != 'Все':
        filtered = [o for o in filtered if o['priority'] == priority_filter]
    if search:
        filtered = [o for o in filtered if search in (o['title'] or '').lower()]
    return render_template_string(
        TEMPLATES['orders.html'],
        orders=filtered,
        statuses=OrderModel.STATUSES,
        priorities=OrderModel.PRIORITIES,
    )


@app_flask.route('/orders/create', methods=['POST'])
@login_required
@role_required('assistant')
def create_order():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    if not title or not content:
        flash('Заголовок и содержание обязательны', 'danger')
        return redirect(url_for('orders_list'))
    order_id = 'order-' + str(uuid.uuid4())[:8]
    is_draft = request.form.get('is_draft') == '1'
    status = 'Черновик' if is_draft else 'На утверждении'
    user = UserModel.get_by_id(session['user_id'])
    OrderModel.create(
        order_id,
        title,
        content,
        request.form.get('priority', 'Нормальный'),
        status,
        session['user_id'],
        user['full_name'],
        request.form.get('deadline') or None,
    )
    OrderHistoryModel.add(order_id, 'Создание распоряжения', user['full_name'], session['user_role'], f'Статус: {status}')
    flash('Распоряжение создано', 'success')
    return redirect(url_for('orders_list'))


@app_flask.route('/orders/<order_id>')
@login_required
def order_details(order_id):
    order = OrderModel.get_by_id(order_id)
    if not order:
        flash('Распоряжение не найдено', 'danger')
        return redirect(url_for('orders_list'))
    history = OrderHistoryModel.get_by_order(order_id)
    departments = DepartmentModel.get_all()
    dept_users = UserModel.get_by_department(order.get('assigned_department_id')) if order.get('assigned_department_id') else []
    return render_template_string(
        TEMPLATES['order_details.html'],
        order=order,
        history=history,
        departments=departments,
        dept_users=dept_users,
    )


@app_flask.route('/department')
@login_required
def department():
    if session.get('user_role') == 'admin':
        departments = _departments_list_with_heads()
        return render_template_string(TEMPLATES['admin_departments.html'], departments=departments)

    dept_id = session.get('department_id')
    if not dept_id:
        flash('У вас нет назначенного отдела', 'warning')
        return redirect(url_for('dashboard'))
    department_row = DepartmentModel.get_by_id(dept_id)
    if not department_row:
        flash('Отдел не найден', 'danger')
        return redirect(url_for('dashboard'))
    users = UserModel.get_by_department(dept_id)
    orders = OrderModel.get_by_department(dept_id)
    return render_template_string(
        TEMPLATES['department.html'],
        department=_department_with_head(department_row),
        users=users,
        orders=orders,
    )


@app_flask.route('/department/<dept_id>')
@login_required
@role_required('admin')
def department_details(dept_id):
    dept = DepartmentModel.get_by_id(dept_id)
    if not dept:
        flash('Отдел не найден', 'danger')
        return redirect(url_for('department'))
    users = UserModel.get_by_department(dept_id)
    orders = OrderModel.get_by_department(dept_id)
    return render_template_string(
        TEMPLATES['department.html'],
        department=_department_with_head(dept),
        users=users,
        orders=orders,
    )


@app_flask.route('/department/create', methods=['POST'])
@login_required
@role_required('admin')
def create_department():
    name = request.form.get('name', '').strip()
    if not name:
        flash('Введите название отдела', 'danger')
        return redirect(url_for('department'))
    dept_id = 'dept-' + str(uuid.uuid4())[:8]
    if DepartmentModel.create(dept_id, name):
        flash('Отдел создан', 'success')
    else:
        flash('Ошибка при создании отдела', 'danger')
    return redirect(url_for('department'))


@app_flask.route('/admin')
@login_required
@role_required('admin')
def admin_panel():
    users = UserModel.get_all()
    departments = _departments_list_with_heads()
    return render_template_string(TEMPLATES['admin.html'], users=users, departments=departments)


@app_flask.route('/orders/<order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = OrderModel.get_by_id(order_id)
    if not order:
        flash('Распоряжение не найдено', 'danger')
        return redirect(url_for('orders_list'))

    new_status = request.form.get('status')
    comment = request.form.get('comment', '')
    user = UserModel.get_by_id(session['user_id'])
    current_role = session['user_role']
    current_status = order['status']

    allowed = False
    details = f'Статус: {new_status}'
    extra = {}

    if current_role == 'head_central' and current_status == 'На утверждении' and new_status in ['Утверждено', 'Отклонено']:
        allowed = True
    elif current_role == 'secretary' and current_status == 'Утверждено':
        dept_id = request.form.get('department_id')
        if dept_id:
            allowed = True
            new_status = 'В отделе'
            extra['assigned_department_id'] = dept_id
            dept = DepartmentModel.get_by_id(dept_id)
            details = f'Назначен отдел: {dept["name"] if dept else dept_id}'
    elif current_role == 'head_department' and current_status == 'В отделе':
        exec_id = request.form.get('executor_id')
        if exec_id:
            allowed = True
            new_status = 'Назначен исполнитель'
            extra['assigned_executor_id'] = exec_id
            executor = UserModel.get_by_id(exec_id)
            details = f'Назначен исполнитель: {executor["full_name"] if executor else exec_id}'
    elif (
        current_role == 'executor'
        and current_status == 'Назначен исполнитель'
        and order.get('assigned_executor_id') == session['user_id']
    ):
        allowed = True
        new_status = 'В работе'
    elif current_role == 'head_department' and current_status == 'Готово к проверке' and new_status == 'Подтверждено':
        allowed = True
        details = 'Работа подтверждена начальником отдела'
    elif current_role == 'head_central' and current_status == 'Подтверждено' and new_status == 'Закрыто':
        allowed = True
        details = 'Распоряжение закрыто руководителем ЦА'
    elif (
        current_role in ['head_department', 'head_central']
        and current_status in ['Готово к проверке', 'Подтверждено']
        and new_status == 'На доработке'
    ):
        allowed = True
        details = f'Отправлено на доработку: {comment}' if comment else 'Отправлено на доработку'

    if allowed:
        OrderModel.update(order_id, status=new_status, **extra)
        OrderHistoryModel.add(order_id, 'Изменение статуса', user['full_name'], current_role, details)
        flash('Статус обновлен', 'success')
    else:
        flash('Действие не разрешено', 'danger')

    return redirect(url_for('order_details', order_id=order_id))


@app_flask.route('/orders/<order_id>/submit', methods=['POST'])
@login_required
def submit_order_result(order_id):
    order = OrderModel.get_by_id(order_id)
    if not order:
        flash('Распоряжение не найдено', 'danger')
        return redirect(url_for('orders_list'))

    current_role = session['user_role']
    current_status = order['status']
    result_content = request.form.get('result_content', '').strip()

    if current_role != 'executor' or current_status != 'В работе' or order.get('assigned_executor_id') != session['user_id']:
        flash('Действие не разрешено', 'danger')
        return redirect(url_for('order_details', order_id=order_id))

    if not result_content:
        flash('Опишите результат выполнения', 'warning')
        return redirect(url_for('order_details', order_id=order_id))

    result = {'content': result_content, 'submittedAt': datetime.now().isoformat(), 'submittedBy': session['user_id']}
    OrderModel.update(order_id, status='Готово к проверке', result=result)
    user = UserModel.get_by_id(session['user_id'])
    OrderHistoryModel.add(order_id, 'Сдача работы', user['full_name'], current_role, 'Работа сдана на проверку')
    flash('Работа сдана на проверку', 'success')
    return redirect(url_for('order_details', order_id=order_id))


@app_flask.route('/admin/users/create', methods=['POST'])
@login_required
@role_required('admin')
def admin_create_user():
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'executor')
    department_id = request.form.get('department_id') or None

    if not full_name or not email or not username or not password:
        flash('Все поля обязательны для заполнения', 'danger')
        return redirect(url_for('admin_panel'))

    uid = 'u-' + str(uuid.uuid4())[:8]
    hashed_pwd = generate_password_hash(password)
    success, error = UserModel.create(uid, full_name, email, username, hashed_pwd, role, department_id)
    flash('Пользователь успешно создан' if success else (error or 'Ошибка'), 'success' if success else 'danger')
    return redirect(url_for('admin_panel'))


@app_flask.route('/admin/users/<uid>/edit', methods=['POST'])
@login_required
@role_required('admin')
def admin_edit_user(uid):
    user = UserModel.get_by_id(uid)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin_panel'))

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role')
    department_id = request.form.get('department_id') or None

    updates = {}
    if full_name:
        updates['full_name'] = full_name
    if email:
        updates['email'] = email
    if role:
        updates['role'] = role
    updates['department_id'] = department_id
    UserModel.update(uid, **updates)
    flash('Пользователь обновлен', 'success')
    return redirect(url_for('admin_panel'))


@app_flask.route('/admin/users/<uid>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_user(uid):
    user = UserModel.get_by_id(uid)
    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('admin_panel'))
    if uid == session['user_id']:
        flash('Нельзя удалить самого себя', 'danger')
        return redirect(url_for('admin_panel'))
    UserModel.delete(uid)
    flash('Пользователь удален', 'success')
    return redirect(url_for('admin_panel'))


@app_flask.route('/admin/departments/<dept_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_department(dept_id):
    dept = DepartmentModel.get_by_id(dept_id)
    if not dept:
        flash('Отдел не найден', 'danger')
        return redirect(url_for('department'))
    DepartmentModel.delete(dept_id)
    flash('Отдел удален', 'success')
    return redirect(url_for('department'))


@app_flask.route('/admin/departments/<dept_id>/set_head', methods=['POST'])
@login_required
@role_required('admin')
def admin_set_department_head(dept_id):
    head_id = request.form.get('head_id')
    if not head_id:
        flash('Выберите руководителя', 'danger')
        return redirect(url_for('department'))
    db = get_db()
    db.execute('UPDATE departments SET head_id = ? WHERE id = ?', (head_id, dept_id))
    db.execute('UPDATE users SET department_id = ? WHERE uid = ?', (dept_id, head_id))
    db.commit()
    flash('Руководитель назначен', 'success')
    return redirect(url_for('department'))


# Инициализация PostgreSQL на Render при деплое (локальный EXE без RENDER сюда не попадает)
if PSYCOPG2_AVAILABLE and str(os.environ.get('RENDER', '')).lower() == 'true':
    with app_flask.app_context():
        init_db()
        seed_database()


class FlaskThread(QThread):
    server_started = pyqtSignal(str)

    def __init__(self, port=5000):
        super().__init__()
        self.port = port

    def run(self):
        app_flask.config['FORCE_SQLITE'] = True
        try:
            with app_flask.app_context():
                init_db()
                seed_database()
        finally:
            pass
        from werkzeug.serving import make_server

        server = make_server('127.0.0.1', self.port, app_flask, threaded=True)
        self.server_started.emit(f'http://127.0.0.1:{self.port}')
        server.serve_forever()


def _read_remote_url() -> str:
    url = (os.environ.get('EDO_REMOTE_URL') or os.environ.get('REMOTE_APP_URL') or '').strip()
    if url:
        return url.rstrip('/')
    cfg = os.path.join(_app_base_dir(), 'edo_remote.url')
    if os.path.isfile(cfg):
        try:
            with open(cfg, encoding='utf-8') as f:
                return f.read().strip().rstrip('/')
        except OSError:
            return ''
    return ''


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ЭДО ЛДПР')
        self.setMinimumSize(1400, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        layout.addWidget(self.web_view)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        refresh_action = QAction('Обновить', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.web_view.reload)
        file_menu.addAction(refresh_action)
        file_menu.addSeparator()
        exit_action = QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu('Вид')
        zoom_in = QAction('Увеличить', self)
        zoom_in.setShortcut('Ctrl++')
        zoom_in.triggered.connect(lambda: self.web_view.setZoomFactor(self.web_view.zoomFactor() + 0.1))
        view_menu.addAction(zoom_in)
        zoom_out = QAction('Уменьшить', self)
        zoom_out.setShortcut('Ctrl+-')
        zoom_out.triggered.connect(lambda: self.web_view.setZoomFactor(self.web_view.zoomFactor() - 0.1))
        view_menu.addAction(zoom_out)

        help_menu = menubar.addMenu('Помощь')
        about = QAction('О программе', self)
        about.triggered.connect(
            lambda: QMessageBox.about(
                self,
                'О программе',
                '<h3>ЭДО ЛДПР</h3><p>Сервер: общая БД на Render (PostgreSQL).</p>'
                '<p>Клиент: при наличии файла edo_remote.url или переменной EDO_REMOTE_URL открывается удалённый адрес.</p>',
            )
        )
        help_menu.addAction(about)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.remote_url = _read_remote_url()
        if self.remote_url:
            self.status_bar.showMessage(f'Подключение к серверу: {self.remote_url}')
            self.web_view.load(QUrl(self.remote_url))
        else:
            self.status_bar.showMessage('Запуск локального сервера...')
            self.flask_thread = FlaskThread(port=int(os.environ.get('EDO_LOCAL_PORT', '5000')))
            self.flask_thread.server_started.connect(self._on_server_started)
            self.flask_thread.start()

    def _on_server_started(self, url: str):
        self.status_bar.showMessage(f'Локально: {url}')
        self.web_view.load(QUrl(url))

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Закрыть приложение?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName('ЭДО ЛДПР')
    app.setApplicationVersion('1.1')
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 10))

    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
