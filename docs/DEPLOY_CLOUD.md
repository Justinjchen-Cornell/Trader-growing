# ☁️ 在线部署指南

本地版跑通后，想让别人也能在线访问？两个选择：

## 方案 A：Streamlit Community Cloud（推荐，真正在线跑应用）

免费、官方、push 自动部署。**需要一次 GitHub 授权**（约 2 分钟）：

1. 打开 https://share.streamlit.io （或 app.streamlit.cloud）并用 **GitHub 账号登录**
2. 点 **New app** → 选择仓库 `Justinjchen-Cornell/Trader-growing`
   - Branch: `master`，Main file: `app.py`，点 Deploy
3. 等待 1-2 分钟 → 得到网址 `https://trader-growing-你的名字.streamlit.app`
4. 以后每次 `git push`，云端**自动重新部署**

> ⚠️ 云端运行说明：
> - 首次打开会自动装依赖（requirements.txt）
> - 数据：云端是无状态的，需要你在应用内点「🎯 操作台 → 更新行情数据（akshare）」按钮拉取
> - 每个人的数据独立存在各自的浏览器会话里（streamlit 无状态 + data/ 不入库）
> - 更适合"演示给朋友看"；自己长期用还是本地版（数据全在本地）

## 方案 B：GitHub Pages 官网（本项目已配好）

- 仓库里已包含 `docs/index.html`（项目官网）+ `.github/workflows/pages.yml`（自动发布）
- 启用步骤（一次，约 30 秒）：
  1. GitHub 仓库 → **Settings → Pages**
  2. **Source** 选择 **GitHub Actions**
  3. 等 1 分钟，官网出现在 `https://justinjchen-cornell.github.io/Trader-growing/`
- 之后每次 push 自动更新官网（纯静态介绍页，不含应用本体）

## 建议组合

| 用途 | 用什么 |
|------|--------|
| 项目介绍页（给所有人看） | GitHub Pages 官网（B） |
| 在线体验应用（给朋友玩） | Streamlit Cloud（A） |
| 自己每天用 | 本地版（数据全在本地，最隐私） |
