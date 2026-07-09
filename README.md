# 📊 ETF 资金流向追踪

> 每日自动追踪沪深交易所 ETF 份额与资产规模变化，透视"国家队"资金动向

[![数据更新](https://img.shields.io/badge/数据-每日16:40自动更新-blue)](#)
[![托管平台](https://img.shields.io/badge/托管-GitHub%20Pages-brightgreen)](#)
[![可视化](https://img.shields.io/badge/可视化-ECharts%205-orange)](#)
[![数据源](https://img.shields.io/badge/数据源-akshare-purple)](#)

---

## 一、项目简介

本项目每日自动从上海证券交易所和深圳证券交易所抓取 ETF 份额日报，按**标的**汇总（同一指数的不同基金公司产品合并），通过 GitHub Actions 定时更新，并以可交互的 Web 仪表盘展示份额与资产规模（AUM）的历史走势。

**核心用途**：

- 追踪宽基/科创/商品/行业主题 ETF 的资金净流入与净流出
- 辅助判断"国家队"对宽基指数（如上证50、沪深300、中证A500）的持仓动向
- 通过强度热图直观看到哪些品类、哪些时段在持续吸金/失血

**线上访问**：[https://digger-yu.github.io/etf-shares-tracker/](https://digger-yu.github.io/etf-shares-tracker/)

---

## 二、核心功能

### 1. 顶部 KPI 卡片

- **全市场总份额**、**全市场总资产规模**、**当日净流入**、**期内累计净流入**
- 涨红跌绿（中国股市惯例）
- 一键切换"资产规模 / 份额"两种口径

### 2. 累计净流入排行（瀑布图）

- 按标的横向对比累计净流入金额
- 自动按升序/降序排列，红涨绿跌
- 排名标题根据所选指标动态切换（AUM → 累计资产规模变化排行；shares → 累计份额变化排行）

### 3. 资产规模结构与走势（强度热图 + 辅图）

- **强度热图**：品类 × 时间矩阵，颜色深 = 规模大，支持 `占比(%)` / `绝对值` 双模式，支持 `按天/按周/按月` 三种粒度
- **每日净变化贡献 Top 10 堆叠柱状**：一眼看出当日资金主要流向哪些品类
- **小型多图（Small Multiples）**：每个标的单独一张迷你走势图，点击可放大查看

### 4. 每日净变化瀑布图

- 按日期维度展示所有标的的净流入/流出
- 颜色深度反映规模，鼠标悬停查看当日明细

### 5. 详细数据表（带 Sparkline）

- 列点击排序
- 行末内嵌 Sparkline 迷你趋势图
- 表头粘性定位，滚动友好

### 6. 分类筛选

- 6 个一级分类 Tab：`全部 / 宽基指数 / 科创系列 / 商品ETF / 行业主题 / 机器人`
- 点击 Tab 即可过滤所有图表

---

## 三、覆盖标的清单（共 21 个）

| 分类 | 标的 |
|---|---|
| 宽基（8） | 上证50、沪深300、中证500、中证1000、中证A500、深证100、国证2000、创业板指 |
| 科创（5） | 科创50、科创100、科创半导体、科创芯片、双创50 |
| 商品（2） | 黄金、白银 |
| 行业（5） | 创新药、有色金属、光伏、半导体、芯片 |
| 机器人（1） | 机器人（聚合 15 只机器人主题 ETF） |

> **数据限制说明**：
> - **白银**：白银 LOF（161226）不在交易所 ETF 份额日报中，本项目仅用历史净值反映白银价格波动，份额/AUM 列为估算值
> - **机器人**：聚合华夏、南方、天弘、景顺等多家基金公司的机器人主题 ETF，份额为求和值

---

## 四、技术栈

| 层 | 技术 |
|---|---|
| 数据采集 | Python 3.13 + [akshare](https://github.com/akfamily/akshare) |
| 定时任务 | GitHub Actions（每日北京时间 16:40） |
| 数据格式 | JSON（前端直接 `fetch` 加载，无需后端） |
| 前端可视化 | 原生 HTML + CSS + JavaScript + [ECharts 5](https://echarts.apache.org/)（CDN 引入） |
| 部署托管 | GitHub Pages（`docs/` 目录） |
| 签名 | GPG 签名提交（`-s -S`） |

---

## 五、目录结构

```
etf-shares-tracker/
├── .github/
│   └── workflows/
│       └── fetch_data.yml        # 每日 16:40 定时抓取任务
├── docs/                          # GitHub Pages 站点根目录
│   ├── index.html                 # 仪表盘主页面（含全部可视化逻辑）
│   └── data/
│       └── etf_shares.json        # 每日生成的数据文件
├── scripts/
│   ├── fetch_data.py              # 主抓取脚本（上交所+深交所+东财）
│   ├── backfill_data.py           # 历史数据回填脚本
│   ├── gen_test_data.py           # 测试数据生成器
│   └── requirements.txt           # Python 依赖
├── .gitignore
└── README.md
```

---

## 六、本地运行

### 6.1 数据采集端

```powershell
# 创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r scripts/requirements.txt

# 抓取当日数据
python scripts/fetch_data.py

# 回填历史数据
python scripts/backfill_data.py
```

数据输出到 `docs/data/etf_shares.json`，格式示例：

```json
{
  "last_update": "2026-07-09 09:02:39",
  "records": {
    "2025-05-06": {
      "上证50":   { "shares": 628.4843, "nav": 2.7086, "aum": 1702.31 },
      "中证A500": { "shares": 2236.014,  "nav": 0.9502, "aum": 2124.66 }
    }
  },
  "_meta": { "silver_note": "..." }
}
```

### 6.2 前端展示端

任选其一：

- **直接打开**：双击 `docs/index.html`（注意：部分浏览器对本地 `fetch` 有限制）
- **本地 HTTP 服务**（推荐）：

```powershell
# 方法 1：Python 内置
cd docs
python -m http.server 8000
# 浏览器访问 http://localhost:8000

# 方法 2：VS Code Live Server 插件
# 右键 docs/index.html → Open with Live Server
```

---

## 七、自动化部署

### 7.1 GitHub Actions 定时任务

工作流定义在 [`.github/workflows/fetch_data.yml`](.github/workflows/fetch_data.yml)：

- **触发时间**：每日北京时间 16:40（UTC 08:40）`cron: '40 8 * * 1-5'`
- **支持手动触发**：`workflow_dispatch`
- **执行步骤**：
  1. 检出代码
  2. 安装 Python 3.13
  3. 安装依赖
  4. 运行 `fetch_data.py`
  5. 自动提交 `docs/data/etf_shares.json` 并推送

### 7.2 GitHub Pages 托管

**首次启用步骤**：

1. 进入仓库 → `Settings` → `Pages`
2. Source 选择 `Deploy from a branch`
3. Branch 选择 `main`，目录选择 `/docs`
4. 保存后等待 1–2 分钟，访问 `https://<用户名>.github.io/etf-shares-tracker/`

> 后续每次推送代码，GitHub Pages 会自动重新部署。

---

## 八、关键设计决策

| 决策 | 原因 |
|---|---|
| 以"资产规模(AUM)"作为默认主指标 | 同时反映资金流向（份额）和资产价格（净值），视角更全面 |
| 按代码 + 名称双轨匹配 | 避免简称模糊（如 SSE 中 510050 叫"50ETF"） |
| 负向关键词过滤 | 排除子分类干扰（如"工业有色"不算"有色金属"） |
| JSON 而非 CSV | 前端是 JS 直接加载，零解析成本 |
| ECharts 5 via CDN | 无需 npm 构建，仓库体积小、零依赖 |
| 热图改用"占比(%)"按"该值/当日总规模"计算 | 让大品类自然更显眼，避免每行各自归一化后视觉趋同 |
| 全部图表合并 resize 监听器 | 防止重复绑定导致内存泄漏 |
| Sparkline 实例显式 dispose | 防止表格重渲时实例累积 |
| `?.[t]` 可选链 + 显式空数据保护 | 数据为空时不再抛 `Cannot read properties of undefined` |

---

## 九、已知问题与限制

| 问题 | 现状 |
|---|---|
| 白银 ETF | A 股无场内白银 ETF，份额/AUM 为估算值，仅净值可反映真实价格 |
| akshare 历史净值接口 | `fund_etf_fund_info_em` 只能取最新 NAV，历史 NAV 通过 `fund_etf_fund_info_em` 历史走势接口补齐 |
| akshare 进度条递归 | `tqdm` 与 akshare 内部调用冲突，已通过环境变量 `TQDM_DISABLE=1` 解决 |
| 数据频率 | 仅交易日 16:40 后更新一次（盘后数据），非实时 |
| 瀑布图 `dataZoom` 文本 | 当选择极端缩放范围时，`dataZoom` 文本可能溢出，后续在 `textStyle.formatter` 中加单位格式化（亿元/亿份）|
| 热图占比模式色阶 | 大权重 ETF 会拉高 `maxColor`、导致中小标的颜色辨识度偏低。后续可切换为百分位裁剪 `[P5, P95]` 或换用三段发散色阶 |

---

## 十、后续步骤（Next Steps）

详细计划见仓库 Wiki 或本节 TODO 列表。

### 近期（1–2 周）

- [ ] 在 GitHub 仓库 Settings → Pages 启用 Pages，绑定线上地址
- [ ] 在仓库 About 区添加简介与线上链接
- [ ] 添加 `LICENSE`（推荐 MIT）
- [ ] 添加 PR / Issue 模板

### 中期（1 个月）

- [ ] 增加导出按钮（CSV / 图片）以便用户下载数据
- [ ] 增加"目标对比"功能：勾选 2–4 个标的同屏对比
- [ ] 接入 5 日 / 10 日 / 20 日均线辅助判断
- [ ] 增加移动端适配优化（当前仅做了基础响应式）

### 长期（季度级）

- [ ] 拓展到港股 ETF、美股 ETF
- [ ] 接入 LOF、场外基金申赎数据
- [ ] 接入 Wind / iFinD 等更稳定的数据源
- [ ] 接入告警：单日净流入/流出超过阈值时邮件/微信通知

---

## 十一、贡献指南

欢迎提交 Issue 和 Pull Request。

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 提交修改：`git commit -s -S -m "feat: 新功能描述"`
4. 推送分支：`git push origin feat/your-feature`
5. 提交 Pull Request（关联关键词写正文，例如 `Fixes #12`）

> 提交请使用 GPG 签名（`-s -S`），保持与现有提交风格一致。

---

## 十二、许可证

本项目代码采用 [MIT 协议](LICENSE) 开源。

数据仅供研究参考，不构成任何投资建议。

---

## 十三、致谢

- 数据来源：[akshare](https://github.com/akfamily/akshare)、上海证券交易所、深圳证券交易所、东方财富
- 可视化：[Apache ECharts](https://echarts.apache.org/)
- 灵感参考：[digger-yu/gold](https://digger-yu.github.io/gold/)
