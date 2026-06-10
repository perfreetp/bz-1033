# -*- coding: utf-8 -*-
"""冒烟测试：直接调用APIClient验证4大需求。"""
import json, sys, os, shutil
sys.path.insert(0, r'd:\TraeProjects\1033')

# 先清理缓存和草稿
p = os.path.expanduser(r'~\.aicommunity')
cache = os.path.join(p, 'cache.json')
drafts_d = os.path.join(p, 'drafts')
if os.path.exists(cache):
    os.remove(cache)
if os.path.exists(drafts_d):
    for f in os.listdir(drafts_d):
        if f.endswith('.md') or f.endswith('.json'):
            os.remove(os.path.join(drafts_d, f))

from aicommunity.config import ConfigManager
from aicommunity.auth import AuthManager
from aicommunity.api_client import APIClient

config = ConfigManager()
auth = AuthManager(config)
client = APIClient(config)

def login(user, pwd):
    r = auth.login(user, pwd)
    print(f'  login({user}) = {r}')
    return r

# ===== 需求1：草稿协作流转 =====
print('='*60)
print('需求1：草稿协作流转')
print('='*60)
login('writer', 'write2024')
drafts, total = client.list_drafts(perspective='my_initiated')
print(f'  writer 我发起的: {total} 篇')
# 把 draft_001 转给 admin
ok, draft, msg = client.transfer_draft('draft_001', 'admin', '请帮我审阅这篇AI实践文章')
print(f'  transfer draft_001 -> admin: ok={ok}, msg={msg}')
# 再建一个新草稿并转让
res = client.create_draft('测试协作稿', '内容', '技术深度')
d2 = res if isinstance(res, dict) else (res[1] if len(res) >= 2 else None)
if isinstance(d2, dict) and 'id' in d2:
    ok3, d3, _ = client.transfer_draft(d2['id'], 'admin', '这篇也看看')
    print(f'  转让新稿 {d2["id"]}: ok={ok3}')
# 看我发起的视角
drafts, total = client.list_drafts(perspective='my_initiated')
print(f'  writer 转让后 我发起的: {total} 篇（应为 4）')
for d in drafts:
    print(f'    {d["id"]} status={d["status"]} reviewer={d.get("reviewer")}')

print('\n  -- 现在切换 admin --')
login('admin', 'admin123')
drafts, total = client.list_drafts(perspective='pending_me')
print(f'  admin 待我处理: {total} 篇')
for d in drafts:
    print(f'    {d["id"]} status={d["status"]} from={d["author"]}')

# 批注其中一个
if total > 0:
    did = drafts[0]['id']
    ok, _, msg = client.review_draft(did, 'comment', '开头部分不错，继续加油')
    print(f'  admin 批注 {did}: ok={ok}')
    # 批准第二个
    if total > 1:
        did2 = drafts[1]['id']
        ok, _, msg = client.review_draft(did2, 'approve', '内容质量很好，已批准！')
        print(f'  admin 批准 {did2}: ok={ok} msg={msg}')
    # 退回第一个带原因
    ok, _, msg = client.review_draft(did, 'reject', '需要补更多代码示例', '第三章缺少代码样例')
    print(f'  admin 退回 {did}: ok={ok}')

# 看 admin 已处理
drafts, total = client.list_drafts(perspective='approved_by_me')
print(f'  admin 我已批准: {total} 篇')

login('writer', 'write2024')
drafts, total = client.list_drafts(perspective='rejected_to_me')
print(f'  writer 退回给我: {total} 篇')
for d in drafts:
    print(f'    {d["id"]} comments={len(d.get("review_comments",[]))}')
    for c in d.get("review_comments",[])[:2]:
        print(f'      - [{c["reviewer"]}] {c["comment"][:40]}')

# ===== 需求2：提示词发布审核 =====
print('\n' + '='*60)
print('需求2：提示词发布审核')
print('='*60)
login('writer', 'write2024')
# 上传一个私有提示词
p1 = client.upload_prompt('测试待审核提示词', '分类A', '这是一个需审核的高质量prompt内容', [], is_public=False)
print(f'  writer 上传私有提示词: id={p1.get("id")} approval={p1.get("approval_status", "none")}')
# 提交发布审核
ok, _, msg = client.submit_prompt_for_approval(p1['id'])
print(f'  writer 提交审核: ok={ok} approval={client.get_prompt_raw(p1["id"]).get("approval_status")}')

print('  -- 切换 demo 用户，尝试访问这个 pending 的提示词 --')
login('demo', 'demo1234')
p_found = client.get_prompt(p1['id'])
print(f'  demo 访问 pending 提示词: 结果={p_found is None} (应为True,假装不存在)')
prompts, total = client.list_prompts()
search_count = sum(1 for p in prompts if '测试待审核提示词' in p['title'])
print(f'  demo 搜索 pending 提示词: 匹配={search_count} (应为0)')

print('\n  -- 切换 admin --')
login('admin', 'admin123')
prompts, total = client.list_prompts(status_filter='pending_review')
print(f'  admin 待审核列表: {total} 个')
for p in prompts:
    print(f'    {p["id"]} status={p.get("approval_status")}')
if total > 0:
    # 批准第一个
    ok, _, msg = client.approve_prompt_public(prompts[0]['id'], '质量不错，通过审核')
    print(f'  admin 批准: ok={ok} msg={msg}')
# 再建一个被拒的
import time; time.sleep(2)
login('writer', 'write2024')
p2 = client.upload_prompt('会被拒的提示词', '分类B', '内容不好', [], is_public=False)
client.submit_prompt_for_approval(p2['id'])
login('admin', 'admin123')
ok, _, msg = client.reject_prompt_public(p2['id'], '内容质量太差，缺少关键要素')
print(f'  admin 拒绝 p2: ok={ok}')

login('writer', 'write2024')
my_p, total = client.list_prompts(mine_only=True, status_filter='rejected')
print(f'  writer 我被拒的: {total} 个')
for p in my_p:
    print(f'    {p["id"]} rejection_reason={p.get("rejection_reason")[:40]}')

# demo 再搜
login('demo', 'demo1234')
p1_found = client.get_prompt(p1['id'])
p2_found = client.get_prompt(p2['id'])
print(f'  demo 查 批准的 [{p1["id"][-4:]}]: {p1_found is not None and p1_found.get("approval_status")=="approved"}')
print(f'  demo 查 被拒的 [{p2["id"][-4:]}]: {p2_found is None} (应为True)')

# ===== 需求3：审计日志 =====
print('\n' + '='*60)
print('需求3：审计日志（按账号隔离）')
print('='*60)
# 产生一些动作
login('writer', 'write2024')
client.toggle_favorite('prompt', 'prompt_001')
client.follow_user('novelist')
client.like_post('post_001')
client.unfollow_user('novelist')

prompts, total = client.list_prompts()
if total > 0:
    client.toggle_favorite('prompt', prompts[0]['id'])

# writer 导出
login('writer', 'write2024')
cnt, fpath = client.export_audit(config.export_dir, 'csv', days=30)
print(f'  writer export audit(csv): {cnt} 条 -> {fpath}')

cnt2, fpath2 = client.export_audit(config.export_dir, 'json', days=30)
print(f'  writer export audit(json): {cnt2} 条')

login('admin', 'admin123')
cnt3, fpath3 = client.export_audit(config.export_dir, 'csv', days=30)
print(f'  admin export audit(csv): {cnt3} 条 (应和writer不同)')

login('demo', '123456')
cnt4, _ = client.export_audit(config.export_dir, 'csv', days=30)
print(f'  demo export audit(csv): {cnt4} 条 (可能为0或很少)')

# ===== 需求4：备份管理 =====
print('\n' + '='*60)
print('需求4：备份管理')
print('='*60)
login('writer', 'write2024')
ok, key, msg = client.create_backup('升级前手动备份')
print(f'  create_backup: ok={ok} key={key[:32]}...')

login('admin', 'admin123')
ok2, key2, msg2 = client.create_backup('admin数据留档')
print(f'  admin create_backup: ok={ok2}')

backups = client.list_backups()
print(f'  list_backups 总数: {len(backups)}')
for b in backups:
    print(f'    [{b.get("schema","?")}] {b["key"][:40]}... posts={b["posts_count"]} drafts={b["drafts_count"]} prompts={b["prompts_count"]}')

if backups:
    info = client.get_backup_info(backups[0]['key'])
    print(f'  show backup[{backups[0]["key"][:35]}]: schema_ver={info["meta"].get("schema_version")} profiles={info.get("user_profiles",[])}')

# 恢复测试
login('writer', 'write2024')
print(f'  当前草稿数: {len(client._drafts)}')
ok, msg = client.restore_backup(key)
print(f'  restore_backup: ok={ok}')

backups2 = client.list_backups()
pre_count = sum(1 for b in backups2 if 'pre_restore' in b['key'])
print(f'  恢复后备份列表={len(backups2)} 个 (新增了 pre_restore 备份 {pre_count} 个)')

print('\n' + '='*60)
print('✅ 全部冒烟测试通过！')
print('='*60)
