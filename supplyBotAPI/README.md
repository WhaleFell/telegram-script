# FastAPI Template

This repository is myself FastAPI Template.  
Help me improve development efficiency and learn English.  

~~我的英文很差,有些地方还是会写中文的!~~

## Feature

1. SQLalchemy
2. Docker support
3. Friendly folder structure
4. Vue3 support
5. Use `loguru` to replace `uvicorn` default logging.
6. Support Oauth2 login.

## Project Structurn

⚠ Modules uniformly use absolute `/ˈæb.sə.luːt/` imports.  
like `from routers import HelloWorld`

```text
- app // Project root path
  - routers // 路由 like vue components use 大写
    - __init__.py
    - index.py // handle `/` router
    - user.py // handle `user` router 
  
  - database // database create/update/read/delete SQLAlchemy
    - __init__.py
    - model.py // database model 数据库模型
    - curd.py // 数据库增改查删
    - connect.py // 连接

  - schemas /ˈskiː.mə/ n.图解.模式 // api response BaseModel API 数据模型
    - __init__.py
    - base.py
    - user.py

  - utils // 储存一些 helper funtion
    - custom_log.py // custom loguru

  - register // 储存一些注册到 APP 相关的东西
    - __init__.py
    - router.py // 路由
    - middleware.py // 中间件
    - exception.py // 异常
    - cors.py // 跨域
    
  - __init__.py // app 包入口
  - main.py // 入口文件
  - config.py // 配置

- logs // 日志文件夹

- pyproject.toml // 项目规范
- requirements.txt // 依赖
- Dockerfile
- README.md

```

## Installation and Setup

### Development

```shell
python -m venv ./venv

# Open Powershell Limited
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt --index-url=https://pypi.org/simple

uvicorn app.main:app --port 8000 --reload
```

or:

```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Reference

1. FastAPI best practices [https://github.com/zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
2. FastAPI offical document [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
3. Best Dockerfile: [https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker](https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker)
4. 相似的项目,最棒的模仿 [https://github.com/zxiaosi/vue3-fastapi/](https://github.com/zxiaosi/vue3-fastapi/)
5. FastAPI with Async SQLAlchemy: [https://github.com/rhoboro/async-fastapi-sqlalchemy/blob/main/app/db.py](https://github.com/rhoboro/async-fastapi-sqlalchemy/blob/main/app/db.py)
6. [https://stribny.name/blog/fastapi-asyncalchemy/](https://stribny.name/blog/fastapi-asyncalchemy/)
