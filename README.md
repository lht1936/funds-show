# 海外投资基金数据服务

基于 FastAPI 和 AkShare 构建的海外投资基金数据服务，提供 RESTful API 接口。

## 功能特性

- 🚀 FastAPI 框架，高性能异步 API
- 📊 基于 AkShare 获取海外投资基金数据
- 💾 SQLite 数据库存储
- ⏰ 定时任务自动更新数据
- 📖 自动生成 API 文档

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```env
DATABASE_URL=sqlite:///./fund_show.db
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true
```

### 运行服务

```bash
uvicorn main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 接口

- `GET /api/v1/funds` - 获取基金列表
- `GET /api/v1/funds/{fund_code}` - 获取基金详情
- `GET /api/v1/funds/{fund_code}/holdings` - 获取基金持仓
- `POST /api/v1/funds/update` - 手动触发数据更新

## 项目结构

```
repo/
├── config.py          # 配置管理
├── database.py        # 数据库连接
├── main.py            # 应用入口
├── models.py          # 数据模型
├── routers.py         # API 路由
├── schemas.py         # Pydantic 模型
├── services.py        # 业务逻辑
├── data_fetcher.py    # 数据获取
└── scheduler.py       # 定时任务
```

## 技术栈

- FastAPI - Web 框架
- SQLAlchemy - ORM
- AkShare - 数据源
- APScheduler - 定时任务
- Pydantic - 数据验证

## License

MIT
