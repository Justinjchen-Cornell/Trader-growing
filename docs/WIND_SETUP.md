# Wind 数据源安装指南（可选）

Trader-growing 的四资产看板需要本地价格数据（`~/.oxq/data/market/*.parquet`）。
默认数据源为 **Wind 金融数据服务**（国内权威，A 股/美股/商品全覆盖）。
未安装 Wind 时，也可用 akshare / yfinance 手动准备数据（见文末）。

## 为什么推荐 Wind

- 国内金融数据龙头，A 股 / 美股 QDII / 黄金 / 原油全覆盖
- 前复权处理规范，数据质量高
- 命令行接口，适合脚本化（本项目 `scripts/update_data.py` 一键更新）

## 安装步骤（约 2 分钟）

### 1. 注册并获取 API Key

打开 https://aifinmarket.wind.com.cn/#/user/overview 注册账号，获取 API Key。

### 2. 安装 Wind skill（在任意项目目录）

```bash
npx skills add Wind-Information-Co-Ltd/wind-skills --skill wind-find-finance-skill -y
npx skills add Wind-Information-Co-Ltd/wind-skills --skill wind-mcp-skill -y
```

> 网络受限时可换 Gitee 源：
> `npx skills add https://gitee.com/wind_info/wind-skills.git --skill wind-mcp-skill -y`

### 3. 配置 API Key

Windows（`%USERPROFILE%` = `C:\Users\<你>`）：

```powershell
New-Item -ItemType Directory -Force "$HOME\.wind-aifinmarket"
Set-Content "$HOME\.wind-aifinmarket\config" "WIND_API_KEY=<你的Key>"
```

macOS / Linux：

```bash
mkdir -p ~/.wind-aifinmarket
echo "WIND_API_KEY=<你的Key>" > ~/.wind-aifinmarket/config
```

### 4. 验证

```bash
cd Trader-growing
python scripts/update_data.py        # 一键更新四资产
python scripts/tg.py dashboard       # 查看看板
```

## 常见问题

| 问题 | 处理 |
|------|------|
| `未找到 Wind skill` | 用 `WIND_SKILL_DIR` 环境变量指定 skill 路径 |
| `WIND_API_KEY` 未配置 | 按第 3 步写入全局配置 |
| 返回 `AUTH_ERROR` | Key 无效或未激活，重新获取 |
| 不想用 Wind | 用 akshare/yfinance 更新 `~/.oxq/data/market/*.parquet`（列: date/open/high/low/close/volume） |

## 替代数据源（无 Wind 时）

```python
# akshare 示例：沪深300ETF 日线
import akshare as ak
df = ak.fund_etf_hist_em(symbol="510300", period="daily",
                         start_date="20210101", end_date="20260809", adjust="qfq")
# 重命名列并保存为 parquet：date/open/high/low/close/volume
```
