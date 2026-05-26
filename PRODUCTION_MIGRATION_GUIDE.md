# 生产环境数据库迁移操作手册

**版本：** 1.0  
**日期：** 2026-05-26  
**迁移目标：** 添加视频翻译标签功能和性能优化索引

---

## 📌 迁移概述

本次迁移将完成以下操作：
1. 创建标签管理相关的两个新表
2. 将现有的 JSON 格式标签数据迁移到新表
3. 添加性能优化索引以提升历史记录查询速度

**预计停机时间：** 根据数据量，5分钟 - 2小时  
**可回滚：** ✅ 是（提供完整回滚方案）

---

## ⚠️ 重要提醒

1. **必须在低峰期执行**（建议凌晨 2:00-6:00）
2. **必须先备份数据库**（这是最后的保险）
3. **必须逐步执行**（不要跳过任何检查步骤）
4. **遇到错误立即停止**（不要强行继续）
5. **保持冷静**（所有操作都可以回滚）

---

## 📋 执行前准备清单

### 1. 环境准备

- [ ] 确认有生产数据库的完整访问权限
- [ ] 确认服务器上已安装 Python 3.8+
- [ ] 确认已安装 PostgreSQL 客户端工具（psql, pg_dump）
- [ ] 确认有足够的磁盘空间用于备份（至少是数据库大小的 2 倍）
- [ ] 准备好数据库连接信息：
  ```
  主机地址：_________________
  端口：_________________
  数据库名：_________________
  用户名：_________________
  密码：_________________
  ```

### 2. 代码准备

- [ ] 已将最新代码部署到生产服务器
- [ ] 确认 `backend/alembic/` 目录存在且包含以下文件：
  - `alembic.ini`
  - `alembic/env.py`
  - `alembic/versions/53addd06ac1a_baseline_existing_schema.py`
  - `alembic/versions/18e286700e23_create_video_translation_tag_tables.py`
  - `alembic/versions/4a7102af09c7_backfill_video_translation_tags.py`
  - `alembic/versions/a1b2c3d4e5f6_add_video_translation_tasks_indexes.py`

### 3. 通知准备

- [ ] 已通知相关团队成员维护时间
- [ ] 已在用户端显示维护公告（如适用）
- [ ] 已准备好紧急联系方式

---

## 🔍 步骤 1：数据库状态检查（预计 5 分钟）

### 1.1 连接到生产数据库

```bash
# 设置数据库连接环境变量（替换为实际值）
export PGHOST="your-db-host"
export PGPORT="5432"
export PGDATABASE="your-database"
export PGUSER="your-username"
export PGPASSWORD="your-password"

# 测试连接
psql -c "SELECT version();"
```

**预期结果：** 显示 PostgreSQL 版本信息

**如果失败：** 检查连接信息是否正确，网络是否可达

---

### 1.2 检查必需的表是否存在

```sql
-- 复制以下 SQL 到 psql 中执行
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('users', 'video_translation_tasks')
ORDER BY table_name;
```

**预期结果：** 应该显示两行
```
        table_name         
---------------------------
 users
 video_translation_tasks
```

**如果失败：** 数据库结构不完整，不能继续迁移

---

### 1.3 检查数据量（重要！决定执行时间）

```sql
-- 检查总记录数
SELECT 
    'video_translation_tasks' as table_name,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE tags IS NOT NULL AND tags <> '') as records_with_tags
FROM video_translation_tasks;
```

**记录结果：**
- 总记录数：_________ 条
- 有标签的记录：_________ 条

**时间预估：**
- < 1,000 条：预计 5-10 分钟
- 1,000-10,000 条：预计 15-30 分钟
- 10,000-100,000 条：预计 30-60 分钟
- > 100,000 条：预计 1-2 小时

---

### 1.4 检查表大小

```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('video_translation_tasks')) as total_size,
    pg_size_pretty(pg_relation_size('video_translation_tasks')) as table_size,
    pg_size_pretty(pg_indexes_size('video_translation_tasks')) as indexes_size;
```

**记录结果：**
- 表总大小：_________
- 数据大小：_________
- 索引大小：_________

---

### 1.5 检查是否已有标签表（不应该存在）

```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%translation_tag%';
```

**预期结果：** 无结果（0 rows）

**如果有结果：** 说明已经执行过迁移，需要先确认状态

---

### 1.6 检查是否已有相关索引（不应该存在）

```sql
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'video_translation_tasks' 
AND (indexname LIKE '%user_created%' OR indexname LIKE '%is_auto%');
```

**预期结果：** 无结果（0 rows）

**如果有结果：** 说明索引已存在，需要先确认状态

---

## 💾 步骤 2：备份数据库（预计 5-30 分钟）

### 2.1 创建备份目录

```bash
# 在服务器上创建备份目录
mkdir -p ~/db_backups
cd ~/db_backups

# 记录当前时间
date
```

---

### 2.2 执行完整备份（推荐）

```bash
# 完整备份（包含结构和数据）
pg_dump -h $PGHOST -U $PGUSER -d $PGDATABASE \
  -F c \
  -f backup_full_$(date +%Y%m%d_%H%M%S).dump

# 检查备份文件
ls -lh backup_full_*.dump
```

**预期结果：** 生成一个 .dump 文件，大小应该接近数据库大小

**记录备份文件名：** _________________________________

---

### 2.3 额外备份关键表（可选但推荐）

```bash
# 只备份将要修改的表
pg_dump -h $PGHOST -U $PGUSER -d $PGDATABASE \
  -t video_translation_tasks \
  -F c \
  -f backup_video_translation_tasks_$(date +%Y%m%d_%H%M%S).dump
```

---

### 2.4 验证备份

```bash
# 查看备份内容（不恢复）
pg_restore -l backup_full_*.dump | head -20
```

**预期结果：** 显示备份文件的内容列表

---

## 🚀 步骤 3：执行数据库迁移（预计 10-60 分钟）

### 3.1 准备迁移环境

```bash
# 进入后端目录
cd /path/to/your/backend

# 设置数据库连接（替换为实际值）
export DATABASE_URL="postgresql://user:password@host:port/database"

# 验证 alembic 配置
ls -la alembic/
ls -la alembic/versions/
```

**预期结果：** 显示 alembic 目录和 4 个迁移文件

---

### 3.2 初始化 Alembic（首次执行）

```bash
# 将数据库标记为 baseline 版本（不执行任何迁移）
alembic stamp 53addd06ac1a

# 验证当前版本
alembic current
```

**预期结果：** 显示
```
53addd06ac1a (head)
```

**如果失败：** 检查数据库连接和 alembic 配置

---

### 3.3 查看待执行的迁移

```bash
# 查看迁移历史
alembic history --verbose
```

**预期结果：** 显示 4 个迁移版本的链条

---

### 3.4 预览迁移 SQL（不实际执行）

```bash
# 生成 SQL 预览文件
alembic upgrade head --sql > migration_preview.sql

# 查看预览文件
less migration_preview.sql
```

**检查要点：**
- 是否有 CREATE TABLE 语句（应该有 2 个新表）
- 是否有 CREATE INDEX 语句（应该有多个索引）
- 是否有 INSERT 语句（回填数据）

---

### 3.5 执行迁移 - 第 1 步：创建标签表

```bash
# 执行到创建表的版本
alembic upgrade 18e286700e23

# 记录执行时间
date
```

**预期输出：**
```
INFO  [alembic.runtime.migration] Running upgrade 53addd06ac1a -> 18e286700e23, create video translation tag tables
```

**如果失败：** 
1. 记录错误信息
2. 不要继续执行
3. 跳转到"回滚步骤"

---

### 3.6 验证表创建

```sql
-- 检查新表是否创建成功
\dt *translation_tag*

-- 检查表结构
\d video_translation_tags
\d video_translation_task_tags
```

**预期结果：** 显示两个新表及其结构

**检查要点：**
- 表是否存在
- 字段是否完整
- 索引是否创建
- 外键约束是否存在

---

### 3.7 执行迁移 - 第 2 步：回填数据

```bash
# 执行数据回填
alembic upgrade 4a7102af09c7

# 记录执行时间
date
```

**预期输出：**
```
INFO  [alembic.runtime.migration] Running upgrade 18e286700e23 -> 4a7102af09c7, backfill video translation tags
```

**注意：** 这一步可能需要较长时间，取决于数据量

**如果失败：**
1. 记录错误信息
2. 检查是否是数据格式问题
3. 跳转到"回滚步骤"

---

### 3.8 验证数据回填

```sql
-- 检查回填的数据量
SELECT 
    (SELECT COUNT(*) FROM video_translation_tasks 
     WHERE tags IS NOT NULL AND tags <> '') as original_tasks_with_tags,
    (SELECT COUNT(DISTINCT task_id) FROM video_translation_task_tags) as migrated_tasks,
    (SELECT COUNT(*) FROM video_translation_tags) as total_tags,
    (SELECT COUNT(*) FROM video_translation_task_tags) as total_task_tag_links;
```

**预期结果：** 
- `original_tasks_with_tags` 应该等于或接近 `migrated_tasks`
- `total_tags` 应该 > 0
- `total_task_tag_links` 应该 >= `migrated_tasks`

**记录结果：**
- 原始有标签的任务：_________ 条
- 迁移后的任务：_________ 条
- 总标签数：_________ 个
- 总关联数：_________ 条

**如果数据不匹配：** 需要调查原因，可能需要回滚

---

### 3.9 执行迁移 - 第 3 步：创建性能索引

```bash
# 执行索引创建
alembic upgrade a1b2c3d4e5f6

# 记录执行时间
date
```

**预期输出：**
```
INFO  [alembic.runtime.migration] Running upgrade 4a7102af09c7 -> a1b2c3d4e5f6, add video translation tasks indexes for performance
```

**注意：** 这一步会锁表，可能需要较长时间

**如果失败：**
1. 记录错误信息
2. 检查是否是索引名冲突
3. 跳转到"回滚步骤"

---

### 3.10 验证索引创建

```sql
-- 检查索引是否创建成功
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename = 'video_translation_tasks'
AND (indexname LIKE '%user_created%' OR indexname LIKE '%is_auto%');
```

**预期结果：** 显示两个新索引
```
ix_video_translation_tasks_user_created
ix_video_translation_tasks_is_auto
```

---

### 3.11 最终验证

```bash
# 检查 alembic 版本
alembic current
```

**预期结果：**
```
a1b2c3d4e5f6 (head)
```

```sql
-- 完整性检查
SELECT 
    'alembic_version' as check_item,
    version_num as value
FROM alembic_version
UNION ALL
SELECT 
    'video_translation_tags',
    COUNT(*)::text
FROM video_translation_tags
UNION ALL
SELECT 
    'video_translation_task_tags',
    COUNT(*)::text
FROM video_translation_task_tags;
```

**记录最终结果：**
- Alembic 版本：_________________
- 标签表记录数：_________________
- 关联表记录数：_________________

---

## ✅ 步骤 4：应用功能测试（预计 10 分钟）

### 4.1 重启应用服务

```bash
# 根据实际部署方式重启应用
# 示例：
systemctl restart your-app-service
# 或
supervisorctl restart your-app
# 或
pm2 restart your-app
```

---

### 4.2 检查应用启动日志

```bash
# 查看最新日志
tail -f /path/to/your/app/logs/app.log
```

**检查要点：**
- 是否有数据库连接错误
- 是否有模型加载错误
- 是否有外键约束错误

---

### 4.3 测试关键接口

```bash
# 测试获取翻译历史（替换为实际 API 地址和认证信息）
curl -X GET "https://your-api.com/api/video-translation/tasks?page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  | jq .

# 测试创建任务（如果适用）
# ...
```

**预期结果：** 接口正常返回数据，无错误

---

### 4.4 数据库性能测试

```sql
-- 测试新索引的性能
EXPLAIN ANALYZE
SELECT * FROM video_translation_tasks
WHERE user_id = 1
ORDER BY created_at DESC
LIMIT 10;
```

**检查要点：**
- 是否使用了新创建的索引 `ix_video_translation_tasks_user_created`
- 执行时间是否合理（应该 < 100ms）

---

## 🎉 步骤 5：完成迁移

### 5.1 记录迁移信息

```bash
# 创建迁移记录文件
cat > migration_record_$(date +%Y%m%d_%H%M%S).txt <<EOF
迁移完成时间: $(date)
Alembic 版本: a1b2c3d4e5f6
数据量统计:
  - 原始任务数: [从步骤 1.3 填写]
  - 迁移标签数: [从步骤 3.8 填写]
  - 新增表: video_translation_tags, video_translation_task_tags
  - 新增索引: ix_video_translation_tasks_user_created, ix_video_translation_tasks_is_auto
备份文件: [从步骤 2.2 填写]
执行人: [你的名字]
EOF

cat migration_record_*.txt
```

---

### 5.2 清理临时文件

```bash
# 删除 SQL 预览文件
rm -f migration_preview.sql
```

---

### 5.3 通知相关人员

- [ ] 通知团队迁移已完成
- [ ] 更新维护公告（如适用）
- [ ] 在项目文档中记录迁移信息

---

## 🔄 回滚步骤（仅在出错时使用）

### 场景 1：迁移过程中出错

#### 如果在步骤 3.5（创建表）失败：

```bash
# 回滚到 baseline
alembic downgrade 53addd06ac1a

# 手动清理（如果需要）
psql -c "DROP TABLE IF EXISTS video_translation_task_tags CASCADE;"
psql -c "DROP TABLE IF EXISTS video_translation_tags CASCADE;"
```

#### 如果在步骤 3.7（回填数据）失败：

```bash
# 回滚到创建表之后
alembic downgrade 18e286700e23

# 清空数据
psql -c "TRUNCATE TABLE video_translation_task_tags CASCADE;"
psql -c "TRUNCATE TABLE video_translation_tags CASCADE;"
```

#### 如果在步骤 3.9（创建索引）失败：

```bash
# 回滚到回填数据之后
alembic downgrade 4a7102af09c7

# 手动删除索引（如果需要）
psql -c "DROP INDEX IF EXISTS ix_video_translation_tasks_user_created;"
psql -c "DROP INDEX IF EXISTS ix_video_translation_tasks_is_auto;"
```

---

### 场景 2：迁移完成后发现问题

#### 完全回滚到迁移前状态：

```bash
# 方式 1：使用 Alembic 回滚
alembic downgrade 53addd06ac1a

# 方式 2：手动清理
psql <<EOF
BEGIN;

-- 删除索引
DROP INDEX IF EXISTS ix_video_translation_tasks_user_created;
DROP INDEX IF EXISTS ix_video_translation_tasks_is_auto;

-- 删除表
DROP TABLE IF EXISTS video_translation_task_tags CASCADE;
DROP TABLE IF EXISTS video_translation_tags CASCADE;

-- 更新 alembic 版本
UPDATE alembic_version SET version_num = '53addd06ac1a';

COMMIT;
EOF
```

---

### 场景 3：数据损坏，需要从备份恢复

```bash
# 停止应用服务
systemctl stop your-app-service

# 恢复整个数据库
pg_restore -h $PGHOST -U $PGUSER -d $PGDATABASE \
  --clean \
  --if-exists \
  backup_full_[你的备份文件名].dump

# 重启应用服务
systemctl start your-app-service
```

**警告：** 这会丢失备份后的所有数据变更！

---

## 📞 故障排查

### 问题 1：连接数据库失败

**错误信息：** `could not connect to server` 或 `connection refused`

**解决方案：**
1. 检查数据库服务是否运行：`systemctl status postgresql`
2. 检查网络连接：`ping your-db-host`
3. 检查防火墙规则
4. 验证连接信息是否正确

---

### 问题 2：权限不足

**错误信息：** `permission denied` 或 `must be owner of table`

**解决方案：**
1. 确认使用的数据库用户有足够权限
2. 检查用户权限：
   ```sql
   SELECT current_user;
   SELECT has_database_privilege(current_database(), 'CREATE');
   ```
3. 如果需要，使用超级用户执行迁移

---

### 问题 3：外键约束失败

**错误信息：** `foreign key constraint fails` 或 `violates foreign key constraint`

**解决方案：**
1. 检查 `users` 表是否存在
2. 检查 `video_translation_tasks` 表是否存在
3. 检查数据完整性：
   ```sql
   SELECT COUNT(*) FROM video_translation_tasks WHERE user_id NOT IN (SELECT id FROM users);
   ```

---

### 问题 4：索引创建超时

**错误信息：** `timeout` 或长时间无响应

**解决方案：**
1. 检查数据库负载：`SELECT * FROM pg_stat_activity;`
2. 如果数据量很大，考虑使用 CONCURRENTLY 选项（需要修改迁移脚本）
3. 增加超时时间
4. 在更低峰期重试

---

### 问题 5：磁盘空间不足

**错误信息：** `No space left on device`

**解决方案：**
1. 检查磁盘空间：`df -h`
2. 清理不必要的文件
3. 如果是备份占用空间，可以将备份移到其他位置
4. 考虑扩展磁盘空间

---

## 📚 附录

### A. 快速命令参考

```bash
# 数据库连接
psql -h HOST -U USER -d DATABASE

# Alembic 常用命令
alembic current                    # 查看当前版本
alembic history                    # 查看迁移历史
alembic upgrade <version>          # 升级到指定版本
alembic downgrade <version>        # 降级到指定版本
alembic upgrade head               # 升级到最新版本
alembic downgrade base             # 降级到初始状态

# 数据库备份恢复
pg_dump -F c -f backup.dump        # 备份
pg_restore -d database backup.dump # 恢复
```

---

### B. 迁移版本说明

| 版本号 | 描述 | 操作 |
|--------|------|------|
| 53addd06ac1a | Baseline | 无操作，标记起点 |
| 18e286700e23 | 创建标签表 | 创建 2 个新表和 6 个索引 |
| 4a7102af09c7 | 回填数据 | 从 JSON 迁移到新表 |
| a1b2c3d4e5f6 | 性能索引 | 添加 2 个查询优化索引 |

---

### C. 数据库表结构

#### video_translation_tags（标签主表）
- `id` - 主键
- `user_id` - 用户 ID（外键）
- `name` - 标签名称
- `normalized_name` - 标准化名称（用于去重）
- `created_at` - 创建时间
- `updated_at` - 更新时间

#### video_translation_task_tags（任务-标签关联表）
- `id` - 主键
- `task_id` - 任务 ID（外键）
- `tag_id` - 标签 ID（外键）
- `created_at` - 创建时间

---

### D. 联系信息

**技术支持：** [填写技术负责人联系方式]  
**紧急联系：** [填写紧急联系方式]  
**文档版本：** 1.0  
**最后更新：** 2026-05-26

---

## ✅ 执行检查清单（打印后使用）

```
□ 步骤 1.1: 连接数据库成功
□ 步骤 1.2: 必需表存在
□ 步骤 1.3: 记录数据量
□ 步骤 1.4: 记录表大小
□ 步骤 1.5: 确认标签表不存在
□ 步骤 1.6: 确认索引不存在
□ 步骤 2.2: 完成数据库备份
□ 步骤 2.4: 验证备份成功
□ 步骤 3.2: 初始化 Alembic
□ 步骤 3.5: 创建标签表
□ 步骤 3.6: 验证表创建
□ 步骤 3.7: 回填数据
□ 步骤 3.8: 验证数据回填
□ 步骤 3.9: 创建索引
□ 步骤 3.10: 验证索引创建
□ 步骤 3.11: 最终验证
□ 步骤 4.1: 重启应用
□ 步骤 4.3: 测试接口
□ 步骤 5.1: 记录迁移信息
□ 步骤 5.3: 通知相关人员
```

---

**祝迁移顺利！** 🚀
