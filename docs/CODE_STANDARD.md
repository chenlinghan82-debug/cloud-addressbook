# 代码规范 Code Standard

本项目遵循 [PEP 8 —— Python 官方代码风格指南](https://peps.python.org/pep-0008/)，
JavaScript 部分参考 [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)。
在此基础上，本项目约定如下：

## Python（后端 `app.py`）

1. 缩进统一 4 空格；字符串统一使用双引号或单引号之一（本项目用单引号）。
2. 命名：函数与变量 `snake_case`，常量 `UPPER_SNAKE_CASE`（如 `DETAIL_TYPES`）。
3. 每个路由函数不超过 40 行，数据库读写与 Excel 解析拆分为独立函数。
4. 所有 SQL 使用参数化查询（`?` 占位符），禁止字符串拼接，防注入。
5. 对外接口统一返回 JSON；错误信息统一放在 `error` 字段并使用 4xx 状态码。

## JavaScript（前端 `static/js/app.js`）

1. 统一使用 ES6+：`const/let`、箭头函数、模板字符串。
2. 命名：函数与变量 `camelCase`，DOM 查询结果缓存于 `state`。
3. 所有用户输入渲染前必须经过 `escapeHtml`，防 XSS。
4. 网络请求统一走 `api()` 封装，错误统一 `toast` 提示。

## HTML / CSS

1. CSS 自定义属性（`:root` 变量）统一管理颜色、圆角、阴影。
2. 类名使用 BDD 式短横线命名（`contact-card`、`detail-row`）。
3. 页面在 640px 以下必须可用（响应式断点）。

## Git 提交规范

- 格式：`<type>(<scope>): <中文描述>`
- `type` 取值：`feat` 功能 / `fix` 修复 / `docs` 文档 / `chore` 杂项
- 每次提交只做一类事情，保证提交历史可读。
