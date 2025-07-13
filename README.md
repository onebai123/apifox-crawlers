# Apifox API文档自动抓取工具

这是一个独立的Web应用程序，用于自动抓取API文档网站的内容，下载markdown文件，并通过三阶段处理流程转换为适合导入Apifox的YAML格式文件。


## 运行截图

<img width="910" height="824" alt="image" src="https://github.com/user-attachments/assets/86a5487a-0ed9-4a42-81be-9f5c0228e90a" />
<img width="716" height="765" alt="image" src="https://github.com/user-attachments/assets/19f0c5a5-3bae-4814-aa23-f7a06abc680d" />

## 功能特性

- 🌐 **Web界面操作** - 简洁的HTML界面，输入API文档URL即可开始处理
- 📥 **自动下载** - 自动下载llms.txt文件并解析API Docs部分的链接
- 🔄 **并发处理** - 支持多线程并发下载MD文件，提高处理效率
- 📊 **实时进度** - 实时显示处理进度和状态信息
- 🎯 **三阶段处理** - 规范化的数据处理流程
- 📁 **智能分类** - 基于内容特征自动分类API接口
- ✅ **格式验证** - 确保生成的YAML文件符合OpenAPI 3.1.0规范

## 项目结构

```
apifox/
├── app.py                 # Flask后端服务器
├── requirements.txt       # Python依赖包
├── README.md             # 项目说明文档
├── static/               # 静态资源
│   ├── css/
│   │   └── style.css     # 样式文件
│   └── js/
│       └── app.js        # 前端JavaScript
├── templates/            # HTML模板（如果使用）
├── utils/                # 工具模块
│   ├── __init__.py
│   ├── downloader.py     # 下载器模块
│   ├── parser.py         # 解析器模块
│   └── processor.py      # 处理器模块
└── data/                 # 数据目录
    ├── 01/               # 阶段1：原始数据
    │   └── md/           # 原始MD文件
    ├── 02/               # 阶段2：清洗数据
    │   ├── md/           # 清洗后的MD文件
    │   └── yml/          # 转换后的YAML文件
    └── final/            # 阶段3：最终合并文件
```

## 三阶段处理流程

### 阶段1：原始数据存储
- 下载llms.txt文件
- 解析API Docs部分的链接（忽略Docs部分）
- 并发下载所有MD文件到`data/01/md/`目录

### 阶段2：数据清洗和转换
- 从MD文件中提取YAML内容
- 验证YAML格式的有效性
- 清洗MD内容（移除多余空行、格式化等）
- 保存清洗后的MD文件到`data/02/md/`
- 保存提取的YAML文件到`data/02/yml/`

### 阶段3：最终合并
- 根据API内容特征进行智能分类
- 合并同类API到单个YAML文件
- 生成符合OpenAPI 3.1.0规范的最终文件
- 保存到`data/final/`目录


## 快速启动

### 方式一：本地Python启动（Windows）

**一键启动脚本**：双击运行 [`start.bat`](start.bat) 文件

或手动执行以下步骤：

```bash
# 1. 安装依赖（使用清华镜像源加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 2. 启动服务
python app.py

# 3. 访问应用
# 浏览器自动打开 http://localhost:5000
```

### 方式二：Docker Compose启动（推荐）

```bash
# 1. 构建并启动服务
docker-compose up --build

# 2. 后台运行
docker-compose up --build -d

# 3. 访问应用
# 打开浏览器访问: http://localhost:5000

# 4. 停止服务
docker-compose down
```

### 使用步骤
1. 在输入框中输入API文档URL（如：`https://api-gpt-ge.apifox.cn/`）
2. 点击"开始处理"按钮
3. 观察实时进度显示
4. 处理完成后，在`data/final/`目录中获取最终的YAML文件

## API接口

### POST /api/start
开始处理API文档
- **参数**: `{"url": "https://api-gpt-ge.apifox.cn/"}`
- **返回**: `{"task_id": "uuid", "status": "started"}`

### GET /api/progress/{task_id}
获取处理进度
- **返回**: `{"stage": 1, "progress": 50, "message": "正在下载..."}`

### GET /api/result/{task_id}
获取处理结果
- **返回**: `{"status": "completed", "files": [...], "stats": {...}}`

## 技术栈

- **后端**: Flask + Python 3.7+
- **前端**: HTML5 + CSS3 + JavaScript (ES6+)
- **数据处理**: PyYAML + 正则表达式
- **并发处理**: ThreadPoolExecutor
- **HTTP客户端**: requests

## 注意事项

1. **网络连接**: 确保能够访问目标API文档网站
2. **磁盘空间**: 处理大量文件时需要足够的磁盘空间
3. **内存使用**: 并发下载时会占用一定内存
4. **文件权限**: 确保对data目录有读写权限
5. **Docker环境**: 使用Docker时确保Docker和Docker Compose已正确安装

## 错误处理

- 网络连接失败时会自动重试
- 无效的YAML文件会被跳过并记录
- 处理过程中的错误会在界面上显示
- 详细的错误日志会输出到控制台

## 故障排除

### Docker相关问题

#### 1. 端口占用
```bash
# 检查端口占用
netstat -tulpn | grep :5000

# 或使用其他端口
docker-compose up --build -p 8080:5000
```

#### 2. 权限问题
```bash
# Linux/Mac 下确保数据目录权限
sudo chown -R $USER:$USER ./data
chmod -R 755 ./data
```

#### 3. 容器无法启动
```bash
# 查看容器日志
docker-compose logs apifox-tool

# 重新构建镜像
docker-compose build --no-cache
```

#### 4. 数据目录问题
```bash
# 手动创建数据目录
mkdir -p data/{01/md,02/{md,yml},final/md}
```

### Python环境问题

#### 1. 依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 2. 模块导入错误
```bash
# 确保在项目根目录
export PYTHONPATH=$PWD:$PYTHONPATH
python app.py
```

### 常见错误解决

1. **"Address already in use"**: 端口5000被占用，修改端口或停止占用进程
2. **"Permission denied"**: 检查文件权限，特别是data目录
3. **"Module not found"**: 检查Python路径和依赖安装
4. **"Connection refused"**: 检查网络连接和防火墙设置

## 扩展功能

可以通过修改以下文件来扩展功能：

- `utils/parser.py` - 修改链接解析逻辑
- `utils/processor.py` - 修改分类和合并逻辑
- `static/js/app.js` - 修改前端交互逻辑
- `static/css/style.css` - 修改界面样式

## 许可证

本项目基于现有成功项目的核心逻辑开发，仅供学习和研究使用。

## 更新日志

### v1.0.0 (2025-01-13)
- 初始版本发布
- 实现三阶段处理流程
- 支持Web界面操作
- 集成现有项目的成功经验
