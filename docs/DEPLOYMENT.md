# 给陈凌晗的部署步骤

本分支在v3.0基础上增加持久化适配，保留收藏筛选、统计、暗色模式和联系人链接。运行时代码不再使用/tmp数据库。

## 合并前先配置

1. 先从现有公网网站导出Excel备份。原临时数据不会自动迁移。
2. 登录原Vercel项目，在Storage/Marketplace连接PostgreSQL（如Neon或Supabase）。自行检查所选方案的条款及费用。
3. 在项目Environment Variables中设置DATABASE_URL，使用提供商给出的连接字符串，保留SSL参数。不要把密码提交GitHub或贴进博客。Production与Preview分别配置；Preview建议用独立测试数据库。
4. SEED_DEMO可设为0；需要四位虚拟联系人时设为1，空库重启会填充演示数据。
5. 配置好后再合并PR并重新部署。没有DATABASE_URL的Vercel实例会显示配置提示、API返回503，不会悄悄使用临时SQLite。
6. 检查/api/health：status=ok、storage=postgresql、persistent=true。导入备份一次，避免重复导入产生重复联系人。
7. 新增虚拟联系人，重新部署，再确认记录仍在；测试收藏、编辑、搜索和Excel导入导出。

## 本地与服务器

本地不设置DATABASE_URL时使用data/contacts.db。python app.py用于本机运行；正式服务器可使用waitress。compose.yaml提供SQLite持久数据卷方案，不能直接在Vercel运行Docker Compose。

## 当前交付状态

适配代码、SQLite自动测试、PostgreSQL CI配置、协作PR及版本材料由张晴涵委托Codex协助准备。线上数据库与Vercel配置交给陈凌晗，配置完成前不宣称线上持久化已验收。

.env.example仅作说明，程序不会自动读取.env文件。

参考：https://vercel.com/docs/storage
