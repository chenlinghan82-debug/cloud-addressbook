# v3.1.0 双人协作与持久化适配

基于陈凌晗的v3.0（acc4935），保留原有收藏筛选、统计面板、深色模式和联系人链接。张晴涵通过Fork提交补充修改，由Codex协助实现与验证。

- 新增PostgreSQL连接适配，删除Vercel的临时SQLite回退；本地仍使用SQLite。
- 未配置DATABASE_URL时显式提示并返回503，避免把临时存储当作持久化。
- 修复Excel中英文表头、姓名列换位、零值处理、整批回滚及文本导出。
- 补充请求校验、上传限制、数据库连接关闭和前端转义。
- 新增11项隔离回归测试；GitHub Actions的SQLite和PostgreSQL两组均通过。
- 修订双人博客与贡献评价，替换图片占位符，附当前公网首页和最新GitHub提交截图。

协作PR：https://github.com/chenlinghan82-debug/cloud-addressbook/pull/1

本Release发布于qinghanz6的Fork，不表示队友原仓库已合并，也不表示现有Vercel网站已部署本版。请陈凌晗先备份原数据、配置DATABASE_URL，再合并部署，见docs/DEPLOYMENT.md。

完整v3.0前端操作视频尚未补成：浏览器控制因无法确认Windows当前网址而被工具停止。已有截图真实保留，原16秒演示不是完整功能视频；不得将旧版或接口测试录像冒充完整前端演示。
