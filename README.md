# OpenFAST 批量化仿真系统

<div align="center">

一个基于 Streamlit 开发的 OpenFAST 风电仿真批量处理系统，支持单个仿真配置、批量案例管理、结果可视化和智能语言指导。

> **声明**：本项目基于开源项目 [OpenFAST](https://github.com/OpenFAST/OpenFAST) 进行二次开发，**仅供学习交流使用**。本系统仅为图形化前端，需单独安装 OpenFAST。感谢 OpenFAST 原作者团队为我们提供便捷的风电仿真计算方式。

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.55.0-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [常见问题](#常见问题)

</div>

---

## 功能特性

本系统提供以下五大功能模块：

| 模块 | 功能 |
|:----:|------|
| 🔧 **单个仿真** | 配置并运行单个 OpenFAST 仿真案例，支持完整的参数配置 |
| 🔢 **批量化仿真** | 批量导入和管理多个仿真案例，一次性运行多个仿真 |
| 📊 **可视化分析** | 查看和分析仿真结果数据（.out/.outb 文件），支持多种图表类型 |
| 🎬 **VTK 3D可视化** | 3D 可视化 VTK 格式的仿真结果，支持动画播放和交互查看 |
| 💬 **语言指导** | 通过自然语言描述需求，自动生成批量仿真案例 |

### 核心功能亮点

- **可视化参数配置**：无需手动编辑 FST 文件，通过图形界面配置所有仿真参数
- **批量案例管理**：支持批量导入、编辑和运行仿真案例
- **智能参数生成**：基于 LangChain + OpenAI 的自然语言参数生成
- **丰富的结果可视化**：支持 2D 图表和 3D VTK 可视化
- **AI 智能助手**：内置使用指南助手，解答系统使用问题

---

## 快速开始

### 环境要求

- **Python**: 3.10
- **操作系统**: Windows
- **OpenFAST**: 4.2.1 或更高版本（需单独安装）

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/yourusername/SimulationSystem_OPENFAST.git
cd SimulationSystem_OPENFAST/v8_release
```

2. **创建虚拟环境**（推荐）

```bash
# Windows
conda create -n SimulationSystem_OPENFAST python==3.10
conda activate SimulationSystem_OPENFAST
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置 OpenFAST 路径**

编辑 `app.py` 中的配置，或通过系统侧边栏设置：

```python
OPENFAST_EXE = r"你的OpenFAST安装路径\openfast_x64.exe"
TEMPLATE_FST = r"你的模板文件路径\5MW_OC4Semi_WSt_WavesWN.fst"
RESULTS_DIR = r"你的结果保存路径\results"
```

5. **启动系统**

```bash
streamlit run app.py
```

浏览器将自动打开 `http://localhost:8501`

---

## 使用指南

### 侧边栏配置

系统启动后，首先在侧边栏配置以下内容：

1. **OpenFAST 路径**：指定 openfast 可执行文件位置
2. **结果保存目录**：设置仿真案例保存位置（需包含 5MW_Baseline 文件夹）
3. **AI 助手**：可选，用于自然语言指导

### 单个仿真流程

```
选择 FST 文件 → 配置仿真参数 → 输入案例名称 → 创建并运行
```

### 批量化仿真流程

```
导入案例文件夹 → 编辑案例参数 → 保存配置 → 批量运行
```

### 可视化分析流程

```
选择结果文件夹 → 查看数据预览 → 选择指标 → 生成图表
```

---

## 项目结构

```
v8_release/
├── app.py              # 主程序
├── requirements.txt    # 项目依赖
├── README.md          # 项目说明
├── 用户手册.md          # 详细使用手册
└── results/
    └── 5MW_Baseline/   # 5MW基准风电场数据模板
        ├── AeroData/   # 气动数据
        ├── Airfoils/   # 翼型数据
        ├── HydroData/  # 水动力数据
        ├── ServoData/  # 伺服控制数据
        └── Wind/       # 风场数据
```

---

## 常见问题

### Q: 如何修改仿真时间？

在"单个仿真"或"批量仿真"的编辑界面，找到"仿真控制"标签，修改 `TMax` 参数。

### Q: 如何关闭 VTK 输出？

在"可视化设置"中，将 `WrVTK` 设置为 `0`。

### Q: 结果文件保存在哪里？

默认保存在 `results` 目录，可在侧边栏设置自定义结果目录。

### Q: 如何查看锚链张力？

在"可视化分析"中选择 `FAIRTEN1-10` 指标进行绘图。

### Q: OpenFAST 在哪里下载？

请访问 [OpenFAST 官网](https://openfast.readthedocs.io/) 下载最新版本。

---

## 参数名称对照表

| 中文 | 参数名 | 说明 |
|------|--------|------|
| 总仿真时间 | TMax | 仿真总时长（秒） |
| 时间步长 | DT | 推荐的模块时间步长（秒） |
| VTK输出 | WrVTK | 0=无, 1=初始化, 2=动画, 3=模态 |
| VTK类型 | VTK_type | 1=曲面, 2=线框, 3=全部 |
| 重力加速度 | Gravity | m/s² |
| 空气密度 | AirDens | kg/m³ |
| 水密度 | WtrDens | kg/m³ |
| 结构动力学 | CompElast | 1, 2, 3 |
| 气动载荷 | CompAero | 0=无, 1, 2, 3 |
| 水动力载荷 | CompHydro | 0=无, 1 |
| 系泊系统 | CompMooring | 0=无, 1, 2, 3, 4 |

---

## 主要依赖

| 库名 | 用途 |
|------|------|
| streamlit | Web 应用框架 |
| pandas | 数据处理 |
| plotly | 交互式图表 |
| pyvista | 3D 可视化 |
| vtk | VTK 文件处理 |
| langchain | AI 语言模型集成 |
| openai | GPT 模型接口 |

完整依赖列表请查看 [requirements.txt](requirements.txt)

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## 免责声明

本项目基于开源项目 [OpenFAST](https://github.com/OpenFAST/OpenFAST) 进行二次开发，**仅供学习交流使用**。

本系统仅为 OpenFAST 的图形化批量处理前端，不包含 OpenFAST 核心计算引擎。使用本系统需要单独安装 OpenFAST。

感谢 OpenFAST 原作者团队为我们所有风机领域爱好者提供如此便捷的风电仿真计算方式。

---

## 致谢

特别感谢以下开源项目：

- [OpenFAST](https://github.com/OpenFAST/OpenFAST) - 开源风力涡轮机仿真工具
- [Streamlit](https://streamlit.io/) - Python Web 应用框架
- [PyVista](https://pyvista.org/) - 3D 可视化库

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐️**

</div>
