import sqlite3
import string
import random
from flask import Flask, render_template, request, redirect, url_for, g
import io
import os

app = Flask(__name__)
DATABASE = 'database.db'

# --- 数据库操作 ---

def get_db():
    """获取数据库连接"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # 让查询结果可以像字典一样访问
    return db

@app.teardown_appcontext
def close_connection(exception):
    """在应用上下文结束时关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """根据schema.sql初始化数据库"""
    with app.app_context():
        db = get_db()
        with io.open('schema.sql', 'r', encoding='utf-8') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- 核心功能 ---

def generate_short_code(length=6):
    """生成指定长度的随机短码"""
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        # 检查数据库中是否已存在该短码
        db = get_db()
        cursor = db.execute('SELECT short_code FROM links WHERE short_code = ?', (code,))
        if cursor.fetchone() is None:
            return code

# --- 路由（页面）定义 ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """主页：处理链接提交和展示结果"""
    if request.method == 'POST':
        original_url = request.form['url']
        if not original_url:
            return render_template('index.html', error="请输入一个有效的URL")
        
        # 检查URL是否已存在
        db = get_db()
        cursor = db.execute('SELECT short_code FROM links WHERE original_url = ?', (original_url,))
        existing = cursor.fetchone()
        
        if existing:
            short_code = existing['short_code']
        else:
            short_code = generate_short_code()
            db.execute('INSERT INTO links (original_url, short_code) VALUES (?, ?)',
                       (original_url, short_code))
            db.commit()

        short_url = url_for('redirect_to_url', short_code=short_code, _external=True)
        return render_template('index.html', short_url=short_url)

    return render_template('index.html')

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """重定向页面：根据短码查找原始URL并跳转"""
    db = get_db()
    cursor = db.execute('SELECT original_url FROM links WHERE short_code = ?', (short_code,))
    link = cursor.fetchone()
    
    if link:
        # 将原始链接传递给中转页模板
        return render_template('redirect_page.html', original_url=link['original_url'])
    else:
        # 如果链接不存在，显示404页面
        return render_template('404.html'), 404

# --- 应用启动 ---

# 使用 `flask init-db` 命令来初始化数据库
@app.cli.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    print('数据库已初始化完毕！')

if __name__ == '__main__':
    # 初始化数据库（如果不存在）
    if not os.path.exists(DATABASE):
        print("初始化数据库...")
        init_db()
        print("数据库初始化完成！")
    
    print("=" * 50)
    print("短链接转换工具")
    print("=" * 50)
    print("正在启动Web服务器...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 尝试自动打开浏览器
    try:
        import webbrowser
        import threading
        import time
        
        def open_browser():
            time.sleep(2)  # 等待服务器启动
            webbrowser.open('http://localhost:5000')
        
        threading.Thread(target=open_browser, daemon=True).start()
    except:
        pass  # 如果无法打开浏览器，继续运行
    
    # 启动Flask应用
    app.run(debug=False, host='0.0.0.0', port=5000) 