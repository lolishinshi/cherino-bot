# Cherino Bot

用于管理 exloli 群组的 bot

## 功能
- 基本管理
  - /ban     - 封禁用户
  - /warn    - 警告用户
- 辅助管理
  - /report  - 举报用户
  - /admin   - 召唤管理
- 其他
  - /ping         - pong~
  - /settings     - 设置
  - /add_question - 快速添加问题
- 入群验证

## 部署

1. 创建 config.toml

```toml
# Telegram Bot Token
token = "xxxxxxx"
# 数据库 URL
db_url = "sqlite:///db.sqlite"
```

2. 创建数据库

```
touch db.sqlite
```

3. 使用 docker-compose 直接构建并启动

```shell
docker-compose up --build -d --force-recreate
```
