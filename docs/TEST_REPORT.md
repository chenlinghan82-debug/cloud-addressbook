# v3.1补充版验证

## 已执行

本机Python 3.13运行`python docs/selftest.py`：11项全部通过。`node --check static/js/app.js`通过。

GitHub Actions首个代码提交8b707a9对应运行：
https://github.com/qinghanz6/cloud-addressbook/actions/runs/43837115241

SQLite、PostgreSQL两组任务均成功。PostgreSQL使用GitHub Actions中独立的PostgreSQL 17服务和addressbook_test数据库，执行同一套回归。不是连接队友的线上数据库。

覆盖CRUD、多联系方式、收藏切换、跨字段搜索、Excel全部字段往返、公式字符串按文本导出、前导零、姓名列换位、零值、异常文件、导入回滚、非法JSON、上传大小限制、跨进程读取，以及Vercel缺少数据库配置时返回503且不创建本地数据库。

## 公开v3.0核查

网站可访问，首页为4人、2位收藏、12条联系方式。此前实际下载并解析线上Excel，得到4行联系人、电话1和电话2分列以及模板工作表，导出结构正确。

最新截图：blog/screenshots/github_latest_20261116.jpg、blog/screenshots/v3_home.jpg。

## 尚未验证

没有配置或重新部署原Vercel项目。完整线上新增、导入、收藏和编辑的浏览器演示未完成；Computer Use因不能可靠确认Windows浏览器网址而停止。本次不以旧版视频替代，也不把CI数据库测试说成线上持久化验收。
