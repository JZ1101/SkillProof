# Task Log

## Rules
- uv run for everything
- Modular: one file per pipeline step
- shit_test/ for throwaway scripts
- Concise code, no bloat
- All keys in .env (no export)
- Focus: backend first, risk-first ordering
- Scope: assessment only (no real-time correction)
- Model: Gemini 2.5 Pro (native video input, no frame extraction needed)
- Positioning: 先做"预评估/练习工具"，认证资质后续拿

---

## Task 0 — NVQ 官方标准整理
- **Method:** 调研 NVQ Level 2 Tiling + Painting & Decorating 评估标准，结构化为 JSON rubric
- **Purpose:** 评估质量的基础，没这个后面全是猜
- **Input:** NVQ/City & Guilds 公开评估 criteria
- **Output:** rubrics/tiling.json, rubrics/painting.json
- **Completeness:** 两个工种完整标准
- **Delivers:** Task 2 的前置
- **Future:** 更多工种标准

## Task 1 — 最小 AI 评估验证
- **Method:** 1个视频/照片 → Gemini 2.5 Pro → 看评估质量
- **Purpose:** 核心风险验证 — AI 到底能不能准确评估
- **Input:** 找一段 tiling/painting 视频 (YouTube)
- **Output:** shit_test/eval_test.py, 评估结果样本
- **Completeness:** 概念验证
- **Delivers:** Go/No-Go 决策
- **Future:** 无

## Task 2 — 项目脚手架 + 配置
- **Method:** uv init + FastAPI + pydantic-settings + .env
- **Purpose:** 项目基础
- **Input:** 无
- **Output:** 项目结构、config.py、main.py、.env.example
- **Completeness:** 基础设施
- **Delivers:** 无（前置）
- **Future:** Docker 化

## Task 3 — 文件上传 + 存储
- **Method:** FastAPI UploadFile → 本地存储
- **Purpose:** 接收工人照片/视频
- **Input:** 图片/视频文件
- **Output:** upload.py, /api/upload endpoint
- **Completeness:** 完整
- **Delivers:** D6
- **Future:** S3, 视频质量预检（光线/角度/稳定性）

## Task 4 — AI 评估 Pipeline
- **Method:** Gemini 2.5 Pro, 原生视频输入, 对标 NVQ 标准 rubric
- **Purpose:** 核心评估 — safety → technique → result quality, 引用具体条款
- **Input:** 视频/照片 + 任务类型 + rubrics/*.json
- **Output:** assessor.py, JSON 评分 (safety/technique/result 0-100) + 条款引用反馈
- **Completeness:** Tiling T1-T5 + Painting P1-P5
- **Delivers:** D7, D8
- **Future:** 多模型对比、置信度阈值、视频质量预检拒绝

## Task 5 — 评分聚合
- **Method:** Safety 30% + Technique 40% + Result 30%, 70% pass, safety 必须过
- **Purpose:** AI 原始评分 → 最终结果
- **Input:** Task 4 JSON
- **Output:** scorer.py, pass/fail + 反馈
- **Completeness:** 完整
- **Delivers:** D8
- **Future:** 分数校准

## Task 6 — 证书生成
- **Method:** ReportLab PDF + qrcode
- **Purpose:** 通过后生成可验证证书
- **Input:** 用户信息 + 分数 + cert_id
- **Output:** certificate.py, PDF + QR
- **Completeness:** 完整
- **Delivers:** D9
- **Future:** 3D 卡片前端展示

## Task 7 — 数据库持久化
- **Method:** SQLModel + SQLite (MVP)
- **Purpose:** 持久化评估数据
- **Input:** gendoc.md schema
- **Output:** models.py, database.py
- **Completeness:** 4 表
- **Delivers:** D10
- **Future:** Supabase

## Task 8 — API 路由整合
- **Method:** FastAPI router
- **Purpose:** 完整 REST API
- **Input:** 所有模块
- **Output:** /api/trades, /api/tasks, /api/upload, /api/assess, /api/certificate, /api/verify/{id}
- **Completeness:** MVP
- **Delivers:** 全部 backend
- **Future:** WebSocket, rate limiting

---

## 状态
- [ ] Task 0 — NVQ 标准整理
- [ ] Task 1 — AI 评估验证 (Go/No-Go)
- [ ] Task 2 — 脚手架
- [ ] Task 3 — 文件上传
- [ ] Task 4 — AI Pipeline
- [ ] Task 5 — 评分聚合
- [ ] Task 6 — 证书生成
- [ ] Task 7 — 数据库
- [ ] Task 8 — API 整合
