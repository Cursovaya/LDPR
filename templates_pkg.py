# -*- coding: utf-8 -*-
"""Jinja-шаблоны (вынесены из основного модуля для удобства правок)."""

BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}ЭДО ЛДПР{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
    <style>
        :root { --ldpr-blue: #003399; --ldpr-gold: #FFD700; }
        body { background: #f4f6f9; font-family: 'Segoe UI', sans-serif; }
        .navbar { background: linear-gradient(135deg, #003399, #001a4d); }
        .navbar-brand { font-weight: 900; letter-spacing: -1px; }
        .sidebar { background: white; min-height: calc(100vh - 56px); box-shadow: 2px 0 10px rgba(0,0,0,0.05); }
        .sidebar .nav-link { color: #555; border-radius: 10px; margin: 3px 8px; padding: 10px 16px; font-weight: 500; }
        .sidebar .nav-link:hover { background: #eef; color: #003399; }
        .sidebar .nav-link.active { background: #003399; color: #fff !important; }
        .card { border: none; border-radius: 18px; box-shadow: 0 2px 16px rgba(0,0,0,0.05); }
        .stat-card { border-left: 5px solid #003399; }
        .badge-status { font-size: 0.75rem; font-weight: 600; padding: 6px 14px; border-radius: 20px; }
        .btn-primary { background: #003399; border: none; }
        .btn-primary:hover { background: #002266; }
        .btn-gold { background: #FFD700; color: #000; font-weight: 700; }
        .table th { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #888; }
    </style>
</head>
<body>
    {% if current_user %}
    <nav class="navbar navbar-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/"><i class="bi bi-building"></i> ЭДО ЛДПР</a>
            <div class="d-flex align-items-center gap-3">
                <span class="text-light">{{ current_user.full_name }}</span>
                <a href="/logout" class="btn btn-outline-light btn-sm"><i class="bi bi-box-arrow-right"></i> Выход</a>
            </div>
        </div>
    </nav>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 sidebar py-3">
                <div class="text-center mb-4">
                    <div class="bg-primary text-white rounded-circle d-inline-flex align-items-center justify-content-center" style="width:64px;height:64px;font-size:1.5rem;font-weight:700;">{{ current_user.full_name[0] }}</div>
                    <p class="mt-2 mb-0 fw-bold">{{ current_user.full_name }}</p>
                    <small class="text-muted">{{ current_user.role }}</small>
                </div>
                <nav class="nav flex-column">
                    <a class="nav-link {{ 'active' if request.path == '/' }}" href="/"><i class="bi bi-speedometer2 me-2"></i>Рабочий стол</a>
                    <a class="nav-link {{ 'active' if '/orders' in request.path }}" href="/orders"><i class="bi bi-file-text me-2"></i>Распоряжения</a>
                    {% if current_user.role in ['head_department', 'admin'] %}
                    <a class="nav-link {{ 'active' if request.path == '/department' }}" href="/department"><i class="bi bi-people me-2"></i>Отдел</a>
                    {% endif %}
                    {% if current_user.role == 'admin' %}
                    <a class="nav-link {{ 'active' if request.path == '/admin' }}" href="/admin"><i class="bi bi-gear me-2"></i>Админ</a>
                    {% endif %}
                </nav>
            </div>
            <div class="col-md-10 p-4">
                {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                {% for cat, msg in messages %}
                <div class="alert alert-{{ cat }} alert-dismissible fade show" role="alert">{{ msg }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>
                {% endfor %}
                {% endif %}
                {% endwith %}
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
    {% else %}
    {% block full_content %}{% endblock %}
    {% endif %}
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>'''

LOGIN_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Вход - ЭДО ЛДПР{% endblock %}
{% block full_content %}
<style>
    .login-page-new {
        background-image: url('/static/bg.png');
        background-size: cover;
        background-position: center;
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    .login-card-new {
        background: #003399;
        border: 3px solid #FFD700;
        border-radius: 20px;
        padding: 40px 50px;
        max-width: 420px;
        width: 100%;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }
    .login-logo { display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 10px; }
    .login-logo-line { height: 2px; width: 60px; background: #FFD700; }
    .login-logo-text { color: #FFD700; font-size: 3rem; font-weight: 900; letter-spacing: 4px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .login-subtitle { color: #FFD700; text-align: center; font-size: 0.75rem; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 30px; line-height: 1.4; }
    .login-label { color: #FFD700; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; display: block; }
    .login-input { background: transparent; border: 2px solid #FFD700; border-radius: 8px; color: #FFD700; padding: 12px 15px; width: 100%; font-size: 1rem; outline: none; transition: all 0.3s; }
    .login-input::placeholder { color: rgba(255,215,0,0.5); }
    .login-input:focus { background: rgba(255,215,0,0.1); box-shadow: 0 0 15px rgba(255,215,0,0.3); }
    .login-btn { background: linear-gradient(180deg, #FFD700 0%, #D4A500 100%); border: none; border-radius: 8px; color: #003399; font-weight: 700; font-size: 1.1rem; padding: 15px; width: 100%; text-transform: uppercase; letter-spacing: 2px; cursor: pointer; transition: all 0.3s; margin-top: 10px; }
    .login-btn:hover { background: linear-gradient(180deg, #FFE44D 0%, #FFD700 100%); box-shadow: 0 5px 20px rgba(255,215,0,0.4); }
    .login-alert { background: rgba(255,0,0,0.2); border: 1px solid #ff6b6b; color: #fff; padding: 10px; border-radius: 8px; margin-bottom: 20px; font-size: 0.85rem; }
    .input-icon-wrapper { position: relative; }
    .input-icon { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); color: #FFD700; opacity: 0.7; font-size: 1.1rem; }
    .login-input.with-icon { padding-left: 45px; }
</style>
<div class="login-page-new">
    <div class="login-card-new">
        <div class="login-logo">
            <div class="login-logo-line"></div>
            <div class="login-logo-text">ЛДПР</div>
            <div class="login-logo-line"></div>
        </div>
        <div class="login-subtitle">Либерально-демократическая<br>партия России</div>
        {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        {% for cat, msg in messages %}
        <div class="login-alert">{{ msg }}</div>
        {% endfor %}
        {% endif %}
        {% endwith %}
        <form method="POST">
            <div class="mb-3">
                <label class="login-label">Логин</label>
                <div class="input-icon-wrapper">
                    <i class="bi bi-person input-icon"></i>
                    <input type="text" name="username" class="login-input with-icon" placeholder="" required>
                </div>
            </div>
            <div class="mb-4">
                <label class="login-label">Пароль</label>
                <div class="input-icon-wrapper">
                    <i class="bi bi-lock input-icon"></i>
                    <input type="password" name="password" class="login-input with-icon" placeholder="" required>
                </div>
            </div>
            <button type="submit" class="login-btn">Войти</button>
        </form>
    </div>
</div>
{% endblock %}'''

DASHBOARD_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Рабочий стол - ЭДО ЛДПР{% endblock %}
{% block content %}
<h2 class="fw-bold mb-4"><i class="bi bi-speedometer2 me-2"></i>Рабочий стол</h2>
<div class="row mb-4">
    <div class="col-md-3 mb-3"><div class="card stat-card p-3"><small class="text-muted text-uppercase fw-bold" style="font-size:0.65rem;">Мои распоряжения</small><h2 class="fw-bold mb-0">{{ stats.total }}</h2></div></div>
    <div class="col-md-3 mb-3"><div class="card stat-card p-3" style="border-left-color:#f59e0b;"><small class="text-muted text-uppercase fw-bold" style="font-size:0.65rem;">На утверждении</small><h2 class="fw-bold mb-0">{{ stats.pending }}</h2></div></div>
    <div class="col-md-3 mb-3"><div class="card stat-card p-3" style="border-left-color:#10b981;"><small class="text-muted text-uppercase fw-bold" style="font-size:0.65rem;">Утверждено</small><h2 class="fw-bold mb-0">{{ stats.approved }}</h2></div></div>
    <div class="col-md-3 mb-3"><div class="card stat-card p-3" style="border-left-color:#6366f1;"><small class="text-muted text-uppercase fw-bold" style="font-size:0.65rem;">В работе</small><h2 class="fw-bold mb-0">{{ stats.in_work }}</h2></div></div>
</div>
<div class="card p-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h5 class="fw-bold mb-0">Последние распоряжения</h5>
        <a href="/orders" class="btn btn-primary btn-sm">Все распоряжения</a>
    </div>
    {% if orders %}
    <div class="table-responsive">
        <table class="table table-hover">
            <thead><tr><th>Документ</th><th>Статус</th><th>Приоритет</th><th>Создан</th></tr></thead>
            <tbody>
                {% for o in orders %}
                <tr style="cursor:pointer" onclick="location.href='/orders/{{ o.id }}'">
                    <td><strong>{{ o.title }}</strong><br><small class="text-muted">#{{ o.id[:8] }}</small></td>
                    <td><span class="badge badge-status {% if o.status in ['Утверждено','Закрыто'] %}bg-success{% elif o.status == 'Отклонено' %}bg-danger{% elif o.status == 'На утверждении' %}bg-warning text-dark{% else %}bg-primary{% endif %}">{{ o.status }}</span></td>
                    <td><span class="fw-bold {% if o.priority == 'Срочный' %}text-danger{% elif o.priority == 'Высокий' %}text-warning{% else %}text-primary{% endif %}">{{ o.priority }}</span></td>
                    <td><small class="text-muted">{{ o.created_at[:10] }}</small></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <p class="text-muted text-center py-4">Нет распоряжений</p>
    {% endif %}
</div>
{% endblock %}'''

ORDERS_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Реестр распоряжений - ЭДО ЛДПР{% endblock %}
{% block content %}
<h2 class="fw-bold mb-4"><i class="bi bi-file-text me-2"></i>Реестр распоряжений</h2>
<div class="card p-3 mb-4">
    <form method="GET" class="row g-3">
        <div class="col-md-4"><div class="input-group"><span class="input-group-text"><i class="bi bi-search"></i></span><input type="text" name="search" class="form-control" placeholder="Поиск..." value="{{ request.args.get('search','') }}"></div></div>
        <div class="col-md-3"><select name="status" class="form-select"><option value="Все">Все статусы</option>{% for s in statuses %}<option value="{{ s }}" {% if request.args.get('status') == s %}selected{% endif %}>{{ s }}</option>{% endfor %}</select></div>
        <div class="col-md-3"><select name="priority" class="form-select"><option value="Все">Все приоритеты</option>{% for p in priorities %}<option value="{{ p }}" {% if request.args.get('priority') == p %}selected{% endif %}>{{ p }}</option>{% endfor %}</select></div>
        <div class="col-md-2"><button type="submit" class="btn btn-primary w-100">Фильтр</button></div>
    </form>
</div>
{% if current_user.role in ['assistant'] %}
<button class="btn btn-primary mb-3" data-bs-toggle="modal" data-bs-target="#createModal"><i class="bi bi-plus-lg"></i> Создать</button>
{% endif %}
<div class="card">
    <div class="table-responsive">
        <table class="table table-hover mb-0">
            <thead><tr><th>Документ</th><th>Приоритет</th><th>Статус</th><th>Срок</th><th>Автор</th><th>Создан</th></tr></thead>
            <tbody>
                {% for o in orders %}
                <tr style="cursor:pointer" onclick="location.href='/orders/{{ o.id }}'">
                    <td><strong>{{ o.title }}</strong><br><small class="text-muted">#{{ o.id[:8] }}</small></td>
                    <td><span class="fw-bold {% if o.priority == 'Срочный' %}text-danger{% elif o.priority == 'Высокий' %}text-warning{% else %}text-primary{% endif %}">{{ o.priority }}</span></td>
                    <td><span class="badge badge-status {% if o.status in ['Утверждено','Закрыто'] %}bg-success{% elif o.status == 'Отклонено' %}bg-danger{% elif o.status == 'На утверждении' %}bg-warning text-dark{% else %}bg-primary{% endif %}">{{ o.status }}</span></td>
                    <td><small>{{ o.deadline or '-' }}</small></td>
                    <td><small>{{ o.creator_name }}</small></td>
                    <td><small class="text-muted">{{ o.created_at[:16] }}</small></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% if current_user.role in ['assistant'] %}
<div class="modal fade" id="createModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header"><h5 class="modal-title fw-bold">Новое распоряжение</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <form method="POST" action="/orders/create">
                <div class="modal-body">
                    <div class="mb-3"><label class="form-label fw-bold small text-uppercase text-muted">Заголовок</label><input type="text" name="title" class="form-control" required></div>
                    <div class="row mb-3">
                        <div class="col-md-6"><label class="form-label fw-bold small text-uppercase text-muted">Приоритет</label><select name="priority" class="form-select"><option>Низкий</option><option selected>Нормальный</option><option>Высокий</option><option>Срочный</option></select></div>
                        <div class="col-md-6"><label class="form-label fw-bold small text-uppercase text-muted">Срок</label><input type="date" name="deadline" class="form-control"></div>
                    </div>
                    <div class="mb-3"><label class="form-label fw-bold small text-uppercase text-muted">Содержание</label><textarea name="content" class="form-control" rows="6" required></textarea></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                    <button type="submit" name="is_draft" value="1" class="btn btn-outline-primary">Черновик</button>
                    <button type="submit" class="btn btn-primary">На утверждение</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}'''

ORDER_DETAILS_TEMPLATE = '''{% extends "base.html" %}
{% block title %}{{ order.title }} - ЭДО ЛДПР{% endblock %}
{% block content %}
<a href="/orders" class="btn btn-outline-secondary btn-sm mb-3"><i class="bi bi-arrow-left"></i> Назад</a>
<div class="row">
    <div class="col-md-8">
        <div class="card p-4 mb-4">
            <div class="d-flex justify-content-between mb-3">
                <div><span class="badge bg-primary mb-2">Р №{{ order.id[:8] }}</span><h3 class="fw-bold">{{ order.title }}</h3></div>
                <span class="badge badge-status {% if order.status in ['Утверждено','Закрыто'] %}bg-success{% elif order.status == 'Отклонено' %}bg-danger{% elif order.status == 'На утверждении' %}bg-warning text-dark{% else %}bg-primary{% endif %}">{{ order.status }}</span>
            </div>
            <div class="row mb-3 py-3 border-top border-bottom">
                <div class="col-md-3"><small class="text-muted text-uppercase fw-bold d-block" style="font-size:0.6rem;">Автор</small><strong>{{ order.creator_name }}</strong></div>
                <div class="col-md-3"><small class="text-muted text-uppercase fw-bold d-block" style="font-size:0.6rem;">Срок</small><strong>{{ order.deadline or 'Не указан' }}</strong></div>
                <div class="col-md-3"><small class="text-muted text-uppercase fw-bold d-block" style="font-size:0.6rem;">Приоритет</small><strong>{{ order.priority }}</strong></div>
                <div class="col-md-3"><small class="text-muted text-uppercase fw-bold d-block" style="font-size:0.6rem;">Создано</small><strong>{{ order.created_at[:10] }}</strong></div>
            </div>
            <h6 class="fw-bold text-uppercase text-muted small mb-3">Текст распоряжения</h6>
            <div class="bg-light p-3 rounded" style="white-space:pre-wrap;">{{ order.content }}</div>
            {% if order.result %}
            <div class="mt-4 p-3 bg-success bg-opacity-10 rounded border border-success border-opacity-25">
                <h6 class="text-success fw-bold"><i class="bi bi-check-circle-fill"></i> Результат выполнения</h6>
                <div style="white-space:pre-wrap;">{{ order.result.content }}</div>
                <small class="text-muted mt-2 d-block">Подано: {{ order.result.submittedAt[:16] }}</small>
            </div>
            {% endif %}
        </div>
        <div class="card p-4">
            <h5 class="fw-bold mb-3"><i class="bi bi-clock-history me-2"></i>История</h5>
            {% for item in history %}
            <div class="d-flex mb-3">
                <div class="me-3"><div class="bg-primary rounded-circle d-inline-flex align-items-center justify-content-center text-white" style="width:28px;height:28px;font-size:0.7rem;"><i class="bi bi-arrow-repeat"></i></div></div>
                <div><strong>{{ item.action }}</strong><br><small class="text-muted">{{ item.details or '' }}</small><br><small class="text-muted" style="font-size:0.7rem;">{{ item.user_name }} - {{ item.created_at }}</small></div>
            </div>
            {% endfor %}
        </div>
    </div>
    <div class="col-md-4">
        <div class="card p-4">
            <h5 class="fw-bold mb-3">Действия</h5>
            {% if current_user.role == 'head_central' and order.status == 'На утверждении' %}
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="Утверждено"><button class="btn btn-success w-100 mb-2"><i class="bi bi-check-circle"></i> Утвердить</button></form>
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="Отклонено"><input type="text" name="comment" class="form-control form-control-sm mb-2" placeholder="Причина отклонения"><button class="btn btn-danger w-100"><i class="bi bi-x-circle"></i> Отклонить</button></form>
            {% endif %}
            {% if current_user.role == 'secretary' and order.status == 'Утверждено' %}
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="В отделе"><select name="department_id" class="form-select form-select-sm mb-2" required><option value="">Выберите отдел...</option>{% for d in departments %}<option value="{{ d.id }}">{{ d.name }}</option>{% endfor %}</select><button class="btn btn-primary w-100"><i class="bi bi-building"></i> Назначить отдел</button></form>
            {% endif %}
            {% if current_user.role == 'head_department' and order.status == 'В отделе' %}
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="Назначен исполнитель"><select name="executor_id" class="form-select form-select-sm mb-2" required><option value="">Выберите исполнителя...</option>{% for u in dept_users %}<option value="{{ u.uid }}">{{ u.full_name }}</option>{% endfor %}</select><button class="btn btn-primary w-100"><i class="bi bi-person-check"></i> Назначить</button></form>
            {% endif %}
            {% if current_user.role == 'executor' and order.status == 'Назначен исполнитель' and order.assigned_executor_id == current_user.uid %}
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="В работе"><button class="btn btn-primary w-100"><i class="bi bi-play-circle"></i> Взять в работу</button></form>
            {% endif %}
            {% if current_user.role == 'executor' and order.status == 'В работе' and order.assigned_executor_id == current_user.uid %}
            <form method="POST" action="/orders/{{ order.id }}/submit"><textarea name="result_content" class="form-control form-control-sm mb-2" rows="4" placeholder="Опишите результат выполнения..." required></textarea><button class="btn btn-success w-100"><i class="bi bi-check-circle"></i> Сдать работу</button></form>
            {% endif %}
            {% if current_user.role == 'head_department' and order.status == 'Готово к проверке' %}
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="Подтверждено"><button class="btn btn-success w-100 mb-2"><i class="bi bi-check-circle"></i> Подтвердить</button></form>
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="На доработке"><input type="text" name="comment" class="form-control form-control-sm mb-2" placeholder="Причина доработки"><button class="btn btn-warning w-100"><i class="bi bi-arrow-counterclockwise"></i> На доработку</button></form>
            {% endif %}
            {% if current_user.role == 'head_central' and order.status == 'Подтверждено' %}
            <form method="POST" action="/orders/{{ order.id }}/status"><input type="hidden" name="status" value="Закрыто"><button class="btn btn-success w-100"><i class="bi bi-check-circle"></i> Закрыть</button></form>
            <form method="POST" action="/orders/{{ order.id }}/status" class="mt-2"><input type="hidden" name="status" value="На доработке"><input type="text" name="comment" class="form-control form-control-sm mb-2" placeholder="Причина доработки"><button class="btn btn-warning w-100"><i class="bi bi-arrow-counterclockwise"></i> На доработку</button></form>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}'''

DEPARTMENT_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Мой отдел - ЭДО ЛДПР{% endblock %}
{% block content %}
<h2 class="fw-bold mb-4"><i class="bi bi-building me-2"></i>Мой отдел</h2>
{% if department %}
<div class="card p-4 mb-4">
    <h4 class="fw-bold">{{ department.name }}</h4>
    <p class="text-muted">Руководитель: {{ department.head_name or 'Не назначен' }}</p>
</div>
<div class="row">
    <div class="col-md-6">
        <div class="card p-4">
            <h5 class="fw-bold mb-3">Сотрудники отдела</h5>
            {% if users %}
            <div class="list-group">
                {% for u in users %}
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div><strong>{{ u.full_name }}</strong><br><small class="text-muted">{{ u.role }}</small></div>
                    <span class="badge bg-primary">{{ u.email }}</span>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p class="text-muted">Нет сотрудников</p>
            {% endif %}
        </div>
    </div>
    <div class="col-md-6">
        <div class="card p-4">
            <h5 class="fw-bold mb-3">Распоряжения отдела</h5>
            {% if orders %}
            <div class="list-group">
                {% for o in orders %}
                <a href="/orders/{{ o.id }}" class="list-group-item list-group-item-action">
                    <div class="d-flex justify-content-between">
                        <strong>{{ o.title }}</strong>
                        <span class="badge badge-status {% if o.status in ['Утверждено','Закрыто'] %}bg-success{% elif o.status == 'Отклонено' %}bg-danger{% elif o.status == 'На утверждении' %}bg-warning text-dark{% else %}bg-primary{% endif %}">{{ o.status }}</span>
                    </div>
                    <small class="text-muted">{{ o.created_at[:10] }}</small>
                </a>
                {% endfor %}
            </div>
            {% else %}
            <p class="text-muted">Нет распоряжений</p>
            {% endif %}
        </div>
    </div>
</div>
{% else %}
<div class="alert alert-warning">Отдел не найден</div>
{% endif %}
{% endblock %}'''

ADMIN_DEPARTMENTS_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Управление отделами - ЭДО ЛДПР{% endblock %}
{% block content %}
<h2 class="fw-bold mb-4"><i class="bi bi-building me-2"></i>Управление отделами</h2>
<div class="card p-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h5 class="fw-bold mb-0">Все отделы</h5>
        <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addDeptModal"><i class="bi bi-plus-lg"></i> Добавить отдел</button>
    </div>
    {% if departments %}
    <div class="table-responsive">
        <table class="table table-hover">
            <thead><tr><th>Название</th><th>Руководитель</th><th>Действия</th></tr></thead>
            <tbody>
                {% for d in departments %}
                <tr>
                    <td><strong>{{ d.name }}</strong></td>
                    <td>{{ d.head_name or 'Не назначен' }}</td>
                    <td><a href="/department/{{ d.id }}" class="btn btn-sm btn-outline-primary"><i class="bi bi-eye"></i> Просмотр</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <p class="text-muted text-center py-4">Нет отделов</p>
    {% endif %}
</div>
<div class="modal fade" id="addDeptModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header"><h5 class="modal-title">Добавить отдел</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <form method="POST" action="/department/create">
                <div class="modal-body"><div class="mb-3"><label class="form-label">Название отдела</label><input type="text" name="name" class="form-control" required></div></div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}'''

ADMIN_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Администрирование - ЭДО ЛДПР{% endblock %}
{% block content %}
<h2 class="fw-bold mb-4"><i class="bi bi-shield-lock me-2"></i>Администрирование</h2>
<div class="row">
    <div class="col-12 mb-4">
        <div class="card p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="fw-bold mb-0">Пользователи</h5>
                <div>
                    <span class="badge bg-primary me-2">{{ users|length }} пользователей</span>
                    <button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addUserModal"><i class="bi bi-plus-lg"></i> Добавить</button>
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead><tr><th>ФИО</th><th>Логин</th><th>Роль</th><th>Email</th><th>Отдел</th><th>Действия</th></tr></thead>
                    <tbody>
                        {% for u in users %}
                        <tr>
                            <td><strong>{{ u.full_name }}</strong></td>
                            <td>{{ u.username }}</td>
                            <td><span class="badge bg-secondary">{{ u.role }}</span></td>
                            <td>{{ u.email }}</td>
                            <td>{% for d in departments %}{% if d.id == u.department_id %}{{ d.name }}{% endif %}{% endfor %}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#editUser{{ u.uid }}"><i class="bi bi-pencil"></i></button>
                                <form method="POST" action="/admin/users/{{ u.uid }}/delete" class="d-inline" onsubmit="return confirm('Удалить пользователя?')">
                                    <button type="submit" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
<div class="row">
    <div class="col-md-6 mb-4">
        <div class="card p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="fw-bold mb-0">Отделы</h5>
                <span class="badge bg-primary">{{ departments|length }}</span>
            </div>
            <div class="table-responsive">
                <table class="table table-sm table-hover">
                    <thead><tr><th>Название</th><th>Руководитель</th><th>Действия</th></tr></thead>
                    <tbody>
                        {% for d in departments %}
                        <tr>
                            <td>{{ d.name }}</td>
                            <td>{% for u in users %}{% if u.uid == d.head_id %}{{ u.full_name }}{% endif %}{% endfor %}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" data-bs-toggle="modal" data-bs-target="#setHead{{ d.id }}"><i class="bi bi-person-badge"></i> Назначить</button>
                                <form method="POST" action="/admin/departments/{{ d.id }}/delete" class="d-inline" onsubmit="return confirm('Удалить отдел?')">
                                    <button type="submit" class="btn btn-sm btn-outline-danger"><i class="bi bi-trash"></i></button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
<div class="modal fade" id="addUserModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header"><h5 class="modal-title">Добавить пользователя</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <form method="POST" action="/admin/users/create">
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6 mb-3"><label class="form-label">ФИО</label><input type="text" name="full_name" class="form-control" required></div>
                        <div class="col-md-6 mb-3"><label class="form-label">Логин</label><input type="text" name="username" class="form-control" required></div>
                        <div class="col-md-6 mb-3"><label class="form-label">Email</label><input type="email" name="email" class="form-control" required></div>
                        <div class="col-md-6 mb-3"><label class="form-label">Пароль</label><input type="password" name="password" class="form-control" required></div>
                        <div class="col-md-6 mb-3"><label class="form-label">Роль</label>
                            <select name="role" class="form-select">
                                <option value="admin">Администратор</option>
                                <option value="secretary">Секретарь</option>
                                <option value="head_central">Руководитель ЦА</option>
                                <option value="head_department">Начальник отдела</option>
                                <option value="assistant">Помощник</option>
                                <option value="executor" selected>Исполнитель</option>
                            </select>
                        </div>
                        <div class="col-md-6 mb-3"><label class="form-label">Отдел</label>
                            <select name="department_id" class="form-select"><option value="">Без отдела</option>{% for d in departments %}<option value="{{ d.id }}">{{ d.name }}</option>{% endfor %}</select>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% for u in users %}
<div class="modal fade" id="editUser{{ u.uid }}" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header"><h5 class="modal-title">Редактировать {{ u.full_name }}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <form method="POST" action="/admin/users/{{ u.uid }}/edit">
                <div class="modal-body">
                    <div class="mb-3"><label class="form-label">ФИО</label><input type="text" name="full_name" class="form-control" value="{{ u.full_name }}" required></div>
                    <div class="mb-3"><label class="form-label">Email</label><input type="email" name="email" class="form-control" value="{{ u.email }}" required></div>
                    <div class="mb-3"><label class="form-label">Роль</label>
                        <select name="role" class="form-select">
                            <option value="admin" {% if u.role == 'admin' %}selected{% endif %}>Администратор</option>
                            <option value="secretary" {% if u.role == 'secretary' %}selected{% endif %}>Секретарь</option>
                            <option value="head_central" {% if u.role == 'head_central' %}selected{% endif %}>Руководитель ЦА</option>
                            <option value="head_department" {% if u.role == 'head_department' %}selected{% endif %}>Начальник отдела</option>
                            <option value="assistant" {% if u.role == 'assistant' %}selected{% endif %}>Помощник</option>
                            <option value="executor" {% if u.role == 'executor' %}selected{% endif %}>Исполнитель</option>
                        </select>
                    </div>
                    <div class="mb-3"><label class="form-label">Отдел</label>
                        <select name="department_id" class="form-select">
                            <option value="" {% if not u.department_id %}selected{% endif %}>Без отдела</option>
                            {% for d in departments %}<option value="{{ d.id }}" {% if d.id == u.department_id %}selected{% endif %}>{{ d.name }}</option>{% endfor %}
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                    <button type="submit" class="btn btn-primary">Сохранить</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endfor %}
{% for d in departments %}
<div class="modal fade" id="setHead{{ d.id }}" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header"><h5 class="modal-title">Назначить руководителя: {{ d.name }}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
            <form method="POST" action="/admin/departments/{{ d.id }}/set_head">
                <div class="modal-body">
                    <div class="mb-3"><label class="form-label">Выберите руководителя</label>
                        <select name="head_id" class="form-select" required>
                            <option value="">-- Выберите --</option>
                            {% for u in users %}{% if u.role == 'head_department' %}<option value="{{ u.uid }}">{{ u.full_name }}</option>{% endif %}{% endfor %}
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
                    <button type="submit" class="btn btn-primary">Назначить</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endfor %}
{% endblock %}'''

TEMPLATES = {
    'base.html': BASE_TEMPLATE,
    'login.html': LOGIN_TEMPLATE,
    'dashboard.html': DASHBOARD_TEMPLATE,
    'orders.html': ORDERS_TEMPLATE,
    'order_details.html': ORDER_DETAILS_TEMPLATE,
    'department.html': DEPARTMENT_TEMPLATE,
    'admin_departments.html': ADMIN_DEPARTMENTS_TEMPLATE,
    'admin.html': ADMIN_TEMPLATE,
}
