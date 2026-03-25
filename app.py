# develop environment: SimulationSystem_OPENFAST python 3.10
import streamlit as st
import os
import re
import subprocess
from datetime import datetime
import shutil
import struct
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import pyvista as pv
from io import BytesIO
import base64
import tempfile
import json
import time
import tkinter as tk
from tkinter import filedialog
import logging
import warnings

# ==================== 隐藏 Streamlit 警告 ====================
# 过滤 Streamlit 的 label 空值警告
logging.getLogger("streamlit.elements.lib.policies").setLevel(logging.ERROR)
logging.getLogger("streamlit").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*empty value.*")
warnings.filterwarnings("ignore", message=".*label_visibility.*")


# ==================== 配置 ====================
OPENFAST_EXE = r"D:\software\openfast-4.2.1\reg_tests\r-test\glue-codes\openfast\5MW_OC4Semi_WSt_WavesWN\openfast_x64.exe"
TEMPLATE_FST = r"D:\software\openfast-4.2.1\reg_tests\r-test\glue-codes\openfast\5MW_OC4Semi_WSt_WavesWN\5MW_OC4Semi_WSt_WavesWN.fst"
RESULTS_DIR = r"d:\project\pythonproject\course\develop\SimulationSystem_OPENFAST\v8\results"


# ==================== 文件夹选择函数 ====================
def select_directory():
    """打开文件夹选择对话框并返回所选路径"""
    try:
        # 创建隐藏的 tkinter 根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.wm_attributes('-topmost', True)  # 置顶显示

        # 打开文件夹选择对话框
        folder_path = filedialog.askdirectory(
            title="选择 FST 文件所在目录",
            initialdir=r"D:\software\openfast-4.2.1"
        )

        # 销毁窗口
        root.destroy()

        return folder_path if folder_path else ""
    except Exception:
        return ""


def select_fst_file():
    """打开文件选择对话框，返回选中的FST文件路径"""
    try:
        # 创建隐藏的 tkinter 根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.wm_attributes('-topmost', True)  # 置顶显示

        # 打开文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择 FST 模板文件",
            initialdir=r"D:\software\openfast-4.2.1",
            filetypes=[("FST 文件", "*.fst"), ("所有文件", "*.*")]
        )

        # 销毁窗口
        root.destroy()

        return file_path if file_path else ""
    except Exception:
        return ""


def select_multiple_directories():
    """使用Windows API打开支持多选的文件夹对话框，返回路径列表"""
    import ctypes
    from ctypes import wintypes

    selected_folders = []

    try:
        # 定义COM接口和常量
        CoInitialize = ctypes.windll.ole32.CoInitialize
        CoCreateInstance = ctypes.windll.ole32.CoCreateInstance

        # GUID定义
        IID_IFileOpenDialog = ctypes.GUID('{d57c7286-d953-4737-9725-a7021262093f}')
        CLSID_FileOpenDialog = ctypes.GUID('{dc1c5a9c-e88a-4dde-a5a1-60f82a20aef7}')

        # 文件对话框选项
        FOS_PICKFOLDERS = 0x00000020
        FOS_ALLOWMULTISELECT = 0x00000200
        FOS_FORCEFILESYSTEM = 0x00000040
        FOS_NOCHANGEDIR = 0x00000100

        # 显示名称标志
        SIGDN_FILESYSPATH = 0x80058000
        SIGDN_DESKTOPABSOLUTEPARSING = 0x80028000

        # 初始化COM
        CoInitialize(None)

        # 创建IFileOpenDialog实例
        dialog = ctypes.c_void_p()
        hr = CoCreateInstance(
            ctypes.byref(CLSID_FileOpenDialog),
            None,
            1,  # CLSCTX_INPROC_SERVER
            ctypes.byref(IID_IFileOpenDialog),
            ctypes.byref(dialog)
        )

        if hr != 0:
            raise Exception("Failed to create FileOpenDialog")

        # 定义IFileOpenDialog::SetOptions方法
        IFileOpenDialog_SetOptions = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            ctypes.c_ulong
        )(('IFileOpenDialog::SetOptions', ctypes.oledll.ole32))

        # 设置选项
        IFileOpenDialog_SetOptions(
            dialog,
            FOS_PICKFOLDERS | FOS_ALLOWMULTISELECT | FOS_FORCEFILESYSTEM | FOS_NOCHANGEDIR
        )

        # 定义IFileOpenDialog::SetTitle方法
        IFileOpenDialog_SetTitle = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            ctypes.c_wchar_p
        )(('IFileOpenDialog::SetTitle', ctypes.oledll.ole32))

        # 设置标题
        IFileOpenDialog_SetTitle(dialog, "选择多个案例文件夹（可使用Ctrl/Shift+点击多选）")

        # 定义IFileOpenDialog::Show方法
        IFileOpenDialog_Show = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            wintypes.HWND
        )(('IFileOpenDialog::Show', ctypes.oledll.ole32))

        # 显示对话框
        result = IFileOpenDialog_Show(dialog, None)

        if result == 0:  # S_OK
            # 定义IFileOpenDialog::GetResults方法
            IFileOpenDialog_GetResults = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p)
            )(('IFileOpenDialog::GetResults', ctypes.oledll.ole32))

            # 获取结果集合
            results = ctypes.c_void_p()
            IFileOpenDialog_GetResults(dialog, ctypes.byref(results))

            # 定义IShellItemArray::GetCount方法
            IShellItemArray_GetCount = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_uint)
            )(('IShellItemArray::GetCount', ctypes.oledll.ole32))

            # 获取项目数量
            count = ctypes.c_uint()
            IShellItemArray_GetCount(results, ctypes.byref(count))

            # 定义IShellItemArray::GetItemAt方法
            IShellItemArray_GetItemAt = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.c_uint,
                ctypes.POINTER(ctypes.c_void_p)
            )(('IShellItemArray::GetItemAt', ctypes.oledll.ole32))

            # 定义IShellItem::GetDisplayName方法
            IShellItem_GetDisplayName = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_wchar_p)
            )(('IShellItem::GetDisplayName', ctypes.oledll.ole32))

            # 获取每个选中的文件夹路径
            for i in range(count.value):
                item = ctypes.c_void_p()
                IShellItemArray_GetItemAt(results, i, ctypes.byref(item))

                name_ptr = ctypes.c_wchar_p()
                IShellItem_GetDisplayName(item, SIGDN_FILESYSPATH, ctypes.byref(name_ptr))

                if name_ptr.value:
                    selected_folders.append(name_ptr.value)
                else:
                    # 如果获取不到文件系统路径，尝试获取解析名称
                    IShellItem_GetDisplayName(item, SIGDN_DESKTOPABSOLUTEPARSING, ctypes.byref(name_ptr))
                    if name_ptr.value and not name_ptr.value.startswith("::"):
                        selected_folders.append(name_ptr.value)

        # 释放
        ctypes.windll.ole32.CoUninitialize()

        return selected_folders

    except Exception as e:
        # 如果Windows API失败，回退到单选模式
        try:
            ctypes.windll.ole32.CoUninitialize()
        except:
            pass

        try:
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', True)

            folder_path = filedialog.askdirectory(
                title="选择案例文件夹",
                initialdir=r"D:\software\openfast-4.2.1"
            )

            root.destroy()

            if folder_path:
                return [folder_path]
            return []
        except:
            return selected_folders


# ==================== FST文件处理函数 ====================
def parse_fst_file(fst_path):
    """解析FST文件，获取参数值和说明"""
    param_info = {}

    with open(fst_path, 'r', encoding='utf-8') as f:
        content = f.read()

    line_pattern = r'^(?:(True|False)|"([^"]*)"|\s*(-?\d+\.?\d*(?:[Ee][+-]?\d+)?))\s+(\w+)\s+-\s+(.+)$'

    for line in content.split('\n'):
        match = re.match(line_pattern, line.strip())
        if match:
            groups = match.groups()
            param_name = groups[3]
            description = groups[4]

            if groups[0] is not None:
                value = groups[0] == "True"
            elif groups[1] is not None:
                value = groups[1]
            elif groups[2] is not None:
                val = groups[2]
                try:
                    if '.' in val or 'E' in val or 'e' in val:
                        value = float(val)
                    else:
                        value = int(val)
                except ValueError:
                    value = val
            else:
                continue

            param_info[param_name] = {
                'value': value,
                'description': description
            }

    return param_info


def parse_fst_from_content(fst_content):
    """从文件内容解析FST文件，获取参数值和说明（用于上传的文件）"""
    param_info = {}

    line_pattern = r'^(?:(True|False)|"([^"]*)"|\s*(-?\d+\.?\d*(?:[Ee][+-]?\d+)?))\s+(\w+)\s+-\s+(.+)$'

    for line in fst_content.split('\n'):
        match = re.match(line_pattern, line.strip())
        if match:
            groups = match.groups()
            param_name = groups[3]
            description = groups[4]

            if groups[0] is not None:
                value = groups[0] == "True"
            elif groups[1] is not None:
                value = groups[1]
            elif groups[2] is not None:
                val = groups[2]
                try:
                    if '.' in val or 'E' in val or 'e' in val:
                        value = float(val)
                    else:
                        value = int(val)
                except ValueError:
                    value = val
            else:
                continue

            param_info[param_name] = {
                'value': value,
                'description': description
            }

    return param_info


# 默认使用模板文件的参数信息
FST_PARAM_INFO = parse_fst_file(TEMPLATE_FST)


def get_fst_value(param_name, param_info=None):
    """从FST参数信息中读取参数值"""
    if param_info is None:
        param_info = FST_PARAM_INFO
    if param_name in param_info:
        return param_info[param_name]['value']
    return None


def get_fst_description(param_name):
    """获取参数说明（中文）"""
    chinese_descriptions = {
        # SIMULATION CONTROL
        "Echo": "是否将输入数据回显到.ech文件",
        "AbortLevel": "仿真中止的错误级别 (WARNING/SEVERE/FATAL)",
        "TMax": "总仿真时间 (秒)",
        "DT": "推荐的模块时间步长 (秒)",
        "InterpOrder": "输入/输出的插值阶数 (1=线性, 2=二次)",
        "NumCrctn": "修正迭代次数 (0=显式计算，无修正)",
        "DT_UJac": "计算雅可比矩阵的时间间隔 (秒)",
        "UJacSclFact": "雅可比矩阵的缩放因子",

        # FEATURE SWITCHES
        "CompElast": "结构动力学计算 (1=ElastoDyn; 2=ElastoDyn+BeamDyn; 3=简化ElastoDyn)",
        "CompInflow": "入流风速计算 (0=无风; 1=InflowWind; 2=外部输入)",
        "CompAero": "气动载荷计算 (0=无; 1=AeroDisk; 2=AeroDyn; 3=外部载荷)",
        "CompServo": "控制与电气驱动动力学 (0=无; 1=ServoDyn)",
        "CompSeaSt": "海况信息计算 (0=无; 1=SeaState)",
        "CompHydro": "水动力载荷计算 (0=无; 1=HydroDyn)",
        "CompSub": "子结构动力学 (0=无; 1=SubDyn; 2=外部平台MCKF)",
        "CompMooring": "系泊系统 (0=无; 1=MAP++; 2=FEAMooring; 3=MoorDyn; 4=OrcaFlex)",
        "CompIce": "冰载荷计算 (0=无; 1=IceFloe; 2=IceDyn)",
        "MHK": "MHK涡轮机类型 (0=非MHK; 1=固定式MHK; 2=漂浮式MHK)",

        # ENVIRONMENTAL CONDITIONS
        "Gravity": "重力加速度 (m/s²)",
        "AirDens": "空气密度 (kg/m³)",
        "WtrDens": "水的密度 (kg/m³)",
        "KinVisc": "运动粘度 (m²/s)",
        "SpdSound": "流体中的声速 (m/s)",
        "Patm": "大气压力 (Pa) [仅用于MHK涡轮机气蚀检查]",
        "Pvap": "蒸汽压力 (Pa) [仅用于MHK涡轮机气蚀检查]",
        "WtrDpth": "水深 (米)",
        "MSL2SWL": "静水位与平均海平面之间的偏移 (米) [向上为正]",

        # OUTPUT
        "SumPrint": "是否将汇总数据打印到.sum文件",
        "SttsTime": "屏幕状态消息的时间间隔 (秒)",
        "ChkptTime": "创建检查点文件的时间间隔 (秒)，用于潜在重启",
        "DT_Out": "表格输出的时间步长 (秒) 或使用\"default\"",
        "TStart": "开始表格输出的时间 (秒)",
        "OutFileFmt": "表格输出文件格式 (1=文本.out; 2=二进制.outb; 3=两者; 4=未压缩二进制; 5=1和4)",
        "TabDelim": "文本表格输出是否使用制表符分隔 (否则使用空格)",
        "OutFmt": "文本表格输出的格式 (不包括时间通道)，结果字段应为10个字符",

        # LINEARIZATION
        "Linearize": "是否进行线性化分析",
        "CalcSteady": "线性化前是否计算稳态周期运行点 [Linearize=False时无效]",
        "TrimCase": "要修剪的控制器参数 (1=偏航; 2=扭矩; 3=变桨) [CalcSteady=True时使用]",
        "TrimTol": "转速收敛的容差 [CalcSteady=True时使用]",
        "TrimGain": "转速误差的比例增益 (>0) [CalcSteady=True时使用] (偏航/变桨: rad/(rad/s); 扭矩: Nm/(rad/s))",
        "Twr_Kdmp": "塔架阻尼系数 [CalcSteady=True时使用] (N/(m/s))",
        "Bld_Kdmp": "叶片阻尼系数 [CalcSteady=True时使用] (N/(m/s))",
        "NLinTimes": "线性化次数 (>=1) [Linearize=False时无效]",
        "LinTimes": "线性化时间列表 (秒) [Linearize=True且CalcSteady=False时使用]",
        "LinInputs": "线性化中包含的输入 (0=无; 1=标准; 2=所有模块输入(调试)) [Linearize=False时无效]",
        "LinOutputs": "线性化中包含的输出 (0=无; 1=来自OutList; 2=所有模块输出(调试)) [Linearize=False时无效]",
        "LinOutJac": "线性化输出中是否包含完整雅可比矩阵(用于调试) [仅当LinInputs=LinOutputs=2时有效]",
        "LinOutMod": "除了完整系统输出外，是否写入模块级线性化输出文件",

        # VISUALIZATION
        "WrVTK": "VTK可视化数据输出 (0=无; 1=仅初始化; 2=动画; 3=模态形状)",
        "VTK_type": "VTK可视化数据类型 (1=曲面; 2=基本网格(线/点); 3=所有网格(调试)) [WrVTK=0时无效]",
        "VTK_fields": "是否将网格字段写入VTK数据文件 [WrVTK=0时无效]",
        "VTK_fps": "VTK输出的帧率 (帧/秒) [WrVTK=2或WrVTK=3时有效]",
    }

    return chinese_descriptions.get(param_name, "")


def update_fst_value(fst_path, param_name, new_value):
    """更新FST文件中的参数值"""
    with open(fst_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 根据值类型选择匹配模式
    if isinstance(new_value, bool):
        # 布尔值：匹配原始行并保留空格格式
        pattern = rf"^([Tt]rue|[Ff]alse)\s+({re.escape(param_name)})"
        value_str = str(new_value)
        replacement = f"{value_str:<6}  {param_name}"
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
    elif isinstance(new_value, str) and new_value.startswith('"'):
        # 带引号的字符串
        pattern = rf'^"[^"]*"\s+({re.escape(param_name)})'
        replacement = f'{new_value}  {param_name}'
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
    elif isinstance(new_value, str):
        # 普通字符串
        pattern = rf'^"[^"]*"\s+({re.escape(param_name)})'
        replacement = f'"{new_value}"  {param_name}'
        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)
    else:
        # 数值
        pattern = rf"^\s*(-?\d+\.?\d*(?:[Ee][+-]?\d+)?)\s+({re.escape(param_name)})"

        if isinstance(new_value, float):
            if abs(new_value) < 0.0001 or abs(new_value) >= 10000:
                replacement = f"{new_value:.6E}  {param_name}"
            else:
                replacement = f"{new_value:.6g}  {param_name}".replace(". ", ".0 ").replace("- ", "-0.")
        else:
            replacement = f"{new_value}  {param_name}"

        new_content = re.sub(pattern, replacement, content, count=1, flags=re.MULTILINE)

    with open(fst_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def create_case_directory(case_name, use_uploaded_fst=False, uploaded_fst_content=None, uploaded_fst_name=None, dependency_dir=None, custom_results_dir=None):
    """创建案例目录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 使用自定义结果目录或默认目录
    base_dir = custom_results_dir if custom_results_dir else RESULTS_DIR
    case_dir = os.path.join(base_dir, f"{case_name}_{timestamp}")
    os.makedirs(case_dir, exist_ok=True)

    copied_files = []
    skipped_files = []

    if use_uploaded_fst and uploaded_fst_content and uploaded_fst_name:
        # 使用用户上传的FST文件内容
        fst_name = uploaded_fst_name
        fst_path = os.path.join(case_dir, fst_name)
        # 直接写入字符串内容，保持原始格式
        with open(fst_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(uploaded_fst_content)
    else:
        # 复制模板FST文件
        fst_name = os.path.basename(TEMPLATE_FST)
        fst_path = os.path.join(case_dir, fst_name)
        shutil.copy2(TEMPLATE_FST, fst_path)

    # 复制依赖文件（如果提供了依赖目录）
    if dependency_dir and os.path.isdir(dependency_dir):
        copied_files, skipped_files = copy_input_files(dependency_dir, case_dir)

    return fst_path, case_dir, copied_files, skipped_files


def copy_input_files(source_dir, target_dir):
    """复制输入文件到工作目录"""
    copied_files = []
    skipped_files = []

    # 复制所有.dat文件和其他依赖文件
    source_files = os.listdir(source_dir)
    for file in source_files:
        # 复制 .dat, .fst, .inp, .txt 等可能的依赖文件
        if any(file.endswith(ext) for ext in ['.dat', '.fst', '.inp', '.txt', '.json', '.yaml', '.yml']):
            src = os.path.join(source_dir, file)
            dst = os.path.join(target_dir, file)
            if not os.path.exists(dst):
                try:
                    shutil.copy2(src, dst)
                    copied_files.append(file)
                except Exception as e:
                    skipped_files.append(f"{file} (错误: {str(e)})")
            else:
                copied_files.append(file)

    return copied_files, skipped_files


# ==================== 结果文件读取函数 ====================
def read_fast_text(file_path):
    """读取OpenFAST文本格式输出文件 (.out)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 解析头部信息
    # 默认格式：第7行是列名，第8行是单位
    header_rows = 8
    name_line = 6  # 0-indexed
    unit_line = 7  # 0-indexed

    if len(lines) < header_rows:
        return None, [], []

    # 读取列名
    channel_names = lines[name_line].strip().split()

    # 读取单位
    channel_units = lines[unit_line].strip().split()

    # 读取数据
    data = []
    for line in lines[header_rows:]:
        line = line.strip()
        if line and not line.startswith('!') and not line.startswith('#'):
            values = [float(x) for x in line.split()]
            if values:
                data.append(values)

    desc_str = lines[4].strip() if len(lines) > 4 else ""  # 获取描述字符串
    return np.array(data), channel_names, channel_units, desc_str


def read_fast_binary(file_path):
    """读取OpenFAST二进制格式输出文件 (.outb)"""
    with open(file_path, 'rb') as f:
        # 读取文件格式ID (int16)
        file_id = struct.unpack('<h', f.read(2))[0]

        # 读取通道名称长度 (int16)
        if file_id == 4:  # ChanLen_In format
            len_name = struct.unpack('<h', f.read(2))[0]
        else:
            len_name = 10

        # 读取输出通道数 (int32)
        num_channels = struct.unpack('<i', f.read(4))[0]

        # 读取时间步数 (int32)
        num_timesteps = struct.unpack('<i', f.read(4))[0]

        # 根据文件ID读取时间信息
        if file_id == 1:  # WithTime
            time_slope = struct.unpack('<d', f.read(8))[0]
            time_offset = struct.unpack('<d', f.read(8))[0]
        else:  # WithoutTime or NoCompressWithoutTime
            time_first = struct.unpack('<d', f.read(8))[0]
            time_incr = struct.unpack('<d', f.read(8))[0]

        # 读取通道缩放因子和偏移量
        if file_id == 3:  # NoCompressWithoutTime
            col_slope = np.ones(num_channels)
            col_offset = np.zeros(num_channels)
        else:
            col_slope = np.array([struct.unpack('<f', f.read(4))[0] for _ in range(num_channels)])
            col_offset = np.array([struct.unpack('<f', f.read(4))[0] for _ in range(num_channels)])

        # 读取描述字符串长度和内容
        len_desc = struct.unpack('<i', f.read(4))[0]
        desc_str = f.read(len_desc).decode('ascii', errors='ignore').strip()

        # 读取通道名称
        channel_names = []
        for _ in range(num_channels + 1):
            name_bytes = f.read(len_name)
            name = name_bytes.decode('ascii', errors='ignore').strip()
            channel_names.append(name)

        # 读取通道单位
        channel_units = []
        for _ in range(num_channels + 1):
            unit_bytes = f.read(len_name)
            unit = unit_bytes.decode('ascii', errors='ignore').strip()
            channel_units.append(unit)

        # 读取数据
        data = np.zeros((num_timesteps, num_channels + 1))

        if file_id == 1:  # WithTime
            # 读取时间数据
            packed_time = np.array([struct.unpack('<i', f.read(4))[0] for _ in range(num_timesteps)])

        # 读取通道数据
        if file_id == 3:  # NoCompressWithoutTime
            packed_data = np.array([struct.unpack('<d', f.read(8))[0] for _ in range(num_timesteps * num_channels)])
        else:
            packed_data = np.array([struct.unpack('<h', f.read(2))[0] for _ in range(num_timesteps * num_channels)])

        # 解压数据
        for it in range(num_timesteps):
            start_idx = num_channels * it
            end_idx = num_channels * (it + 1)
            data[it, 1:] = (packed_data[start_idx:end_idx] - col_offset) / col_slope

        # 处理时间列
        if file_id == 1:  # WithTime
            data[:, 0] = (packed_time - time_offset) / time_slope
        else:  # WithoutTime
            data[:, 0] = time_first + time_incr * np.arange(num_timesteps)

        return data, channel_names, channel_units, desc_str


def render_parameter_input(param_name, param_type, default_value, options, section_name, version=0):
    """渲染参数输入组件 - 统一格式版本"""
    # 生成唯一的key（包含版本号，以便在文件变化时强制刷新）
    key = f"{section_name}_{param_name}_v{version}"

    # 获取参数说明
    description = get_fst_description(param_name)

    # 统一：标签和控件换行显示
    st.markdown(f"**{param_name}** · :gray[{description}]", unsafe_allow_html=True)

    if param_type == "bool":
        # 布尔值使用下拉选择
        bool_options = [True, False]
        # 处理None值，默认为False
        if default_value is None:
            default_value = False
        labels = {True: "True", False: "False"}
        selected = st.selectbox("", bool_options, index=bool_options.index(default_value), format_func=lambda x: labels.get(x, str(x)), key=key, label_visibility="collapsed")
        return selected
    elif param_type == "select":
        if isinstance(options[0], int):
            labels = {v: str(v) for v in options}
        else:
            labels = {v: v for v in options}
        selected = st.selectbox("", options, index=options.index(default_value) if default_value in options else 0, format_func=lambda x: labels.get(x, str(x)), key=key, label_visibility="collapsed")
        return selected
    elif param_type == "float":
        min_val, max_val = options
        return st.number_input("", min_value=min_val, max_value=max_val, value=float(default_value), step=0.0001, format="%.6g", key=key, label_visibility="collapsed")
    elif param_type == "int":
        min_val, max_val = options
        return st.number_input("", min_value=min_val, max_value=max_val, value=int(default_value), step=1, key=key, label_visibility="collapsed")
    elif param_type == "text":
        return st.text_input("", value=str(default_value), key=key, label_visibility="collapsed")

    return default_value


# ==================== AI助手辅助函数 ====================
USER_MANUAL_PATH = os.path.join(os.path.dirname(__file__), "用户手册.md")

def load_user_manual():
    """加载用户手册内容"""
    try:
        with open(USER_MANUAL_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return "用户手册未找到"

def check_forbidden_questions(user_input):
    """检查是否为拒答问题"""
    forbidden_keywords = [
        'api', 'API', '密钥', 'key', 'token', 'openai', 'chatgpt',
        '后端', '服务端', '服务器', '数据库', '部署', '源码',
        '环境变量', '配置文件', '隐藏功能', '权限', '密码',
        '闲聊', '你好', '天气', '笑话', '聊天'
    ]
    user_lower = user_input.lower()
    for keyword in forbidden_keywords:
        if keyword.lower() in user_lower:
            return True
    return False

def get_system_prompt():
    """获取系统提示词"""
    return """你是OpenFAST批量化仿真系统的前端使用助手。

【规则】
1. 只回答系统前端使用问题
2. 优先从用户手册中查找答案
3. 回答不超过3句话
4. 无法确认时回答"当前无法确认"

【拒答】API、后端、部署、数据库、源码、配置、权限等"""

def query_ai_assistant(user_input, manual_content):
    """查询AI助手"""
    try:
        import dotenv
        from langchain_openai import ChatOpenAI

        # 加载.env配置
        dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

        # 直接从.env读取密钥和URL
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')

        if not api_key:
            return "错误：API密钥未配置"
        if not base_url:
            return "错误：API地址未配置"

        # 创建LLM实例（直接传入参数）
        llm = ChatOpenAI(
            model='gpt-4o-mini',
            temperature=0,
            api_key=api_key,
            base_url=base_url
        )

        # 构建消息
        user_message = f"""用户手册：{manual_content[:3000]}

问题：{user_input}

回答不超过3句话。无法确认请回答"当前无法确认"。"""

        response = llm.invoke([
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": user_message}
        ])
        return response.content.strip()

    except ImportError as e:
        return "错误：缺少依赖库，请运行: pip install langchain-openai python-dotenv"
    except Exception as e:
        error_detail = str(e)
        if "401" in error_detail:
            return "错误：API密钥无效"
        elif "timeout" in error_detail.lower():
            return "错误：请求超时"
        elif "connection" in error_detail.lower():
            return "错误：网络连接失败"
        else:
            return f"错误：{error_detail[:80]}"


# ==================== Streamlit 界面 ====================
st.set_page_config(
    page_title="OpenFAST 批量化仿真系统",
    page_icon="🌊",
    layout="wide"
)

# 初始化 session_state
if 'fst_version' not in st.session_state:
    st.session_state.fst_version = 0
if 'param_values_cache' not in st.session_state:
    st.session_state.param_values_cache = {}

st.title("🌊 OpenFAST 批量化仿真系统")
st.markdown("---")

# 侧边栏 - 配置信息
with st.sidebar:
    st.header("⚙️ 配置信息")

    # ==================== OpenFAST 路径选择 ====================
    st.markdown("---")
    st.markdown("### 🔧 OpenFAST 路径")

    col_of1, col_of2 = st.columns([3, 1])

    with col_of1:
        # 显示当前 OpenFAST 路径
        current_openfast_path = st.session_state.get('custom_openfast_path', OPENFAST_EXE)
        if st.session_state.get('use_custom_openfast', False):
            st.success(f"📁 自定义:\n`{current_openfast_path}`")
        else:
            st.info(f"📁 默认:\n`{OPENFAST_EXE}`")

    with col_of2:
        use_custom_openfast = st.checkbox("自定义", value=False, key="use_custom_openfast_chk")

    if use_custom_openfast:
        # 显示文件选择界面
        col_of_path1, col_of_path2 = st.columns([4, 1])

        with col_of_path1:
            st.caption("💡 选择 OpenFAST 可执行文件所在目录")

        with col_of_path2:
            if st.button("📂 浏览", key="browse_openfast", use_container_width=True):
                selected_path = select_directory()
                if selected_path:
                    # 查找目录中的 openfast.exe 文件
                    exe_files = [f for f in os.listdir(selected_path) if f.lower().startswith('openfast') and f.lower().endswith('.exe')]
                    if exe_files:
                        exe_path = os.path.join(selected_path, exe_files[0])
                        st.session_state.custom_openfast_path = exe_path
                        st.session_state.use_custom_openfast = True
                        st.success(f"✅ 已找到: {exe_files[0]}")
                        st.rerun()
                    else:
                        st.warning("⚠️ 目录中未找到 openfast*.exe 文件")
                        st.session_state.custom_openfast_path = selected_path
                        st.session_state.use_custom_openfast = True
                        st.rerun()
                else:
                    st.warning("未选择文件夹")

        # 同时也保留手动输入的选项
        with st.expander("或手动输入路径"):
            manual_openfast_path = st.text_input(
                "OpenFAST 可执行文件完整路径",
                value=st.session_state.get('custom_openfast_path', ''),
                placeholder=r"D:\software\openfast-4.2.1\...\openfast.exe",
                key="manual_openfast_path"
            )
            if manual_openfast_path and st.button("使用手动输入的路径", key="use_manual_openfast"):
                if os.path.isfile(manual_openfast_path):
                    st.session_state.custom_openfast_path = manual_openfast_path
                    st.session_state.use_custom_openfast = True
                    st.rerun()
                else:
                    st.error("❌ 文件不存在，请检查路径")

    # ==================== 结果目录选择 ====================
    st.markdown("---")
    st.markdown("### 📂 结果保存目录 Note:该目录下需要有 - 5MW_Baseline - 基础文件夹")

    col_res1, col_res2 = st.columns([3, 1])

    with col_res1:
        # 显示当前结果目录
        current_results_dir = st.session_state.get('custom_results_dir', RESULTS_DIR)
        if st.session_state.get('use_custom_results', False):
            st.success(f"📁 自定义:\n`{current_results_dir}`")
        else:
            st.info(f"📁 默认:\n`{RESULTS_DIR}`")

    with col_res2:
        use_custom_results = st.checkbox("自定义", value=False, key="use_custom_results_chk")

    if use_custom_results:
        # 显示目录选择界面
        col_res_path1, col_res_path2 = st.columns([4, 1])

        with col_res_path1:
            st.caption("💡 选择结果保存目录")

        with col_res_path2:
            if st.button("📂 浏览", key="browse_results", use_container_width=True):
                selected_path = select_directory()
                if selected_path:
                    st.session_state.custom_results_dir = selected_path
                    st.session_state.use_custom_results = True
                    st.rerun()
                else:
                    st.warning("未选择文件夹")

        # 同时也保留手动输入的选项
        with st.expander("或手动输入路径"):
            manual_results_path = st.text_input(
                "结果保存目录完整路径",
                value=st.session_state.get('custom_results_dir', ''),
                placeholder=r"D:\results\...",
                key="manual_results_path"
            )
            if manual_results_path and st.button("使用手动输入的路径", key="use_manual_results"):
                st.session_state.custom_results_dir = manual_results_path
                st.session_state.use_custom_results = True
                st.rerun()

    # ==================== 模板 FST 信息 ====================
    st.markdown("---")
    st.markdown("### 📋 模板 FST")
    st.info(f"**文件:**\n{os.path.basename(TEMPLATE_FST)}")

    # ==================== AI智能询问助手 ====================
    st.markdown("---")
    st.markdown("### 💬 AI助手")

    # 初始化助手状态
    if 'ai_assistant_expanded' not in st.session_state:
        st.session_state.ai_assistant_expanded = False
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []

    # 展开/收起按钮
    if st.button("🤖 打开助手" if not st.session_state.ai_assistant_expanded else "🔽 收起助手", key="ai_toggle", use_container_width=True):
        st.session_state.ai_assistant_expanded = not st.session_state.ai_assistant_expanded
        st.rerun()

    # 助手面板（展开时显示）
    if st.session_state.ai_assistant_expanded:
        st.markdown("---")

        # 用户输入
        user_input = st.text_input(
            "请输入问题",
            value="",
            placeholder="例如：如何修改仿真时间？",
            key="ai_assistant_input",
            max_chars=100,
            label_visibility="visible"
        )

        col_ask1, col_ask2 = st.columns([2, 1])

        with col_ask1:
            if st.button("🤖 提问", key="ai_ask_button", use_container_width=True):
                if user_input.strip():
                    # 检查是否为拒答问题
                    if check_forbidden_questions(user_input):
                        st.error("❌ 该问题不在助手服务范围内")
                    else:
                        # 查询AI助手
                        with st.spinner("🤖 思考中..."):
                            manual_content = load_user_manual()
                            answer = query_ai_assistant(user_input, manual_content)
                            st.session_state.ai_chat_history.append({
                                'question': user_input,
                                'answer': answer
                            })
                        st.rerun()
                else:
                    st.warning("⚠️ 请输入问题")

        with col_ask2:
            if st.button("🗑️ 清空", key="ai_clear_history", use_container_width=True):
                st.session_state.ai_chat_history = []
                st.rerun()

        # 显示对话历史
        if st.session_state.ai_chat_history:
            st.markdown("**对话记录:**")
            for chat in reversed(st.session_state.ai_chat_history[-5:]):  # 只显示最近5条
                with st.expander(f"Q: {chat['question']}", expanded=False):
                    st.markdown(f"**A:** {chat['answer']}")
        else:
            st.caption("💡 暂无对话记录")

# ==================== 主标签页 ====================
# 创建主标签页：单个仿真 / 批量化仿真
main_tabs = st.tabs([
    "🔧 单个仿真", "🔢 批量化仿真", "📊 可视化分析", "🎬 VTK 3D可视化", "💬 语言指导"
])

# ==================== 单个仿真板块 ====================
with main_tabs[0]:
    st.markdown("### 单个仿真设置")
    st.markdown("---")

    # ==================== FST文件选择 ====================
    st.subheader("📁 FST 文件选择")

    col_file1, col_file2 = st.columns([2, 1])

    with col_file1:
        uploaded_fst = st.file_uploader(
            "选择 FST 文件（可选）",
            type=['fst'],
            help="如果未选择，将使用默认模板文件",
            key="fst_uploader"
        )

    with col_file2:
        use_template = st.checkbox("使用默认模板", value=True, help="勾选则使用系统默认模板文件", key="use_template_chk")

    # 依赖文件目录设置（仅在上传文件时显示）
    dependency_dir = ""
    if uploaded_fst is not None:
        st.markdown("**📂 依赖文件目录**")

        # 使用列布局来放置输入框和浏览按钮
        col_dep1, col_dep2 = st.columns([4, 1])

        with col_dep1:
            # 显示当前选择的路径（只读）
            current_path = st.session_state.get('current_dependency_dir', '')
            if current_path:
                st.info(f"📁 已选择: `{current_path}`")
            else:
                st.caption("💡 请选择 FST 文件所在目录，将自动复制该目录下的 .dat 和 .fst 依赖文件")

        with col_dep2:
            # 浏览文件夹按钮
            if st.button("📂 浏览", key=f"browse_dep_{st.session_state.get('fst_version', 0)}", use_container_width=True):
                selected_path = select_directory()
                if selected_path:
                    st.session_state.current_dependency_dir = selected_path
                    st.rerun()  # 重新运行以更新显示
                else:
                    st.warning("未选择文件夹")

        # 同时也保留手动输入的选项
        with st.expander("或手动输入路径"):
            manual_path = st.text_input(
                "手动输入路径",
                value="",
                placeholder=r"D:\software\openfast-4.2.1\...",
                key="manual_dep_path"
            )
            if manual_path and st.button("使用手动输入的路径", key="use_manual_path"):
                st.session_state.current_dependency_dir = manual_path
                st.rerun()

    # 检测文件变化，更新版本号以强制刷新 widget
    current_fst_source = TEMPLATE_FST
    current_fst_param_info = FST_PARAM_INFO
    fst_display_name = os.path.basename(TEMPLATE_FST)
    need_refresh = False

    if uploaded_fst is not None:
        # 用户上传了文件
        uploaded_name = uploaded_fst.name
        if 'last_uploaded_name' not in st.session_state or st.session_state.last_uploaded_name != uploaded_name:
            need_refresh = True
            st.session_state.last_uploaded_name = uploaded_name
            st.session_state.fst_version += 1

        # 尝试多种编码方式解码文件，确保正确读取
        file_bytes = uploaded_fst.getvalue()
        fst_content = None
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
            try:
                fst_content = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if fst_content is None:
            # 如果所有编码都失败，使用 UTF-8 并忽略错误
            fst_content = file_bytes.decode('utf-8', errors='ignore')

        current_fst_param_info = parse_fst_from_content(fst_content)
        current_fst_source = uploaded_name
        fst_display_name = uploaded_name
        st.success(f"✅ 已加载文件: {uploaded_name}")
        # 在 session_state 中保存上传的文件内容
        st.session_state.uploaded_fst_content = fst_content
        st.session_state.uploaded_fst_name = uploaded_name
        st.session_state.use_uploaded_fst = True
    else:
        # 检查是否从上传切换回模板
        if st.session_state.get('use_uploaded_fst', False):
            need_refresh = True
            st.session_state.fst_version += 1

        if use_template:
            # 使用默认模板
            st.info(f"📋 使用默认模板: {fst_display_name}")
            st.session_state.use_uploaded_fst = False
        else:
            st.info("📋 使用默认模板")
            st.session_state.use_uploaded_fst = False

    st.markdown("---")

    # 案例名称
    case_name = st.text_input("案例名称", value="simulation", help="用于标识本次仿真")

    # ==================== 参数设置标签页 ====================
    st.subheader("📝 仿真参数设置")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "仿真控制", "功能开关", "环境条件", "输出设置", "线性化", "可视化"
    ])

    # 存储所有参数值
    param_values = {}

    # Tab 1: SIMULATION CONTROL
    with tab1:
        st.markdown("#### ⚙️ 仿真控制参数")
        col1, col2 = st.columns(2)
        with col1:
            param_values["Echo"] = render_parameter_input("Echo", "bool", get_fst_value("Echo", current_fst_param_info), None, "SIM_CTRL", st.session_state.fst_version)
            param_values["AbortLevel"] = render_parameter_input("AbortLevel", "select", get_fst_value("AbortLevel", current_fst_param_info), ["WARNING", "SEVERE", "FATAL"], "SIM_CTRL", st.session_state.fst_version)
            param_values["TMax"] = render_parameter_input("TMax", "float", get_fst_value("TMax", current_fst_param_info), (1.0, 10000.0), "SIM_CTRL", st.session_state.fst_version)
            param_values["DT"] = render_parameter_input("DT", "float", get_fst_value("DT", current_fst_param_info), (0.001, 1.0), "SIM_CTRL", st.session_state.fst_version)
        with col2:
            param_values["InterpOrder"] = render_parameter_input("InterpOrder", "int", get_fst_value("InterpOrder", current_fst_param_info), (1, 2), "SIM_CTRL", st.session_state.fst_version)
            param_values["NumCrctn"] = render_parameter_input("NumCrctn", "int", get_fst_value("NumCrctn", current_fst_param_info), (0, 10), "SIM_CTRL", st.session_state.fst_version)
            param_values["DT_UJac"] = render_parameter_input("DT_UJac", "float", get_fst_value("DT_UJac", current_fst_param_info), (0.0, 100000.0), "SIM_CTRL", st.session_state.fst_version)
            param_values["UJacSclFact"] = render_parameter_input("UJacSclFact", "float", get_fst_value("UJacSclFact", current_fst_param_info), (0.0, 10000000.0), "SIM_CTRL", st.session_state.fst_version)

    # Tab 2: FEATURE SWITCHES
    with tab2:
        st.markdown("#### 🔧 功能模块开关")
        col1, col2 = st.columns(2)
        with col1:
            param_values["CompElast"] = render_parameter_input("CompElast", "select", get_fst_value("CompElast", current_fst_param_info), [1, 2, 3], "FEAT", st.session_state.fst_version)
            param_values["CompInflow"] = render_parameter_input("CompInflow", "select", get_fst_value("CompInflow", current_fst_param_info), [0, 1, 2], "FEAT", st.session_state.fst_version)
            param_values["CompAero"] = render_parameter_input("CompAero", "select", get_fst_value("CompAero", current_fst_param_info), [0, 1, 2, 3], "FEAT", st.session_state.fst_version)
            param_values["CompServo"] = render_parameter_input("CompServo", "select", get_fst_value("CompServo", current_fst_param_info), [0, 1], "FEAT", st.session_state.fst_version)
            param_values["CompSeaSt"] = render_parameter_input("CompSeaSt", "select", get_fst_value("CompSeaSt", current_fst_param_info), [0, 1], "FEAT", st.session_state.fst_version)
        with col2:
            param_values["CompHydro"] = render_parameter_input("CompHydro", "select", get_fst_value("CompHydro", current_fst_param_info), [0, 1], "FEAT", st.session_state.fst_version)
            param_values["CompSub"] = render_parameter_input("CompSub", "select", get_fst_value("CompSub", current_fst_param_info), [0, 1, 2], "FEAT", st.session_state.fst_version)
            param_values["CompMooring"] = render_parameter_input("CompMooring", "select", get_fst_value("CompMooring", current_fst_param_info), [0, 1, 2, 3, 4], "FEAT", st.session_state.fst_version)
            param_values["CompIce"] = render_parameter_input("CompIce", "select", get_fst_value("CompIce", current_fst_param_info), [0, 1, 2], "FEAT", st.session_state.fst_version)
            param_values["MHK"] = render_parameter_input("MHK", "select", get_fst_value("MHK", current_fst_param_info), [0, 1, 2], "FEAT", st.session_state.fst_version)

    # Tab 3: ENVIRONMENTAL CONDITIONS
    with tab3:
        st.markdown("#### 🌍 环境条件参数")
        col1, col2 = st.columns(2)
        with col1:
            param_values["Gravity"] = render_parameter_input("Gravity", "float", get_fst_value("Gravity", current_fst_param_info), (0.0, 20.0), "ENV", st.session_state.fst_version)
            param_values["AirDens"] = render_parameter_input("AirDens", "float", get_fst_value("AirDens", current_fst_param_info), (0.0, 10.0), "ENV", st.session_state.fst_version)
            param_values["WtrDens"] = render_parameter_input("WtrDens", "float", get_fst_value("WtrDens", current_fst_param_info), (0.0, 2000.0), "ENV", st.session_state.fst_version)
            param_values["KinVisc"] = render_parameter_input("KinVisc", "float", get_fst_value("KinVisc", current_fst_param_info), (0.0, 1.0), "ENV", st.session_state.fst_version)
            param_values["SpdSound"] = render_parameter_input("SpdSound", "float", get_fst_value("SpdSound", current_fst_param_info), (0.0, 1000.0), "ENV", st.session_state.fst_version)
        with col2:
            param_values["Patm"] = render_parameter_input("Patm", "float", get_fst_value("Patm", current_fst_param_info), (0.0, 200000.0), "ENV", st.session_state.fst_version)
            param_values["Pvap"] = render_parameter_input("Pvap", "float", get_fst_value("Pvap", current_fst_param_info), (0.0, 10000.0), "ENV", st.session_state.fst_version)
            param_values["WtrDpth"] = render_parameter_input("WtrDpth", "float", get_fst_value("WtrDpth", current_fst_param_info), (0.0, 1000.0), "ENV", st.session_state.fst_version)
            param_values["MSL2SWL"] = render_parameter_input("MSL2SWL", "float", get_fst_value("MSL2SWL", current_fst_param_info), (-100.0, 100.0), "ENV", st.session_state.fst_version)

    # Tab 4: OUTPUT
    with tab4:
        st.markdown("#### 📊 输出设置")
        col1, col2 = st.columns(2)
        with col1:
            param_values["SumPrint"] = render_parameter_input("SumPrint", "bool", get_fst_value("SumPrint", current_fst_param_info), None, "OUT", st.session_state.fst_version)
            param_values["SttsTime"] = render_parameter_input("SttsTime", "float", get_fst_value("SttsTime", current_fst_param_info), (0.0, 100.0), "OUT", st.session_state.fst_version)
            param_values["ChkptTime"] = render_parameter_input("ChkptTime", "float", get_fst_value("ChkptTime", current_fst_param_info), (0.0, 10000.0), "OUT", st.session_state.fst_version)
            param_values["DT_Out"] = render_parameter_input("DT_Out", "float", get_fst_value("DT_Out", current_fst_param_info), (0.0, 1.0), "OUT", st.session_state.fst_version)
        with col2:
            param_values["TStart"] = render_parameter_input("TStart", "float", get_fst_value("TStart", current_fst_param_info), (0.0, 1000.0), "OUT", st.session_state.fst_version)
            param_values["OutFileFmt"] = render_parameter_input("OutFileFmt", "select", get_fst_value("OutFileFmt", current_fst_param_info), [1, 2, 3, 4, 5], "OUT", st.session_state.fst_version)
            param_values["TabDelim"] = render_parameter_input("TabDelim", "bool", get_fst_value("TabDelim", current_fst_param_info), None, "OUT", st.session_state.fst_version)
            param_values["OutFmt"] = render_parameter_input("OutFmt", "text", get_fst_value("OutFmt", current_fst_param_info), None, "OUT", st.session_state.fst_version)

    # Tab 5: LINEARIZATION
    with tab5:
        st.markdown("#### 📈 线性化分析")
        col1, col2 = st.columns(2)
        with col1:
            param_values["Linearize"] = render_parameter_input("Linearize", "bool", get_fst_value("Linearize", current_fst_param_info), None, "LIN", st.session_state.fst_version)
            param_values["CalcSteady"] = render_parameter_input("CalcSteady", "bool", get_fst_value("CalcSteady", current_fst_param_info), None, "LIN", st.session_state.fst_version)
            param_values["TrimCase"] = render_parameter_input("TrimCase", "select", get_fst_value("TrimCase", current_fst_param_info), [1, 2, 3], "LIN", st.session_state.fst_version)
            param_values["TrimTol"] = render_parameter_input("TrimTol", "float", get_fst_value("TrimTol", current_fst_param_info), (0.0, 1.0), "LIN", st.session_state.fst_version)
            param_values["TrimGain"] = render_parameter_input("TrimGain", "float", get_fst_value("TrimGain", current_fst_param_info), (0.0, 1.0), "LIN", st.session_state.fst_version)
            param_values["Twr_Kdmp"] = render_parameter_input("Twr_Kdmp", "float", get_fst_value("Twr_Kdmp", current_fst_param_info), (0.0, 100000.0), "LIN", st.session_state.fst_version)
            param_values["Bld_Kdmp"] = render_parameter_input("Bld_Kdmp", "float", get_fst_value("Bld_Kdmp", current_fst_param_info), (0.0, 100000.0), "LIN", st.session_state.fst_version)
        with col2:
            param_values["NLinTimes"] = render_parameter_input("NLinTimes", "int", get_fst_value("NLinTimes", current_fst_param_info), (1, 100), "LIN", st.session_state.fst_version)
            param_values["LinTimes"] = render_parameter_input("LinTimes", "text", get_fst_value("LinTimes", current_fst_param_info), None, "LIN", st.session_state.fst_version)
            param_values["LinInputs"] = render_parameter_input("LinInputs", "select", get_fst_value("LinInputs", current_fst_param_info), [0, 1, 2], "LIN", st.session_state.fst_version)
            param_values["LinOutputs"] = render_parameter_input("LinOutputs", "select", get_fst_value("LinOutputs", current_fst_param_info), [0, 1, 2], "LIN", st.session_state.fst_version)
            param_values["LinOutJac"] = render_parameter_input("LinOutJac", "bool", get_fst_value("LinOutJac", current_fst_param_info), None, "LIN", st.session_state.fst_version)
            param_values["LinOutMod"] = render_parameter_input("LinOutMod", "bool", get_fst_value("LinOutMod", current_fst_param_info), None, "LIN", st.session_state.fst_version)

    # Tab 6: VISUALIZATION
    with tab6:
        st.markdown("#### 🎨 可视化设置")
        col1, col2 = st.columns(2)
        with col1:
            param_values["WrVTK"] = render_parameter_input("WrVTK", "select", get_fst_value("WrVTK", current_fst_param_info), [0, 1, 2, 3], "VIS", st.session_state.fst_version)
            param_values["VTK_type"] = render_parameter_input("VTK_type", "select", get_fst_value("VTK_type", current_fst_param_info), [1, 2, 3], "VIS", st.session_state.fst_version)
        with col2:
            param_values["VTK_fields"] = render_parameter_input("VTK_fields", "bool", get_fst_value("VTK_fields", current_fst_param_info), None, "VIS", st.session_state.fst_version)
            param_values["VTK_fps"] = render_parameter_input("VTK_fps", "int", get_fst_value("VTK_fps", current_fst_param_info), (1, 60), "VIS", st.session_state.fst_version)

    # 将重要的参数值保存到 session_state，供后续模块使用
    if 'param_values' in locals() and 'WrVTK' in param_values:
        st.session_state.WrVTK = param_values["WrVTK"]

    st.markdown("---")

    # ==================== 运行控制区域 ====================
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📥 更新参数并创建案例", type="primary", width='stretch'):
            # 获取是否使用上传文件
            use_uploaded = st.session_state.get('use_uploaded_fst', False)
            uploaded_content = st.session_state.get('uploaded_fst_content', None)
            uploaded_name = st.session_state.get('uploaded_fst_name', None)
            # 从 session_state 获取依赖目录
            dep_dir = st.session_state.get('current_dependency_dir', '').strip() if use_uploaded else ''

            # 验证依赖目录（如果使用上传文件）
            if use_uploaded:
                if not dep_dir:
                    st.warning("⚠️ 未指定依赖文件目录。FST 文件通常需要同目录下的 .dat 等依赖文件才能正常运行。")
                    response = st.button("继续创建（可能导致仿真失败）", key="continue_without_deps")
                    if not response:
                        st.stop()
                elif not os.path.isdir(dep_dir):
                    st.error(f"❌ 依赖文件目录不存在: {dep_dir}")
                    st.stop()

            with st.spinner("正在创建案例目录..."):
                # 获取自定义结果目录（如果有）
                custom_results_dir = st.session_state.get('custom_results_dir', None) if st.session_state.get('use_custom_results', False) else None

                fst_path, case_dir, copied_files, skipped_files = create_case_directory(
                    case_name,
                    use_uploaded_fst=use_uploaded,
                    uploaded_fst_content=uploaded_content,
                    uploaded_fst_name=uploaded_name,
                    dependency_dir=dep_dir if use_uploaded else None,
                    custom_results_dir=custom_results_dir
                )

                # 如果使用模板，还需要复制模板目录的依赖文件
                if not use_uploaded:
                    template_dir = os.path.dirname(TEMPLATE_FST)
                    copied_files, skipped_files = copy_input_files(template_dir, case_dir)

                st.success(f"✅ 案例目录创建成功")

                # 验证保存的 FST 文件格式
                try:
                    with open(fst_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    # 检查 Echo 参数行
                    echo_line_found = False
                    for i, line in enumerate(lines[:20]):
                        if 'Echo' in line and '-' in line:  # 确保是参数行（包含分隔符 -）
                            echo_line_found = True
                            st.info(f"🔍 Echo 参数行 (第{i+1}行): `{repr(line.rstrip())}`")
                            # 验证格式：应该是 "True" 或 "False" 开头
                            stripped = line.strip()
                            if stripped.startswith('True') or stripped.startswith('False'):
                                st.success(f"✅ FST 文件格式验证通过")
                            else:
                                st.error(f"❌ Echo 参数格式错误!")
                                st.error(f"   期望格式: 'True' 或 'False' 开头")
                                st.error(f"   实际内容: `{stripped[:30]}...`")

                                # 显示文件的前几行用于调试
                                with st.expander("📄 查看文件前20行（调试）"):
                                    for j, debug_line in enumerate(lines[:20]):
                                        st.text(f"{j+1}: {repr(debug_line.rstrip())}")
                            break
                    if not echo_line_found:
                        st.warning("⚠️ 未找到 Echo 参数行")
                except Exception as e:
                    st.warning(f"⚠️ 无法验证 FST 文件格式: {str(e)}")

                # 显示文件复制信息
                if copied_files:
                    st.info(f"📋 已复制 {len(copied_files)} 个依赖文件")
                if skipped_files:
                    st.warning(f"⚠️ {len(skipped_files)} 个文件复制失败")

            with st.spinner("正在更新参数..."):
                # 更新所有参数
                for param_name, param_value in param_values.items():
                    update_fst_value(fst_path, param_name, param_value)

                st.success(f"✅ 参数更新成功! 共更新 {len(param_values)} 个参数")

                # 显示摘要
                with st.expander("📋 查看参数摘要"):
                    summary_data = {
                        "案例名称": case_name,
                        "工作目录": case_dir,
                        "FST文件": os.path.basename(fst_path),
                        "参数数量": len(param_values),
                        "来源": "用户上传" if use_uploaded else "默认模板",
                        "依赖目录": dep_dir if use_uploaded else str(os.path.dirname(TEMPLATE_FST)),
                        "复制的依赖文件数量": len(copied_files)
                    }
                    st.json(summary_data)

                    if copied_files:
                        st.markdown("**复制的文件列表**:")
                        for f in copied_files[:20]:  # 最多显示20个
                            st.text(f"  • {f}")
                        if len(copied_files) > 20:
                            st.text(f"  ... 还有 {len(copied_files) - 20} 个文件")

                    if skipped_files:
                        st.markdown("**复制失败的文件**:")
                        for f in skipped_files:
                            st.text(f"  ⚠️ {f}")

            # 保存到session state
            st.session_state.current_fst = fst_path
            st.session_state.current_dir = case_dir

    st.markdown("---")

    # 运行仿真按钮
    if st.button("▶️ 运行 OpenFAST 仿真", type="primary", width='stretch', disabled="current_fst" not in st.session_state):
        if "current_fst" in st.session_state:
            fst_path = st.session_state.current_fst
            working_dir = st.session_state.current_dir

            st.session_state.working_dir = working_dir

            if "simulation_output" in st.session_state:
                del st.session_state.simulation_output
            if "simulation_success" in st.session_state:
                del st.session_state.simulation_success

            st.info(f"📂 工作目录: {working_dir}")

            output_placeholder = st.empty()
            status_placeholder = st.empty()

            with output_placeholder:
                st.code("正在启动 OpenFAST...", language="", height=400)

            fst_name = os.path.basename(fst_path)
            try:
                # 获取自定义 OpenFAST 路径（如果有）
                openfast_exe = st.session_state.get('custom_openfast_path', OPENFAST_EXE) if st.session_state.get('use_custom_openfast', False) else OPENFAST_EXE

                process = subprocess.Popen(
                    [openfast_exe, fst_name],
                    cwd=working_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                output_lines = []
                line_count = 0

                for line in process.stdout:
                    output_lines.append(line.rstrip())
                    line_count += 1

                    if line_count % 3 == 0:
                        current_output = "\n".join(output_lines)
                        with output_placeholder:
                            st.code(current_output, language="", height=400)

                return_code = process.wait()
                success = return_code == 0
                final_output = "\n".join(output_lines)

                st.session_state.simulation_output = final_output
                st.session_state.simulation_success = success

                if success:
                    with status_placeholder:
                        st.success("✅ 仿真运行成功!")
                else:
                    with status_placeholder:
                        st.error("❌ 仿真运行失败!")

            except Exception as e:
                with output_placeholder:
                    st.code(f"错误: {str(e)}", language="", height=400)
                with status_placeholder:
                    st.error("❌ 仿真运行失败!")

    st.markdown("---")

    if "simulation_success" in st.session_state and "simulation_output" in st.session_state:
        if st.session_state.simulation_success:
            st.subheader("📊 生成的文件")
            working_dir = st.session_state.get("working_dir", "")
            if working_dir and os.path.exists(working_dir):
                result_files = sorted(os.listdir(working_dir))
                for file in result_files:
                    file_path = os.path.join(working_dir, file)
                    if os.path.isfile(file_path):
                        size_kb = os.path.getsize(file_path) / 1024
                        st.text(f"📄 {file} ({size_kb:.2f} KB)")

                with st.expander("📥 下载结果文件"):
                    for file in result_files:
                        file_path = os.path.join(working_dir, file)
                        if os.path.isfile(file_path):
                            with open(file_path, 'rb') as f:
                                st.download_button(
                                label=f"⬇️ 下载 {file}",
                                data=f,
                                file_name=file,
                                mime="application/octet-stream",
                                key=f"download_{file}"
                                )

    st.markdown("---")

    # ==================== 结果可视化模块 ====================
    st.subheader("📈 结果数据可视化")

    if "working_dir" in st.session_state and st.session_state.working_dir:
        working_dir = st.session_state.working_dir

        # 查找结果文件
        result_files = []
        for file in os.listdir(working_dir):
            if file.endswith('.out') and not file.endswith('.MD.out'):
                result_files.append(os.path.join(working_dir, file))
            elif file.endswith('.outb'):
                result_files.append(os.path.join(working_dir, file))

        if result_files:
            # 优先选择二进制格式(.outb)，然后是文本格式(.out)
            result_files.sort(key=lambda x: (not x.endswith('.outb'), x))
            result_file = result_files[0]

            st.info(f"📂 正在读取: {os.path.basename(result_file)}")

            # 读取结果数据
            data = None
            channel_names = []
            channel_units = []
            desc_str = ""

            try:
                if result_file.endswith('.out'):
                    # 读取文本格式
                    data, channel_names, channel_units, desc_str = read_fast_text(result_file)
                elif result_file.endswith('.outb'):
                    # 读取二进制格式
                    data, channel_names, channel_units, desc_str = read_fast_binary(result_file)

                if data is not None and len(data) > 0:
                    # 显示文件描述信息
                    if desc_str:
                        st.caption(f"📄 {desc_str}")
                    # 创建DataFrame
                    df = pd.DataFrame(data, columns=channel_names)

                    # 显示前10行数据
                    st.markdown("#### 📋 数据预览（前10行）")
                    st.dataframe(df.head(10), width='stretch', height=300)

                    st.markdown("---")

                    # 可视化选择
                    st.markdown("#### 📊 图表绘制")

                    # 指标说明字典（完整版）
                    channel_descriptions = {
                        "Time": "时间",
                        # === 发电机相关 ===
                        "GenSpeed": "发电机转速",
                        "GenPwr": "发电机功率",
                        "GenTq": "发电机扭矩",
                        "RotSpeed": "转子转速",
                        "RotPwr": "转子功率",
                        "RotTorq": "转子扭矩",
                        "BldPitch1": "叶片1变桨角",
                        "BldPitch2": "叶片2变桨角",
                        "BldPitch3": "叶片3变桨角",
                        "BldPitch1Com": "叶片1指令变桨角",
                        "BldPitch2Com": "叶片2指令变桨角",
                        "BldPitch3Com": "叶片3指令变桨角",
                        # === 平台运动（平动） ===
                        "PtfmSurge": "平台纵荡",
                        "PtfmSway": "平台横荡",
                        "PtfmHeave": "平台垂荡",
                        # === 平台运动（转动） ===
                        "PtfmPitch": "平台纵摇",
                        "PtfmRoll": "平台横摇",
                        "PtfmYaw": "平台艏摇",
                        # === 平台平动速度 ===
                        "PtfmTVxi": "平台纵荡速度",
                        "PtfmTVyi": "平台横荡速度",
                        "PtfmTVzi": "平台垂荡速度",
                        # === 平台转动速度 ===
                        "PtfmRVxi": "平台横摇角速度",
                        "PtfmRVyi": "平台纵摇角速度",
                        "PtfmRVzi": "平台艏摇角速度",
                        # === 平台平动加速度 ===
                        "PtfmTAxi": "平台纵荡加速度",
                        "PtfmTAyi": "平台横荡加速度",
                        "PtfmTAzi": "平台垂荡加速度",
                        # === 平台转动加速度 ===
                        "PtfmRAxi": "平台横摇角加速度",
                        "PtfmRAyi": "平台纵摇角加速度",
                        "PtfmRAzi": "平台艏摇角加速度",
                        # === 平台相对运动 ===
                        "PtfmADxt": "平台相对纵向位移",
                        "PtfmADyt": "平台相对侧向位移",
                        "PtfmADzt": "平台相对垂向位移",
                        "WRPSurge": "浮台参考点纵荡",
                        "WRPPitch": "浮台参考点纵摇",
                        "WRPYaw": "浮台参考点艏摇",
                        # === 塔架相关 ===
                        "YawBrTDxp": "塔顶前后位移",
                        "YawBrTDyp": "塔顶侧向位移",
                        "YawBrTDzt": "塔顶垂向位移",
                        "YawBrRDxt": "塔顶横向转角",
                        "YawBrRDyt": "塔顶纵向转角",
                        "YawBrRDzt": "塔顶垂直转角",
                        "YawBrRVxp": "塔顶横向角速度",
                        "YawBrRVyp": "塔顶纵向角速度",
                        "YawBrRVzp": "塔顶垂直角速度",
                        "YawBrTAxp": "塔顶横向角加速度",
                        "YawBrTAyp": "塔顶纵向角加速度",
                        "YawBrTAzp": "塔顶垂直角加速度",
                        # === 低速轴相关 ===
                        "LSShftTq": "低速轴扭矩",
                        "LSShftFxa": "低速轴纵向力",
                        "LSShftFys": "低速轴侧向剪力",
                        "LSShftFzs": "低速轴垂向剪力",
                        "LSShftMxs": "低速轴滚转弯矩",
                        "LSSTipMys": "叶片俯仰弯矩",
                        "LSSTipMzs": "叶片偏航弯矩",
                        # === 转子相关 ===
                        "RotSpeed": "转子转速",
                        "RotThrust": "转子推力",
                        "RotTorq": "转子扭矩",
                        "RotPwr": "转子功率",
                        "RtAeroFxh": "转子气动推力",
                        "RtAeroFyh": "转子侧向气动力",
                        "RtAeroFzh": "转子垂向气动力",
                        "RtAeroMxh": "转子滚转气动力矩",
                        "RtAeroMyh": "转子俯仰气动力矩",
                        "RtAeroMzh": "转子偏航气动力矩",
                        # === 水动力载荷 ===
                        "HydroFxi": "水动力纵向载荷",
                        "HydroFyi": "水动力侧向载荷",
                        "HydroFzi": "水动力垂向载荷",
                        "HydroMxi": "水动力滚转力矩",
                        "HydroMyi": "水动力俯仰力矩",
                        "HydroMzi": "水动力偏航力矩",
                        # === 波浪载荷 ===
                        "WavesFxi": "波浪纵向激励载荷",
                        "WavesFyi": "波浪侧向激励载荷",
                        "WavesFzi": "波浪垂向激励载荷",
                        "WavesMxi": "波浪滚转激励力矩",
                        "WavesMyi": "波浪俯仰激励力矩",
                        "WavesMzi": "波浪偏航激励力矩",
                        "Wave1Elev": "波面高度",
                        "Wave1Time": "波浪时间",
                        "Wave1PeakDt": "波浪峰值周期",
                        # === 锚链载荷 ===
                        "FAIRTEN1": "锚链1张力",
                        "FAIRTEN2": "锚链2张力",
                        "FAIRTEN3": "锚链3张力",
                        "FAIRTEN4": "锚链4张力",
                        "FAIRTEN5": "锚链5张力",
                        "FAIRTEN6": "锚链6张力",
                        "FAIRTEN7": "锚链7张力",
                        "FAIRTEN8": "锚链8张力",
                        "FAIRTEN9": "锚链9张力",
                        "FAIRTEN10": "锚链10张力",
                        # === 锚链力 ===
                        "L2N1FX": "锚链1纵向力",
                        "L2N1FY": "锚链1侧向力",
                        "L2N1FZ": "锚链1垂向力",
                        "L2N1T": "锚链1张力",
                        "L2N1PX": "锚链1位置X",
                        "L2N1PY": "锚链1位置Y",
                        "L2N1PZ": "锚链1位置Z",
                        "L2N2FX": "锚链2纵向力",
                        "L2N2FY": "锚链2侧向力",
                        "L2N2FZ": "锚链2垂向力",
                        "L2N2T": "锚链2张力",
                        # === 环境条件 ===
                        "Wind1VelX": "风速X分量",
                        "Wind1VelY": "风速Y分量",
                        "Wind1VelZ": "风速Z分量",
                        "RtVavgxh": "轮毂相对平均风速",
                        # === 叶片根部载荷 ===
                        "RootFxb1": "叶片1根部纵向力",
                        "RootFyb1": "叶片1根部侧向力",
                        "RootFzb1": "叶片1根部垂向力",
                        "RootMxb1": "叶片1根部滚转力矩",
                        "RootMyb1": "叶片1根部俯仰力矩",
                        "RootMzb1": "叶片1根部偏航力矩",
                        "RootFxb2": "叶片2根部纵向力",
                        "RootFyb2": "叶片2根部侧向力",
                        "RootFzb2": "叶片2根部垂向力",
                        "RootMxb2": "叶片2根部滚转力矩",
                        "RootMyb2": "叶片2根部俯仰力矩",
                        "RootMzb2": "叶片2根部偏航力矩",
                        "RootFxb3": "叶片3根部纵向力",
                        "RootFyb3": "叶片3根部侧向力",
                        "RootFzb3": "叶片3根部垂向力",
                        "RootMxb3": "叶片3根部滚转力矩",
                        "RootMyb3": "叶片3根部俯仰力矩",
                        "RootMzb3": "叶片3根部偏航力矩",
                        # === 叶片载荷 ===
                        "Spn1ALxb1": "叶片1截面1纵向力",
                        "Spn1ALyb1": "叶片1截面1侧向力",
                        "Spn1ALzb1": "叶片1截面1垂向力",
                        "Spn1AMxb1": "叶片1截面1滚转力矩",
                        "Spn1AMyb1": "叶片1截面1俯仰力矩",
                        "Spn1AMzb1": "叶片1截面1偏航力矩",
                        # === 变桨相关 ===
                        "BldPitch1": "叶片1变桨角",
                        "BldPitch2": "叶片2变桨角",
                        "BldPitch3": "叶片3变桨角",
                        # === 控制器相关 ===
                        "PC_TI_ACP": "变桨指令",
                        "GenTq_Req": "发电机扭矩需求",
                        # === 其他 ===
                        "Q_B1E1": "叶片1模态位移",
                        "Q_B2E1": "叶片2模态位移",
                        "Q_B3E1": "叶片3模态位移",
                        }

                    # 创建三个列布局
                    col_viz1, col_viz2, col_viz3 = st.columns([2, 2, 1])

                    with col_viz1:
                        # 排除Time列的可选指标
                        available_channels = [ch for ch in channel_names if ch != 'Time']

                        # 创建带说明的选项标签
                        channel_options_with_desc = {}
                        for ch in available_channels:
                            desc = channel_descriptions.get(ch, "")
                            if desc:
                                channel_options_with_desc[ch] = f"{ch} · {desc}"
                            else:
                                channel_options_with_desc[ch] = ch

                        selected_channels = st.multiselect(
                            "选择要绘制的指标",
                            options=available_channels,
                            default=available_channels[:5] if len(available_channels) >= 5 else available_channels,
                            format_func=lambda x: channel_options_with_desc.get(x, x),
                            help="可以选择多个指标同时绘制"
                        )

                        with col_viz2:
                            chart_type = st.selectbox(
                            "图表类型",
                            ["折线图", "散点图", "面积图"],
                            index=0
                        )

                        with col_viz3:
                            show_grid = st.checkbox("显示网格", value=True)
                            show_legend = st.checkbox("显示图例", value=True)

                        # 绘图按钮
                        if st.button("🎨 生成图表", type="primary", width='stretch') and selected_channels:
                            fig = go.Figure()

                            # 添加Time列
                            if 'Time' in channel_names:
                                x_data = df['Time']
                                x_label = f"Time ({channel_units[channel_names.index('Time')] if channel_names.index('Time') < len(channel_units) else 's'})"
                            else:
                                x_data = df.index
                                x_label = "Index"

                            for channel in selected_channels:
                                if channel in channel_names:
                                    y_data = df[channel]
                                unit = channel_units[channel_names.index(channel)] if channel_names.index(channel) < len(channel_units) else ""
                                label = f"{channel} ({unit})" if unit else channel

                                if chart_type == "折线图":
                                    fig.add_trace(go.Scatter(
                                x=x_data,
                                y=y_data,
                                mode='lines',
                                name=label,
                                line=dict(width=2)
                                ))
                                elif chart_type == "散点图":
                                    fig.add_trace(go.Scatter(
                                x=x_data,
                                y=y_data,
                                mode='markers',
                                name=label,
                                marker=dict(size=4)
                                ))
                                elif chart_type == "面积图":
                                    fig.add_trace(go.Scatter(
                                x=x_data,
                                y=y_data,
                                mode='lines',
                                name=label,
                                fill='tozeroy',
                                line=dict(width=1)
                                ))

                            fig.update_layout(
                                title="OpenFAST 仿真结果",
                                xaxis_title=x_label,
                                yaxis_title="数值",
                                hovermode='x unified',
                                height=500,
                                showlegend=show_legend,
                                plot_bgcolor='white',
                                paper_bgcolor='white',
                                font=dict(size=12)
                            )

                            if show_grid:
                                fig.update_xaxes(showgrid=True, gridcolor='lightgray')
                                fig.update_yaxes(showgrid=True, gridcolor='lightgray')

                            st.plotly_chart(fig, width='stretch')

                            # 统计信息
                            with st.expander("📊 统计信息"):
                                stats_cols = st.columns(len(selected_channels))
                                for i, channel in enumerate(selected_channels):
                                    if channel in channel_names:
                                        col = stats_cols[i]
                                data_series = df[channel]
                                col.metric(
                                label=channel,
                                value=f"{data_series.mean():.4f}",
                                delta=f"±{data_series.std():.4f}"
                                )
                                col.caption(f"Min: {data_series.min():.4f}")
                                col.caption(f"Max: {data_series.max():.4f}")
            except Exception as e:
                st.error(f"❌ 读取文件失败: {str(e)}")
            else:
                st.warning("⚠️ 未找到结果文件 (.out 或 .outb)")
    else:
        st.info("💡 请先运行仿真，然后在此处查看可视化结果")

    # ==================== VTK 3D 可视化模块 ====================
    st.markdown("---")
    st.subheader("🎬 VTK 3D 可视化")

    # 获取当前 WrVTK 值 - 优先使用用户在前端修改后的值
    # 由于 Streamlit 的执行机制，param_values 可能已经包含了用户最新的修改
    # 因此我们优先从 param_values 获取，其次使用 session_state 缓存的值，最后使用原始文件值
    wrvtk_current = None
    source_text = "未知"

    # 方法1: 尝试从 session_state 获取最新值（用户修改参数时会更新这里）
    if 'WrVTK' in st.session_state:
        wrvtk_current = st.session_state.WrVTK
        source_text = "Session State (最新修改)"

    # 方法2: 尝试从 param_values 获取
    if wrvtk_current is None and 'param_values' in locals() and 'WrVTK' in param_values:
        wrvtk_current = param_values["WrVTK"]
        source_text = "前端参数设置"

    # 方法3: 使用原始文件值
    if wrvtk_current is None:
        wrvtk_current = get_fst_value("WrVTK", current_fst_param_info)
        source_text = "FST 文件原始值"

    # 保存到 session_state 以便后续使用
    st.session_state.WrVTK = wrvtk_current

    vtk_status_text = {
        0: "❌ 未启用 (0)",
        1: "📝 仅初始化 (1)",
        2: "✅ 动画输出 (2)",
        3: "✅ 模态形状 (3)"
    }
    wrvtk_status = vtk_status_text.get(wrvtk_current, f"❓ 未知值 ({wrvtk_current})")

    # 显示当前状态
    col_vtk_info1, col_vtk_info2 = st.columns([3, 1])
    with col_vtk_info1:
        st.info(f"📊 当前 WrVTK 设置: {wrvtk_status}")
    with col_vtk_info2:
        if st.button("🔄 刷新", key="refresh_vtk_status", help="刷新 VTK 状态"):
            st.rerun()

    # 检查是否启用了VTK输出 - 使用用户当前设置的值
    wrvtk_enabled = False
    if wrvtk_current and wrvtk_current != 0:
        wrvtk_enabled = True

    if not wrvtk_enabled:
        st.info("💡 VTK可视化未启用。请在【可视化设置】标签页中设置 'WrVTK' 参数为 2（动画）或 3（模态形状），然后重新运行仿真。")
    elif "working_dir" in st.session_state and st.session_state.working_dir:
        # 查找VTK文件 - 在vtk子目录下
        working_dir = st.session_state.working_dir
        vtk_dir = os.path.join(working_dir, "vtk")

        if not os.path.exists(vtk_dir):
            st.warning(f"⚠️ 未找到vtk目录: {vtk_dir}")
            st.info("💡 请确保仿真已完成且WrVTK参数设置正确。")
        else:
            # 按时间步组织VTK文件
            vtk_files = sorted([f for f in os.listdir(vtk_dir) if f.endswith('.vtp') or f.endswith('.vtk') or f.endswith('.vtu')])

            if not vtk_files:
                st.warning("⚠️ 未找到VTK文件。请确保仿真已成功完成并生成了VTK输出。")
            else:
                st.success(f"✅ 找到 {len(vtk_files)} 个VTK文件，位于 `vtk/` 目录")

                # 分析文件命名模式，按时间步分组
                # OpenFAST VTK文件通常命名为: FAST.<Component>.<Timestep>.vtp
                timestep_groups = {}
                for filename in vtk_files:
                    # 尝试提取时间步（通常是最后一段数字）
                    parts = filename.split('.')
                    timestep = None
                    component = filename

                    # 查找数字部分作为时间步
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            timestep = int(part)
                            # 组件名是时间步之前的部分
                            component = '.'.join(parts[:i]) if i > 0 else 'unknown'
                            break

                    if timestep is None:
                        # 没有找到时间步，使用文件索引
                        timestep = len(timestep_groups)
                        component = filename.replace('.vtp', '').replace('.vtk', '').replace('.vtu', '')

                    if timestep not in timestep_groups:
                        timestep_groups[timestep] = []
                    timestep_groups[timestep].append({
                        'filename': filename,
                        'path': os.path.join(vtk_dir, filename),
                        'component': component
                    })

                # 按时间步排序
                sorted_timesteps = sorted(timestep_groups.keys())

                # 显示文件信息
                with st.expander("📁 VTK文件信息"):
                    st.write(f"**总文件数**: {len(vtk_files)}")
                    st.write(f"**时间步数**: {len(sorted_timesteps)}")
                    st.write(f"**每步文件数**: {len(list(timestep_groups.values())[0]) if timestep_groups else 0}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**时间步分布**:")
                        for ts in sorted_timesteps[:10]:
                            st.text(f"  时间步 {ts}: {len(timestep_groups[ts])} 个文件")
                        if len(sorted_timesteps) > 10:
                            st.text(f"  ... 共 {len(sorted_timesteps)} 个时间步")
                    with col_b:
                        st.markdown("**组件示例**:")
                        if sorted_timesteps:
                            components = set([f['component'] for f in timestep_groups[sorted_timesteps[0]]])
                            for comp in list(components)[:5]:
                                st.text(f"  - {comp}")

                st.markdown("---")

                # VTK可视化控制面板
                st.markdown("#### 🎮 可视化控制")

                col_vtk1, col_vtk2, col_vtk3 = st.columns([2, 1, 1])

                with col_vtk1:
                    # 显示选项
                    show_edges = st.checkbox("显示边框", value=False)
                    show_axes = st.checkbox("显示坐标轴", value=True)

                with col_vtk3:
                    # 背景颜色
                    bg_color = st.selectbox(
                        "背景颜色",
                        ["白色", "黑色", "深灰", "浅灰"],
                        index=0
                    )
                    bg_map = {"白色": "white", "黑色": "black", "深灰": "#2b2b2b", "浅灰": "#f0f0f0"}
                    bg_hex = bg_map[bg_color]

                st.markdown("---")

                # 定义VTK文件加载函数
                @st.cache_data(ttl=3600)
                def load_vtk_file(vtk_path):
                    """缓存VTK文件加载"""
                    try:
                        mesh = pv.read(vtk_path)
                        return mesh
                    except Exception:
                        return None

                # 定义颜色映射（为不同组件分配不同颜色）
                component_colors = {}

                def get_component_color(component_name):
                    """根据组件名称返回颜色"""
                    if component_name not in component_colors:
                        # 为新组件分配颜色
                        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
                                '#1abc9c', '#e67e22', '#34495e', '#7f8c8d', '#16a085']
                        idx = len(component_colors) % len(colors)
                        component_colors[component_name] = colors[idx]
                    return component_colors[component_name]

                # 渲染指定时间步的所有VTK文件
                def render_timestep(timestep_idx):
                    """渲染指定时间步的所有VTK文件"""
                    if timestep_idx >= len(sorted_timesteps):
                        return None

                    timestep = sorted_timesteps[timestep_idx]
                    files_in_timestep = timestep_groups[timestep]

                    # 创建绘图器
                    plotter = pv.Plotter(window_size=[1000, 700])
                    plotter.set_background(bg_hex)
                    plotter.enable_anti_aliasing()

                    # 设置交互样式：启用Ctrl+左键平移
                    plotter.enable_trackball_style()
                    # 或者使用默认样式，但添加额外的按键绑定
                    # plotter.add_text("Ctrl+左键: 平移 | 左键: 旋转 | 滚轮: 缩放", position='upper_left', font_size=8)

                    # 加载并添加所有网格
                    total_points = 0
                    total_cells = 0
                    components_loaded = []

                    for file_info in files_in_timestep:
                        mesh = load_vtk_file(file_info['path'])
                        if mesh is not None:
                            color = get_component_color(file_info['component'])
                            plotter.add_mesh(
                                mesh,
                                color=color,
                                show_edges=show_edges,
                                edge_color="black" if show_edges else None,
                                label=file_info['component']
                            )
                            total_points += mesh.n_points
                            total_cells += mesh.n_cells
                            components_loaded.append(file_info['component'])

                    # 添加坐标轴
                    if show_axes:
                        plotter.add_axes()

                    # 添加图例
                    if len(components_loaded) > 1:
                        plotter.add_legend(bcolor=(0.1, 0.1, 0.1, 0.5), face='circle', size=(0.3, 0.2))

                    # 设置为等轴测视图
                    plotter.view_isometric()

                    return plotter, total_points, total_cells, components_loaded

                # 单帧查看模式
                col_frame, col_view = st.columns([1, 3])

                with col_frame:
                    st.markdown("**选择帧**")
                    frame_index = st.slider(
                        "时间步",
                        min_value=0,
                        max_value=len(sorted_timesteps) - 1,
                        value=0,
                        step=1
                    )

                    st.caption(f"时间步编号: {sorted_timesteps[frame_index]}")

                    # 预设视图
                    st.markdown("**视图角度**")
                    view_preset = st.selectbox(
                        "快速定位",
                        ["等轴测", "前视图", "后视图", "左视图", "右视图", "顶视图", "底视图"],
                        index=0
                    )

                with col_view:
                    result = render_timestep(frame_index)
                    if result:
                        plotter, total_points, total_cells, components = result

                        # 设置视图
                        view_map = {
                            "等轴测": lambda: plotter.view_isometric(),
                            "前视图": lambda: plotter.view_xy(),
                            "后视图": lambda: plotter.view_xy(negative=True),
                            "左视图": lambda: plotter.view_yz(),
                            "右视图": lambda: plotter.view_yz(negative=True),
                            "顶视图": lambda: plotter.view_xz(),
                            "底视图": lambda: plotter.view_xz(negative=True),
                        }
                        view_map[view_preset]()

                        # 导出HTML
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                            temp_html_path = f.name
                        plotter.export_html(temp_html_path)
                        with open(temp_html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        os.unlink(temp_html_path)
                        st.components.v1.html(html_content, height=700, scrolling=False)
                        # 显示网格信息
                        with st.expander("📊 网格信息"):
                            st.write(f"**总点数**: {total_points:,}")
                            st.write(f"**总单元数**: {total_cells:,}")
                            st.write(f"**组件数**: {len(components)}")
                            st.write("**加载的组件**:")
                            for comp in components:
                                color = get_component_color(comp)
                                st.markdown(f"<span style='color:{color}'>■</span> {comp}", unsafe_allow_html=True)

                # 使用说明
                with st.expander("💡 交互说明"):
                    st.markdown("""
                    **鼠标操作**:
                        - 左键拖动: 旋转视角
                    - 滚轮滚动: 缩放

                    **使用说明**:
                        - 选择帧：通过滑块选择要查看的时间步
                    - 切换视图：使用预设视图按钮快速切换角度

                    **模型说明**:
                        - 不同组件使用不同颜色显示
                    - 图例显示各组件对应的颜色
                    """)


# ==================== 批量化仿真板块 ====================
with main_tabs[1]:
    st.markdown("### 🔢 批量化仿真设置")
    st.markdown("---")

    # 初始化批量仿真的 session_state
    if 'batch_case_folders' not in st.session_state:
        st.session_state.batch_case_folders = []
    if 'batch_param_values' not in st.session_state:
        st.session_state.batch_param_values = {}

    st.markdown("#### 📂 批量案例文件夹导入")

    col_browse1, col_browse2 = st.columns([3, 1])

    with col_browse1:
        st.caption("💡 选择包含完整仿真案例的文件夹（每个文件夹应包含 .fst 和 .dat 等文件）")

    with col_browse2:
        if st.button("🗑️ 清空列表", key="clear_batch_folders"):
            st.session_state.batch_case_folders = []
            st.session_state.batch_param_values = {}
            st.rerun()

    # ============= 批量导入区域 =============
    st.markdown("---")
    st.markdown("#### 📦 批量导入案例")

    # Tab切换不同的导入方式
    import_tabs = st.tabs(["📂 浏览父文件夹批量导入", "📝 输入路径批量导入", "➕ 快速添加单个"])

    with import_tabs[0]:
        st.markdown("**选择包含多个案例文件夹的父目录**")
        st.caption("💡 例如：选择 `D:\\cases`，系统会自动扫描并列出其中所有包含 .fst 文件的子文件夹")

        # 初始化父文件夹路径状态
        if 'parent_folder_value' not in st.session_state:
            st.session_state.parent_folder_value = ""

        # 显示当前使用的路径
        if st.session_state.parent_folder_value:
            st.info(f"📂 当前路径: `{st.session_state.parent_folder_value}`")

        col_p1, col_p2, col_p3, col_p4 = st.columns([4, 2, 2, 2])
        with col_p1:
            # 手动输入路径
            input_folder = st.text_input("父文件夹路径", placeholder=r"D:\software\openfast-4.2.1\cert_tests", key="parent_folder_tab1", label_visibility="collapsed")
        with col_p2:
            if st.button("📂 浏览...", key="browse_parent_tab1", use_container_width=True):
                selected = select_multiple_directories()
                if selected:
                    st.session_state.parent_folder_value = selected[0]
                    st.rerun()
        with col_p3:
            if st.button("✅ 使用输入路径", key="use_input_path", use_container_width=True):
                if input_folder:
                    st.session_state.parent_folder_value = input_folder
                    st.rerun()
        with col_p4:
            if st.button("🔄 刷新", key="refresh_folders", use_container_width=True):
                st.rerun()

        # 使用存储的路径值
        parent_folder = st.session_state.parent_folder_value

        # 显示可用的子文件夹
        if parent_folder and os.path.exists(parent_folder):
            # 扫描所有子文件夹
            available_folders = []
            for item in os.listdir(parent_folder):
                item_path = os.path.join(parent_folder, item)
                if os.path.isdir(item_path):
                    try:
                        fst_files = [f for f in os.listdir(item_path) if f.endswith('.fst')]
                        if fst_files:
                            already_imported = any(f['path'] == item_path for f in st.session_state.batch_case_folders)
                            available_folders.append({
                                'name': item,
                                'path': item_path,
                                'fst_file': fst_files[0],
                                'imported': already_imported
                            })
                    except:
                        pass

            if available_folders:
                st.markdown(f"**找到 {len(available_folders)} 个案例文件夹**")

                # 全选/取消全选按钮
                col_sel1, col_sel2, col_sel3 = st.columns([2, 2, 8])
                with col_sel1:
                    if st.button("✅ 全选未导入", key="select_all_folders", use_container_width=True):
                        for idx, folder in enumerate(available_folders):
                            if not folder['imported']:
                                st.session_state[f"folder_select_tab1_{idx}"] = True
                        st.rerun()
                with col_sel2:
                    if st.button("❌ 取消全选", key="deselect_all_folders", use_container_width=True):
                        for idx, folder in enumerate(available_folders):
                            if not folder['imported']:
                                st.session_state[f"folder_select_tab1_{idx}"] = False
                        st.rerun()

                # 显示复选框列表（使用grid布局）
                # 分列显示
                cols_per_row = 3
                for row_start in range(0, len(available_folders), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for col_idx in range(cols_per_row):
                        idx = row_start + col_idx
                        if idx < len(available_folders):
                            folder = available_folders[idx]
                            with cols[col_idx]:
                                status_icon = "✅" if folder['imported'] else "📁"
                                label = f"{status_icon} **{folder['name']}**\n<{folder['fst_file']}>"
                                st.checkbox(
                                    label,
                                    value=False,
                                    key=f"folder_select_tab1_{idx}",
                                    disabled=folder['imported'],
                                    label_visibility="visible"
                                )

                # 批量导入按钮
                st.markdown("---")
                if st.button("📥 批量导入选中的案例文件夹", key="import_batch_tab1", type="primary", use_container_width=True):
                    added_count = 0
                    for idx, folder in enumerate(available_folders):
                        if not folder['imported'] and st.session_state.get(f"folder_select_tab1_{idx}", False):
                            try:
                                fst_path = os.path.join(folder['path'], folder['fst_file'])
                                fst_param_info = parse_fst_file(fst_path)
                                st.session_state.batch_case_folders.append({
                                    'name': folder['name'],
                                    'path': folder['path'],
                                    'original_path': folder['path'],
                                    'fst_file': folder['fst_file'],
                                    'fst_path': fst_path,
                                    'param_info': fst_param_info
                                })
                                added_count += 1
                            except Exception as e:
                                st.error(f"❌ {folder['name']}: {str(e)}")
                    if added_count > 0:
                        st.success(f"✅ 成功导入 {added_count} 个案例文件夹！")
                        st.rerun()
                    else:
                        st.warning("⚠️ 请先勾选要导入的文件夹")
            else:
                st.info("⚠️ 在父文件夹中未找到包含 .fst 文件的子文件夹")
        elif parent_folder:
            st.warning("⚠️ 文件夹路径不存在")

    with import_tabs[1]:
        st.markdown("**输入多个案例文件夹的路径（每行一个）**")
        st.caption("💡 复制粘贴多个文件夹路径，每行一个")

        folder_paths = st.text_area(
            "案例文件夹路径列表",
            placeholder=r"D:\cases\case1\nD:\cases\case2\nD:\cases\case3",
            height=150,
            key="manual_paths_input"
        )

        if st.button("📥 批量导入", key="import_manual_paths", type="primary", use_container_width=True):
            paths = [p.strip() for p in folder_paths.strip().split('\n') if p.strip()]
            if paths:
                added_count = 0
                for path in paths:
                    if os.path.exists(path) and os.path.isdir(path):
                        fst_files = [f for f in os.listdir(path) if f.endswith('.fst')]
                        if fst_files and not any(f['path'] == path for f in st.session_state.batch_case_folders):
                            try:
                                fst_path = os.path.join(path, fst_files[0])
                                fst_param_info = parse_fst_file(fst_path)
                                st.session_state.batch_case_folders.append({
                                    'name': os.path.basename(path),
                                    'path': path,
                                    'original_path': path,
                                    'fst_file': fst_files[0],
                                    'fst_path': fst_path,
                                    'param_info': fst_param_info
                                })
                                added_count += 1
                            except Exception as e:
                                st.error(f"❌ {os.path.basename(path)}: {str(e)}")
                if added_count > 0:
                    st.success(f"✅ 成功导入 {added_count} 个案例文件夹！")
                    st.rerun()
                else:
                    st.warning("⚠️ 没有新的案例被导入")
            else:
                st.warning("⚠️ 请输入至少一个文件夹路径")

    with import_tabs[2]:
        st.markdown("**快速添加单个案例文件夹**")
        if st.button("📂 选择文件夹", key="quick_single_import", use_container_width=True):
            selected = select_multiple_directories()
            if selected:
                path = selected[0]
                fst_files = [f for f in os.listdir(path) if f.endswith('.fst')]
                if fst_files and not any(f['path'] == path for f in st.session_state.batch_case_folders):
                    try:
                        fst_path = os.path.join(path, fst_files[0])
                        fst_param_info = parse_fst_file(fst_path)
                        st.session_state.batch_case_folders.append({
                            'name': os.path.basename(path),
                            'path': path,
                            'original_path': path,
                            'fst_file': fst_files[0],
                            'fst_path': fst_path,
                            'param_info': fst_param_info
                        })
                        st.success(f"✅ 成功添加: {os.path.basename(path)}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 解析失败: {str(e)}")
                elif fst_files:
                    st.info("ℹ️ 该案例已存在")
                else:
                    st.warning("⚠️ 文件夹中没有 .fst 文件")

    # 显示已导入的案例文件夹列表
    if st.session_state.batch_case_folders:
        st.markdown(f"**已导入 {len(st.session_state.batch_case_folders)} 个案例文件夹**:")

        # 使用可展开的列表显示每个案例
        for i, case in enumerate(st.session_state.batch_case_folders):
            with st.expander(f"📁 {case['name']}", expanded=False):
                col_info1, col_info2, col_info3 = st.columns([3, 1, 1])

                with col_info1:
                    st.caption(f"FST 文件: {case['fst_file']}")
                    st.caption(f"参数数量: {len(case['param_info'])}")
                    st.caption(f"路径: `{case['path']}`")

                with col_info2:
                    if st.button("🗑️ 删除", key=f"delete_batch_{i}"):
                        st.session_state.batch_case_folders.pop(i)
                        if f'batch_params_{i}' in st.session_state.batch_param_values:
                            del st.session_state.batch_param_values[f'batch_params_{i}']
                        st.rerun()

                with col_info3:
                    if st.button("⚙️ 编辑", key=f"edit_batch_{i}"):
                        st.session_state[f'edit_batch_case_{i}'] = not st.session_state.get(f'edit_batch_case_{i}', False)
                        st.rerun()

                # 如果点击了编辑，显示参数修改界面
                if st.session_state.get(f'edit_batch_case_{i}', False):
                    st.markdown("**参数修改**:")

                    # 获取或创建参数缓存
                    param_key = f'batch_params_{i}'
                    if param_key not in st.session_state.batch_param_values:
                        st.session_state.batch_param_values[param_key] = {}

                    # 创建参数编辑界面
                    batch_param_values = {}
                    edit_tabs = st.tabs([
                        "仿真控制", "功能开关", "环境条件", "输出设置", "线性化", "可视化"
                    ])

                    # 仿真控制
                    with edit_tabs[0]:
                        st.markdown("#### ⚙️ 仿真控制参数")
                        col1, col2 = st.columns(2)
                        with col1:
                            batch_param_values["Echo"] = render_parameter_input(
                                "Echo", "bool",
                                get_fst_value("Echo", case['param_info']),
                                None, f"BATCH_SIM_CTRL_{i}", i
                            )
                            batch_param_values["AbortLevel"] = render_parameter_input(
                                "AbortLevel", "select",
                                get_fst_value("AbortLevel", case['param_info']),
                                ["WARNING", "SEVERE", "FATAL"], f"BATCH_SIM_CTRL_{i}", i
                            )
                            batch_param_values["TMax"] = render_parameter_input(
                                "TMax", "float",
                                get_fst_value("TMax", case['param_info']),
                                (1.0, 10000.0), f"BATCH_SIM_CTRL_{i}", i
                            )
                            batch_param_values["DT"] = render_parameter_input(
                                "DT", "float",
                                get_fst_value("DT", case['param_info']),
                                (0.001, 1.0), f"BATCH_SIM_CTRL_{i}", i
                            )
                        with col2:
                            batch_param_values["InterpOrder"] = render_parameter_input(
                                "InterpOrder", "int",
                                get_fst_value("InterpOrder", case['param_info']),
                                (1, 2), f"BATCH_SIM_CTRL_{i}", i
                            )
                            batch_param_values["NumCrctn"] = render_parameter_input(
                                "NumCrctn", "int",
                                get_fst_value("NumCrctn", case['param_info']),
                                (0, 10), f"BATCH_SIM_CTRL_{i}", i
                            )

                    # 功能开关
                    with edit_tabs[1]:
                        st.markdown("#### 🔧 功能模块开关")
                        col1, col2 = st.columns(2)
                        with col1:
                            batch_param_values["CompElast"] = render_parameter_input(
                                "CompElast", "select",
                                get_fst_value("CompElast", case['param_info']),
                                [1, 2, 3], f"BATCH_FEAT_{i}", i
                            )
                            batch_param_values["CompInflow"] = render_parameter_input(
                                "CompInflow", "select",
                                get_fst_value("CompInflow", case['param_info']),
                                [0, 1, 2], f"BATCH_FEAT_{i}", i
                            )
                        with col2:
                            batch_param_values["WrVTK"] = render_parameter_input(
                                "WrVTK", "select",
                                get_fst_value("WrVTK", case['param_info']),
                                [0, 1, 2, 3], f"BATCH_FEAT_{i}", i
                            )

                    # 环境条件
                    with edit_tabs[2]:
                        st.markdown("#### 🌍 环境条件参数")
                        col1, col2 = st.columns(2)
                        with col1:
                            batch_param_values["Gravity"] = render_parameter_input(
                                "Gravity", "float",
                                get_fst_value("Gravity", case['param_info']),
                                (0.0, 20.0), f"BATCH_ENV_{i}", i
                            )
                            batch_param_values["AirDens"] = render_parameter_input(
                                "AirDens", "float",
                                get_fst_value("AirDens", case['param_info']),
                                (0.0, 10.0), f"BATCH_ENV_{i}", i
                            )
                        with col2:
                            batch_param_values["WtrDens"] = render_parameter_input(
                                "WtrDens", "float",
                                get_fst_value("WtrDens", case['param_info']),
                                (500.0, 2000.0), f"BATCH_ENV_{i}", i
                            )
                            batch_param_values["WtrDpth"] = render_parameter_input(
                                "WtrDpth", "float",
                                get_fst_value("WtrDpth", case['param_info']),
                                (0.0, 2000.0), f"BATCH_ENV_{i}", i
                            )

                    # 输出设置
                    with edit_tabs[3]:
                        st.markdown("#### 📊 输出设置参数")
                        col1, col2 = st.columns(2)
                        with col1:
                            batch_param_values["SumPrint"] = render_parameter_input(
                                "SumPrint", "bool",
                                get_fst_value("SumPrint", case['param_info']),
                                None, f"BATCH_OUT_{i}", i
                            )
                            batch_param_values["DT_Out"] = render_parameter_input(
                                "DT_Out", "float",
                                get_fst_value("DT_Out", case['param_info']),
                                (0.0, 1.0), f"BATCH_OUT_{i}", i
                            )
                        with col2:
                            batch_param_values["OutFileFmt"] = render_parameter_input(
                                "OutFileFmt", "select",
                                get_fst_value("OutFileFmt", case['param_info']),
                                [1, 2, 3, 4, 5], f"BATCH_OUT_{i}", i
                            )

                    # 线性化
                    with edit_tabs[4]:
                        st.markdown("#### 📈 线性化分析参数")
                        col1, col2 = st.columns(2)
                        with col1:
                            batch_param_values["Linearize"] = render_parameter_input(
                                "Linearize", "bool",
                                get_fst_value("Linearize", case['param_info']),
                                None, f"BATCH_LIN_{i}", i
                            )
                        with col2:
                            batch_param_values["NLinTimes"] = render_parameter_input(
                                "NLinTimes", "int",
                                get_fst_value("NLinTimes", case['param_info']),
                                (0, 100), f"BATCH_LIN_{i}", i
                            )

                    # 可视化
                    with edit_tabs[5]:
                        st.markdown("#### 🎨 可视化设置参数")
                        st.info("💡 此处设置是否生成VTK可视化文件。生成的VTK文件可在【可视化分析】标签页中查看。")
                        col1, col2 = st.columns(2)
                        with col1:
                            batch_param_values["WrVTK"] = render_parameter_input(
                                "WrVTK", "select",
                                get_fst_value("WrVTK", case['param_info']),
                                [0, 1, 2, 3], f"BATCH_VIZ_{i}", i
                            )
                        with col2:
                            batch_param_values["VTK_type"] = render_parameter_input(
                                "VTK_type", "select",
                                get_fst_value("VTK_type", case['param_info']),
                                [1, 2, 3], f"BATCH_VIZ_{i}", i
                            )

                    # 保存参数按钮
                    col_save1, col_save2 = st.columns([1, 1])
                    with col_save1:
                        if st.button("💾 保存参数", key=f"save_batch_params_{i}"):
                            st.session_state.batch_param_values[param_key] = batch_param_values
                            st.success(f"✅ 已保存 {case['name']} 的参数（暂未应用）")
                    with col_save2:
                        if st.button("❌ 取消", key=f"cancel_batch_{i}"):
                            st.session_state[f'edit_batch_case_{i}'] = False
                            st.rerun()

        st.markdown("---")
        st.markdown("#### 🚀 批量仿真配置与运行")

        # 批量案例名称前缀
        batch_case_prefix = st.text_input("案例名称前缀", value="batch_sim", help="批量仿真的案例名称前缀")

        # 显示摘要
        st.markdown("**批量仿真摘要**:")
        st.info(f"""
        - **案例数量**: {len(st.session_state.batch_case_folders)}
        - **案例前缀**: {batch_case_prefix}
        - **结果目录**: {st.session_state.get('custom_results_dir', RESULTS_DIR) if st.session_state.get('use_custom_results', False) else RESULTS_DIR}
        """)

        col_save1, col_save2 = st.columns([1, 1])

        with col_save1:
            if st.button("💾 保存所有配置并创建案例", type="secondary", key="save_all_batch_config"):
                # 为每个案例创建新的仿真目录
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_dir = st.session_state.get('custom_results_dir', None) if st.session_state.get('use_custom_results', False) else None
                base_dir = base_dir if base_dir else RESULTS_DIR

                created_cases = []

                for i, case in enumerate(st.session_state.batch_case_folders):
                    # 创建案例目录
                    case_name = f"{batch_case_prefix}_{i+1}_{case['name']}_{timestamp}"
                    case_dir = os.path.join(base_dir, case_name)
                    os.makedirs(case_dir, exist_ok=True)

                    # 读取原始 FST 文件内容
                    with open(case['fst_path'], 'r', encoding='utf-8') as f:
                        fst_content = f.read()

                    # 如果有参数修改，更新 FST 内容
                    param_key = f'batch_params_{i}'
                    if param_key in st.session_state.batch_param_values:
                        # 创建临时文件进行参数更新
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.fst', delete=False, encoding='utf-8') as f:
                            f.write(fst_content)
                            temp_path = f.name

                        try:
                            for param_name, param_value in st.session_state.batch_param_values[param_key].items():
                                update_fst_value(temp_path, param_name, param_value)

                            # 读取更新后的内容
                            with open(temp_path, 'r', encoding='utf-8') as f:
                                fst_content = f.read()
                        finally:
                            os.unlink(temp_path)

                    # 保存更新后的 FST 文件
                    new_fst_path = os.path.join(case_dir, case['fst_file'])
                    with open(new_fst_path, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(fst_content)

                    # 复制所有依赖文件
                    source_dir = case['path']
                    copied_files = []
                    for file in os.listdir(source_dir):
                        if any(file.endswith(ext) for ext in ['.dat', '.inp', '.txt', '.json', '.yaml', '.yml']):
                            src = os.path.join(source_dir, file)
                            dst = os.path.join(case_dir, file)
                            shutil.copy2(src, dst)
                            copied_files.append(file)

                    created_cases.append({
                        'name': case_name,
                        'dir': case_dir,
                        'fst_file': case['fst_file'],
                        'copied_files': copied_files
                    })

                st.session_state.batch_created_cases = created_cases
                st.success(f"✅ 已创建 {len(created_cases)} 个仿真案例")
                st.info("💡 现在可以点击【运行批量仿真】按钮开始计算")

        with col_save2:
            if st.button("▶️ 运行批量仿真", type="primary", key="run_batch_simulation"):
                # 检查是否已创建案例
                if 'batch_created_cases' not in st.session_state or not st.session_state.batch_created_cases:
                    st.warning("⚠️ 请先保存配置并创建案例")
                else:
                    # 运行批量仿真
                    st.session_state.batch_running = True
                    st.rerun()

        # 处理批量仿真运行
        if st.session_state.get('batch_running', False) and 'batch_created_cases' in st.session_state:
            st.markdown("---")
            st.markdown("#### 🔄 批量仿真运行中")

            progress_bar = st.progress(0)
            status_text = st.empty()
            output_placeholder = st.empty()

            results = []
            all_output = []

            for i, case_info in enumerate(st.session_state.batch_created_cases):
                status_text.text(f"正在处理 {i+1}/{len(st.session_state.batch_created_cases)}: {case_info['name']}")

                # 运行仿真
                openfast_exe = st.session_state.get('custom_openfast_path', OPENFAST_EXE) if st.session_state.get('use_custom_openfast', False) else OPENFAST_EXE

                try:
                    process = subprocess.Popen(
                        [openfast_exe, case_info['fst_file']],
                        cwd=case_info['dir'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )

                    output_lines = []
                    for line in process.stdout:
                        output_lines.append(line.rstrip())
                        all_output.append(f"[{case_info['name']}] {line.rstrip()}")

                    return_code = process.wait()
                    success = return_code == 0

                    results.append({
                        'name': case_info['name'],
                        'case_dir': case_info['dir'],
                        'fst_file': case_info['fst_file'],
                        'success': success,
                        'output': '\n'.join(output_lines)
                    })

                    if success:
                        st.success(f"✅ {case_info['name']} 仿真成功")
                    else:
                        st.error(f"❌ {case_info['name']} 仿真失败")

                except Exception as e:
                    results.append({
                        'name': case_info['name'],
                        'case_dir': case_info['dir'],
                        'fst_file': case_info['fst_file'],
                        'success': False,
                        'output': str(e)
                    })
                    st.error(f"❌ {case_info['name']} 仿真出错: {str(e)}")

                progress_bar.progress((i + 1) / len(st.session_state.batch_created_cases))

            status_text.text("批量仿真完成!")
            st.session_state.batch_results = results
            st.session_state.batch_running = False

            # 显示结果摘要
            st.markdown("---")
            st.markdown("#### 📊 批量仿真结果摘要")

            success_count = sum(1 for r in results if r['success'])
            fail_count = len(results) - success_count

            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric("成功", success_count)
            with col_res2:
                st.metric("失败", fail_count)

            # 显示详细输出
            with st.expander("📋 查看完整输出日志", expanded=False):
                for line in all_output[-100:]:  # 显示最后100行
                    st.text(line)

            if fail_count > 0:
                with st.expander("❌ 失败详情"):
                    for r in results:
                        if not r['success']:
                            st.markdown(f"**{r['name']}**")
                            st.text(r['output'])
                            st.markdown("---")

            if success_count > 0:
                st.success("✅ 批量仿真完成! 可以在【可视化分析】标签页中查看结果")

    else:
        st.info("💡 请先导入案例文件夹，然后配置参数并运行批量仿真")


# ==================== 可视化分析板块 ====================
with main_tabs[2]:
    st.markdown("### 📊 可视化分析")
    st.markdown("---")

    st.markdown("#### 📁 选择仿真结果文件夹")

    # 使用列布局来放置输入框和浏览按钮
    col_viz1, col_viz2 = st.columns([4, 1])

    viz_results_dir = ""
    with col_viz1:
        # 显示当前选择的路径
        current_viz_path = st.session_state.get('viz_results_dir', '')
        if current_viz_path:
            st.success(f"📁 已选择: `{current_viz_path}`")
        else:
            st.caption("💡 请选择仿真结果文件夹（包含 .out/.outb 文件）")

    with col_viz2:
        # 浏览文件夹按钮
        if st.button("📂 浏览", key="browse_viz_results", use_container_width=True):
            selected_path = select_directory()
            if selected_path:
                st.session_state.viz_results_dir = selected_path
                st.rerun()
            else:
                st.warning("未选择文件夹")

    # 同时也保留手动输入的选项
    with st.expander("或手动输入路径"):
        manual_viz_path = st.text_input(
            "结果文件夹路径",
            value=st.session_state.get('viz_results_dir', ''),
            placeholder=r"D:\results\simulation_20240101_120000",
            key="manual_viz_path"
        )
        if manual_viz_path and st.button("使用手动输入的路径", key="use_manual_viz"):
            st.session_state.viz_results_dir = manual_viz_path
            st.rerun()

    # 刷新按钮
    if st.session_state.get('viz_results_dir'):
        if st.button("🔄 刷新", key="refresh_viz"):
            st.rerun()

    # 如果选择了目录，显示可视化内容
    if st.session_state.get('viz_results_dir'):
        viz_dir = st.session_state.viz_results_dir

        # 查找结果文件
        out_files = [f for f in os.listdir(viz_dir) if (f.endswith('.outb') or (f.endswith('.out') and not f.endswith('.MD.out')))]

        if out_files:
            st.markdown(f"**找到 {len(out_files)} 个结果文件**:")

            # 排序：优先.outb文件，然后是.out文件
            out_files.sort(key=lambda x: (not x.endswith('.outb'), x))

            # 选择要可视化的文件
            selected_out_file = st.selectbox("选择结果文件", out_files)

            if selected_out_file:
                out_file_path = os.path.join(viz_dir, selected_out_file)

                st.markdown("---")
                st.markdown("#### 📈 时程曲线可视化")

                try:
                    # 读取文件
                    if selected_out_file.endswith('.outb'):
                        data, channel_names, channel_units, desc_str = read_fast_binary(out_file_path)
                    else:
                        data, channel_names, channel_units, desc_str = read_fast_text(out_file_path)

                    # 转换为 pandas DataFrame
                    df = pd.DataFrame(data, columns=channel_names)

                    st.success(f"✅ 成功读取文件: {selected_out_file}")
                    st.info(f"**数据点数**: {len(df)} | **通道数**: {len(channel_names)}")

                    # 通道选择
                    st.markdown("**选择要绘制的通道**:")

                    # 使用多选框
                    selected_channels = st.multiselect(
                        "选择通道（最多选择10个）",
                        options=channel_names,
                        default=channel_names[:min(5, len(channel_names))],
                        max_selections=10
                    )

                    if selected_channels:
                        # 创建图表
                        fig = go.Figure()

                        for channel in selected_channels:
                            if channel in df.columns:
                                fig.add_trace(go.Scatter(
                                x=df.index,
                                y=df[channel],
                                mode='lines',
                                name=channel,
                                line=dict(width=1.5)
                                ))

                        fig.update_layout(
                            title="时程曲线",
                            xaxis_title="时间步",
                            yaxis_title="值",
                            hovermode='x unified',
                            height=500
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # 统计信息
                        st.markdown("**统计信息**:")
                        cols = st.columns(min(4, len(selected_channels)))
                        for i, channel in enumerate(selected_channels):
                            if channel in df.columns:
                                with cols[i % 4]:
                                    data_series = df[channel]
                                st.metric(
                                label=channel,
                                value=f"{data_series.mean():.4f}",
                                delta=f"±{data_series.std():.4f}"
                                )

                except Exception as e:
                    st.error(f"❌ 读取文件失败: {str(e)}")
        else:
            st.warning("⚠️ 未找到结果文件 (.out 或 .outb)")
    else:
        st.info("💡 请先选择仿真结果文件夹，然后查看可视化结果")


# ==================== VTK 3D可视化板块 ====================
with main_tabs[3]:
    st.markdown("### 🎬 VTK 3D可视化")
    st.markdown("---")

    st.markdown("#### 📁 选择VTK结果文件夹")

    # 使用列布局来放置输入框和浏览按钮
    col_vtk1, col_vtk2 = st.columns([4, 1])

    with col_vtk1:
        # 显示当前选择的路径
        current_vtk_path = st.session_state.get('vtk_results_dir', '')
        if current_vtk_path:
            st.success(f"📁 已选择: `{current_vtk_path}`")
        else:
            st.caption("💡 请选择包含VTK文件的文件夹（通常在仿真结果目录下的vtk子目录）")

    with col_vtk2:
        # 浏览文件夹按钮
        if st.button("📂 浏览", key="browse_vtk_results", use_container_width=True):
            selected_path = select_directory()
            if selected_path:
                st.session_state.vtk_results_dir = selected_path
                st.rerun()
            else:
                st.warning("未选择文件夹")

    # 同时也保留手动输入的选项
    with st.expander("或手动输入路径"):
        manual_vtk_path = st.text_input(
            "VTK文件夹路径",
            value=st.session_state.get('vtk_results_dir', ''),
            placeholder=r"D:\results\simulation_20240101_120000\vtk",
            key="manual_vtk_path"
        )
        if manual_vtk_path and st.button("使用手动输入的路径", key="use_manual_vtk"):
            st.session_state.vtk_results_dir = manual_vtk_path
            st.rerun()

    # 刷新按钮
    if st.session_state.get('vtk_results_dir'):
        if st.button("🔄 刷新", key="refresh_vtk_tab"):
            st.rerun()

    # 如果选择了目录，显示可视化内容
    if st.session_state.get('vtk_results_dir'):
        vtk_dir = st.session_state.vtk_results_dir

        # 检查目录是否存在
        if not os.path.exists(vtk_dir):
            st.error(f"❌ 目录不存在: {vtk_dir}")
        else:
            # 查找VTK文件
            vtk_files = sorted([f for f in os.listdir(vtk_dir) if f.endswith('.vtp') or f.endswith('.vtk') or f.endswith('.vtu')])

            if not vtk_files:
                st.warning("⚠️ 未找到VTK文件（.vtp/.vtk/.vtu）")
                st.info("💡 请确保选择的目录包含OpenFAST生成的VTK输出文件")
            else:
                st.success(f"✅ 找到 {len(vtk_files)} 个VTK文件")

                # 分析文件命名模式，按时间步分组
                # OpenFAST VTK文件通常命名为: FAST.<Component>.<Timestep>.vtp
                timestep_groups = {}
                for filename in vtk_files:
                    # 尝试提取时间步（通常是最后一段数字）
                    parts = filename.split('.')
                    timestep = None
                    component = filename

                    # 查找数字部分作为时间步
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            timestep = int(part)
                            # 组件名是时间步之前的部分
                            component = '.'.join(parts[:i]) if i > 0 else 'unknown'
                            break

                    if timestep is None:
                        # 没有找到时间步，使用文件索引
                        timestep = len(timestep_groups)
                        component = filename.replace('.vtp', '').replace('.vtk', '').replace('.vtu', '')

                    if timestep not in timestep_groups:
                        timestep_groups[timestep] = []
                    timestep_groups[timestep].append({
                        'filename': filename,
                        'path': os.path.join(vtk_dir, filename),
                        'component': component
                    })

                # 按时间步排序
                sorted_timesteps = sorted(timestep_groups.keys())

                # 显示文件信息
                with st.expander("📁 VTK文件信息"):
                    st.write(f"**总文件数**: {len(vtk_files)}")
                    st.write(f"**时间步数**: {len(sorted_timesteps)}")
                    if timestep_groups:
                        st.write(f"**每步文件数**: {len(list(timestep_groups.values())[0])}")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**时间步分布**:")
                        for ts in sorted_timesteps[:10]:
                            st.text(f"  时间步 {ts}: {len(timestep_groups[ts])} 个文件")
                        if len(sorted_timesteps) > 10:
                            st.text(f"  ... 共 {len(sorted_timesteps)} 个时间步")
                    with col_b:
                        st.markdown("**组件示例**:")
                        if sorted_timesteps:
                            components = set([f['component'] for f in timestep_groups[sorted_timesteps[0]]])
                            for comp in list(components)[:5]:
                                st.text(f"  - {comp}")

                st.markdown("---")

                # VTK可视化控制面板
                st.markdown("#### 🎮 可视化控制")

                col_vtk_ctrl1, col_vtk_ctrl2, col_vtk_ctrl3 = st.columns([2, 1, 1])

                with col_vtk_ctrl1:
                    # 显示选项
                    show_edges_tab = st.checkbox("显示边框", value=False, key="show_edges_tab")
                    show_axes_tab = st.checkbox("显示坐标轴", value=True, key="show_axes_tab")

                with col_vtk_ctrl3:
                    # 背景颜色
                    bg_color_tab = st.selectbox(
                        "背景颜色",
                        ["白色", "黑色", "深灰", "浅灰"],
                        index=0,
                        key="bg_color_tab"
                    )
                    bg_map = {"白色": "white", "黑色": "black", "深灰": "#2b2b2b", "浅灰": "#f0f0f0"}
                    bg_hex_tab = bg_map[bg_color_tab]

                st.markdown("---")

                # 定义VTK文件加载函数
                @st.cache_data(ttl=3600)
                def load_vtk_file_tab(vtk_path):
                    """缓存VTK文件加载"""
                    try:
                        mesh = pv.read(vtk_path)
                        return mesh
                    except Exception as e:
                        st.error(f"加载文件失败: {e}")
                        return None

                # 定义颜色映射（为不同组件分配不同颜色）
                component_colors_tab = {}

                def get_component_color_tab(component_name):
                    """根据组件名称返回颜色"""
                    if component_name not in component_colors_tab:
                        # 为新组件分配颜色
                        colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
                                '#1abc9c', '#e67e22', '#34495e', '#7f8c8d', '#16a085']
                        idx = len(component_colors_tab) % len(colors)
                        component_colors_tab[component_name] = colors[idx]
                    return component_colors_tab[component_name]

                # 渲染指定时间步的所有VTK文件
                def render_timestep_tab(timestep_idx):
                    """渲染指定时间步的所有VTK文件"""
                    if timestep_idx >= len(sorted_timesteps):
                        return None

                    timestep = sorted_timesteps[timestep_idx]
                    files_in_timestep = timestep_groups[timestep]

                    # 创建绘图器
                    plotter = pv.Plotter(window_size=[1000, 700])
                    plotter.set_background(bg_hex_tab)
                    plotter.enable_anti_aliasing()

                    # 设置交互样式：启用Ctrl+左键平移
                    plotter.enable_trackball_style()

                    # 加载并添加所有网格
                    total_points = 0
                    total_cells = 0
                    components_loaded = []

                    for file_info in files_in_timestep:
                        mesh = load_vtk_file_tab(file_info['path'])
                        if mesh is not None:
                            color = get_component_color_tab(file_info['component'])
                            plotter.add_mesh(
                                mesh,
                                color=color,
                                show_edges=show_edges_tab,
                                edge_color="black" if show_edges_tab else None,
                                label=file_info['component']
                            )
                            total_points += mesh.n_points
                            total_cells += mesh.n_cells
                            components_loaded.append(file_info['component'])

                    # 添加坐标轴
                    if show_axes_tab:
                        plotter.add_axes()

                    # 添加图例
                    if len(components_loaded) > 1:
                        plotter.add_legend(bcolor=(0.1, 0.1, 0.1, 0.5), face='circle', size=(0.3, 0.2))

                    # 设置为等轴测视图
                    plotter.view_isometric()

                    return plotter, total_points, total_cells, components_loaded

                # 单帧查看模式
                col_frame_tab, col_view_tab = st.columns([1, 3])

                with col_frame_tab:
                    st.markdown("**选择帧**")
                    frame_index_tab = st.slider(
                        "时间步",
                        min_value=0,
                        max_value=len(sorted_timesteps) - 1,
                        value=0,
                        step=1,
                        key="frame_index_tab"
                    )

                    st.caption(f"时间步编号: {sorted_timesteps[frame_index_tab]}")

                    # 预设视图
                    st.markdown("**视图角度**")
                    view_preset_tab = st.selectbox(
                        "快速定位",
                        ["等轴测", "前视图", "后视图", "左视图", "右视图", "顶视图", "底视图"],
                        index=0,
                        key="view_preset_tab"
                    )

                with col_view_tab:
                    result_tab = render_timestep_tab(frame_index_tab)
                    if result_tab:
                        plotter_tab, total_points_tab, total_cells_tab, components_tab = result_tab

                        # 设置视图
                        view_map = {
                            "等轴测": lambda: plotter_tab.view_isometric(),
                            "前视图": lambda: plotter_tab.view_xy(),
                            "后视图": lambda: plotter_tab.view_xy(negative=True),
                            "左视图": lambda: plotter_tab.view_yz(),
                            "右视图": lambda: plotter_tab.view_yz(negative=True),
                            "顶视图": lambda: plotter_tab.view_xz(),
                            "底视图": lambda: plotter_tab.view_xz(negative=True),
                        }
                        view_map[view_preset_tab]()

                        # 导出HTML
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                            temp_html_path_tab = f.name
                        plotter_tab.export_html(temp_html_path_tab)
                        with open(temp_html_path_tab, 'r', encoding='utf-8') as f:
                            html_content_tab = f.read()
                        os.unlink(temp_html_path_tab)
                        st.components.v1.html(html_content_tab, height=700, scrolling=False)

                        # 显示网格信息
                        with st.expander("📊 网格信息"):
                            st.write(f"**总点数**: {total_points_tab:,}")
                            st.write(f"**总单元数**: {total_cells_tab:,}")
                            st.write(f"**组件数**: {len(components_tab)}")
                            st.write("**加载的组件**:")
                            for comp in components_tab:
                                color = get_component_color_tab(comp)
                                st.markdown(f"<span style='color:{color}'>■</span> {comp}", unsafe_allow_html=True)

                # 使用说明
                with st.expander("💡 交互说明"):
                    st.markdown("""
                    **鼠标操作**:
                        - 左键拖动: 旋转视角
                        - 滚轮滚动: 缩放

                    **使用说明**:
                        - 选择帧：通过滑块选择要查看的时间步
                        - 切换视图：使用预设视图按钮快速切换角度

                    **模型说明**:
                        - 不同组件使用不同颜色显示
                        - 图例显示各组件对应的颜色
                    """)
    else:
        st.info("💡 请选择包含VTK文件的文件夹以开始可视化")


# ==================== 语言指导板块 ====================
with main_tabs[4]:
    st.markdown("### 💬 语言指导 - 智能批量案例生成")
    st.markdown("---")

    st.info("📝 使用自然语言描述您的仿真需求，系统将自动生成多个仿真案例并配置参数")

    # 初始化 session_state
    if 'lang_guide_template_path' not in st.session_state:
        st.session_state.lang_guide_template_path = ""
    if 'lang_guide_template_content' not in st.session_state:
        st.session_state.lang_guide_template_content = None
    if 'lang_guide_template_name' not in st.session_state:
        st.session_state.lang_guide_template_name = None
    if 'lang_guide_generated_cases' not in st.session_state:
        st.session_state.lang_guide_generated_cases = []
    if 'lang_guide_confirmed_cases' not in st.session_state:
        st.session_state.lang_guide_confirmed_cases = []

    # ==================== 步骤1: 选择模板文件 ====================
    st.markdown("#### 📂 步骤 1: 选择 FST 模板文件")

    col_temp1, col_temp2, col_temp3 = st.columns([4, 2, 2])

    with col_temp1:
        template_path = st.text_input(
            "模板文件路径",
            value=st.session_state.lang_guide_template_path,
            placeholder=r"D:\software\openfast-4.2.1\reg_tests\r-test\glue-codes\openfast\5MW_OC4Semi_WSt_WavesWN\5MW_OC4Semi_WSt_WavesWN.fst",
            key="lang_guide_template_path_input",
            label_visibility="collapsed"
        )

    with col_temp2:
        if st.button("📂 浏览文件", key="lang_guide_browse_template", use_container_width=True):
            selected_file = select_fst_file()
            if selected_file:
                st.session_state.lang_guide_template_path = selected_file
                # 自动加载选中的文件
                try:
                    with open(selected_file, 'r', encoding='utf-8') as f:
                        st.session_state.lang_guide_template_content = f.read()
                    st.session_state.lang_guide_template_name = os.path.basename(selected_file)
                    st.session_state.lang_guide_generated_cases = []
                    st.session_state.lang_guide_confirmed_cases = []
                    st.success(f"✅ 已加载模板: {st.session_state.lang_guide_template_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 加载模板失败: {str(e)}")

    with col_temp3:
        if st.button("🔄 重新加载", key="lang_guide_load_template", use_container_width=True):
            if template_path and os.path.exists(template_path):
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        st.session_state.lang_guide_template_content = f.read()
                    st.session_state.lang_guide_template_path = template_path
                    st.session_state.lang_guide_template_name = os.path.basename(template_path)
                    st.session_state.lang_guide_generated_cases = []
                    st.session_state.lang_guide_confirmed_cases = []
                    st.success(f"✅ 已加载模板: {st.session_state.lang_guide_template_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 加载模板失败: {str(e)}")
            else:
                st.warning("⚠️ 请输入有效的模板文件路径")

    # 显示已加载的模板信息
    if st.session_state.lang_guide_template_name:
        st.success(f"📄 当前模板: **{st.session_state.lang_guide_template_name}**")

        # 解析模板参数
        template_param_info = parse_fst_file(st.session_state.lang_guide_template_path)
        st.caption(f"💡 模板包含 {len(template_param_info)} 个参数")

        # 显示关键参数预览
        with st.expander("🔍 查看模板参数预览"):
            param_preview = {}
            for key in ['TMax', 'DT', 'WrVTK', 'VTK_type', 'CompElast', 'CompAero', 'CompHydro']:
                if key in template_param_info:
                    param_preview[key] = template_param_info[key]['value']
            st.json(param_preview)

    # ==================== 步骤2: 输入需求描述 ====================
    st.markdown("---")
    st.markdown("#### 📝 步骤 2: 输入仿真需求描述")

    st.caption("💡 示例: '创建TMax分别为1,2,3的三个案例，都不需要VTK可视化' 或 '生成总仿真时间为10、20、30秒的三个案例，WrVTK都设为0'")

    user_prompt = st.text_area(
        "请描述您的仿真需求",
        placeholder="例如：创建TMax分别为1,2,3的三个案例，都不需要VTK可视化...",
        height=100,
        key="lang_guide_prompt"
    )

    col_gen1, col_gen2 = st.columns([3, 1])

    with col_gen1:
        st.caption("💡 提示：参数名称必须与FST文件中的名称一致（如 TMax、DT、WrVTK 等）")

    with col_gen2:
        generate_button = st.button("🤖 智能生成案例", type="primary", use_container_width=True)

    # ==================== 步骤3: 调用 API 分析并生成案例 ====================
    if generate_button:
        if not st.session_state.lang_guide_template_content:
            st.error("❌ 请先加载 FST 模板文件")
        elif not user_prompt.strip():
            st.warning("⚠️ 请输入仿真需求描述")
        else:
            # 调用 LLM API 解析需求
            with st.spinner("🤖 正在分析您的需求并生成案例..."):
                try:
                    # 导入必要的库
                    from dotenv import load_dotenv
                    from langchain_openai import ChatOpenAI
                    import json

                    load_dotenv()
                    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
                    os.environ['OPENAI_BASE_URL'] = os.getenv('OPENAI_BASE_URL')

                    # 创建 LLM 实例
                    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)

                    # 构建提示词
                    system_prompt = """你是一个OpenFAST仿真参数配置专家。用户将描述他们需要创建的仿真案例需求，你需要：

1. 分析用户需求，确定需要创建多少个案例
2. 为每个案例确定需要修改的参数及其值
3. 返回JSON格式的结构化数据

参数类型说明：
- bool: 布尔值 (True 或 False)
- int: 整数
- float: 浮点数
- select: 选择项 (如 1, 2, 3 等)

常见参数说明：
- TMax: 总仿真时间（秒）
- DT: 时间步长（秒）
- WrVTK: VTK可视化输出 (0=无, 1=仅初始化, 2=动画, 3=模态形状)
- VTK_type: VTK类型 (1=曲面, 2=网格, 3=所有)
- VTK_fps: VTK帧率
- CompElast: 结构动力学 (1, 2, 3)
- CompAero: 气动载荷 (0, 1, 2, 3)
- CompHydro: 水动力 (0, 1)
- Gravity: 重力加速度
- AirDens: 空气密度
- WtrDens: 水密度

请严格按照以下JSON格式返回：
{
  "case_count": 案例数量,
  "cases": [
    {
      "case_name": "案例1名称",
      "description": "案例1描述",
      "parameters": {
        "参数名": {"value": 参数值, "type": "参数类型"},
        ...
      }
    },
    ...
  ]
}

注意：
1. 参数名必须与FST文件中的完全一致
2. 案例名称应该简洁描述主要特点
3. 只包含用户明确要求修改的参数"""

                    user_message = f"""用户需求: {user_prompt}

请根据用户需求生成仿真案例配置。"""

                    response = llm.invoke([
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ])

                    # 解析响应
                    response_text = response.content
                    st.info("📤 AI 响应:")
                    st.text(response_text)

                    # 尝试提取JSON
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        json_str = json_match.group()
                        try:
                            parsed_data = json.loads(json_str)

                            # 验证数据结构
                            if 'cases' in parsed_data and isinstance(parsed_data['cases'], list):
                                # 为每个案例加载完整的模板参数
                                template_param_info = parse_fst_file(st.session_state.lang_guide_template_path)

                                generated_cases = []
                                for case_data in parsed_data['cases']:
                                    case_name = case_data.get('case_name', f"案例_{len(generated_cases)+1}")
                                    case_desc = case_data.get('description', '')

                                    # 从模板复制所有参数，然后应用修改
                                    case_params = {}
                                    for param_name, param_info in template_param_info.items():
                                        case_params[param_name] = {
                                            'value': param_info['value'],
                                            'description': param_info['description']
                                        }

                                    # 应用用户修改的参数
                                    if 'parameters' in case_data:
                                        for param_name, param_config in case_data['parameters'].items():
                                            if param_name in case_params:
                                                case_params[param_name]['value'] = param_config['value']

                                    generated_cases.append({
                                        'name': case_name,
                                        'description': case_desc,
                                        'parameters': case_params,
                                        'modified_params': case_data.get('parameters', {})
                                    })

                                st.session_state.lang_guide_generated_cases = generated_cases
                                st.success(f"✅ 成功生成 {len(generated_cases)} 个案例")
                                st.rerun()
                            else:
                                st.error("❌ AI 返回的数据格式不正确")
                        except json.JSONDecodeError as e:
                            st.error(f"❌ 解析 AI 响应失败: {str(e)}")
                    else:
                        st.error("❌ AI 响应中未找到有效的 JSON 数据")

                except ImportError as e:
                    st.error(f"❌ 缺少必要的库: {str(e)}")
                    st.info("💡 请安装: pip install python-dotenv langchain-openai")
                except Exception as e:
                    st.error(f"❌ 调用 AI API 失败: {str(e)}")

    # ==================== 步骤4: 确认和编辑参数 ====================
    if st.session_state.lang_guide_generated_cases:
        st.markdown("---")
        st.markdown("#### ✅ 步骤 3: 确认并编辑案例参数")

        st.info(f"📋 已生成 **{len(st.session_state.lang_guide_generated_cases)}** 个案例，请检查并确认参数")

        # 显示每个案例的参数编辑界面
        for i, case in enumerate(st.session_state.lang_guide_generated_cases):
            with st.expander(f"📁 案例 {i+1}: {case['name']}", expanded=True):
                col_case1, col_case2 = st.columns([3, 1])

                with col_case1:
                    st.caption(f"📝 {case['description']}")

                    # 修改案例名称
                    new_name = st.text_input(
                        "案例名称",
                        value=case['name'],
                        key=f"lang_guide_case_name_{i}"
                    )
                    if new_name != case['name']:
                        st.session_state.lang_guide_generated_cases[i]['name'] = new_name

                    # 显示已修改的参数
                    if case.get('modified_params'):
                        st.markdown("**AI 识别的参数修改:**")
                        mod_cols = st.columns(min(4, len(case['modified_params'])))
                        for j, (param_name, param_config) in enumerate(case['modified_params'].items()):
                            with mod_cols[j % len(mod_cols)]:
                                st.info(f"**{param_name}** = `{param_config['value']}`")

                with col_case2:
                    if st.button("⚙️ 编辑参数", key=f"lang_guide_edit_{i}"):
                        st.session_state[f'lang_guide_editing_{i}'] = not st.session_state.get(f'lang_guide_editing_{i}', False)
                        st.rerun()

                # 参数编辑界面
                if st.session_state.get(f'lang_guide_editing_{i}', False):
                    st.markdown("**参数编辑:**")

                    edit_tabs = st.tabs([
                        "仿真控制", "功能开关", "环境条件", "输出设置", "线性化", "可视化"
                    ])

                    # 仿真控制
                    with edit_tabs[0]:
                        col1, col2 = st.columns(2)
                        with col1:
                            if "Echo" in case['parameters']:
                                new_val = render_parameter_input(
                                    "Echo", "bool", case['parameters']["Echo"]['value'],
                                    None, f"LANG_SIM_CTRL_{i}", i
                                )
                                if new_val != case['parameters']["Echo"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["Echo"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["Echo"] = {'value': new_val, 'type': 'bool'}

                            if "TMax" in case['parameters']:
                                new_val = render_parameter_input(
                                    "TMax", "float", case['parameters']["TMax"]['value'],
                                    (1.0, 10000.0), f"LANG_SIM_CTRL_{i}", i
                                )
                                if new_val != case['parameters']["TMax"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["TMax"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["TMax"] = {'value': new_val, 'type': 'float'}

                            if "DT" in case['parameters']:
                                new_val = render_parameter_input(
                                    "DT", "float", case['parameters']["DT"]['value'],
                                    (0.001, 1.0), f"LANG_SIM_CTRL_{i}", i
                                )
                                if new_val != case['parameters']["DT"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["DT"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["DT"] = {'value': new_val, 'type': 'float'}

                        with col2:
                            if "AbortLevel" in case['parameters']:
                                new_val = render_parameter_input(
                                    "AbortLevel", "select", case['parameters']["AbortLevel"]['value'],
                                    ["WARNING", "SEVERE", "FATAL"], f"LANG_SIM_CTRL_{i}", i
                                )
                                if new_val != case['parameters']["AbortLevel"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["AbortLevel"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["AbortLevel"] = {'value': new_val, 'type': 'select'}

                            if "InterpOrder" in case['parameters']:
                                new_val = render_parameter_input(
                                    "InterpOrder", "int", case['parameters']["InterpOrder"]['value'],
                                    (1, 2), f"LANG_SIM_CTRL_{i}", i
                                )
                                if new_val != case['parameters']["InterpOrder"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["InterpOrder"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["InterpOrder"] = {'value': new_val, 'type': 'int'}

                    # 功能开关
                    with edit_tabs[1]:
                        col1, col2 = st.columns(2)
                        with col1:
                            if "CompElast" in case['parameters']:
                                new_val = render_parameter_input(
                                    "CompElast", "select", case['parameters']["CompElast"]['value'],
                                    [1, 2, 3], f"LANG_FEAT_{i}", i
                                )
                                if new_val != case['parameters']["CompElast"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["CompElast"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["CompElast"] = {'value': new_val, 'type': 'select'}

                            if "CompAero" in case['parameters']:
                                new_val = render_parameter_input(
                                    "CompAero", "select", case['parameters']["CompAero"]['value'],
                                    [0, 1, 2, 3], f"LANG_FEAT_{i}", i
                                )
                                if new_val != case['parameters']["CompAero"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["CompAero"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["CompAero"] = {'value': new_val, 'type': 'select'}

                        with col2:
                            if "CompHydro" in case['parameters']:
                                new_val = render_parameter_input(
                                    "CompHydro", "select", case['parameters']["CompHydro"]['value'],
                                    [0, 1], f"LANG_FEAT_{i}", i
                                )
                                if new_val != case['parameters']["CompHydro"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["CompHydro"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["CompHydro"] = {'value': new_val, 'type': 'select'}

                    # 可视化
                    with edit_tabs[5]:
                        col1, col2 = st.columns(2)
                        with col1:
                            if "WrVTK" in case['parameters']:
                                new_val = render_parameter_input(
                                    "WrVTK", "select", case['parameters']["WrVTK"]['value'],
                                    [0, 1, 2, 3], f"LANG_VIS_{i}", i
                                )
                                if new_val != case['parameters']["WrVTK"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["WrVTK"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["WrVTK"] = {'value': new_val, 'type': 'select'}

                        with col2:
                            if "VTK_type" in case['parameters']:
                                new_val = render_parameter_input(
                                    "VTK_type", "select", case['parameters']["VTK_type"]['value'],
                                    [1, 2, 3], f"LANG_VIS_{i}", i
                                )
                                if new_val != case['parameters']["VTK_type"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["VTK_type"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["VTK_type"] = {'value': new_val, 'type': 'select'}

                            if "VTK_fps" in case['parameters']:
                                new_val = render_parameter_input(
                                    "VTK_fps", "int", case['parameters']["VTK_fps"]['value'],
                                    (1, 60), f"LANG_VIS_{i}", i
                                )
                                if new_val != case['parameters']["VTK_fps"]['value']:
                                    st.session_state.lang_guide_generated_cases[i]['parameters']["VTK_fps"]['value'] = new_val
                                    st.session_state.lang_guide_generated_cases[i]['modified_params']["VTK_fps"] = {'value': new_val, 'type': 'int'}

                    if st.button("💾 完成编辑", key=f"lang_guide_done_edit_{i}"):
                        st.session_state[f'lang_guide_editing_{i}'] = False
                        st.rerun()

        st.markdown("---")

        # ==================== 步骤5: 创建案例并运行批量仿真 ====================
        st.markdown("#### 🚀 步骤 4: 创建案例并运行仿真")

        col_final1, col_final2 = st.columns([1, 1])

        # 案例名称前缀
        case_prefix = st.text_input("案例名称前缀", value="ai_generated", key="lang_guide_prefix")

        with col_final1:
            if st.button("💾 创建所有案例", type="primary", key="lang_guide_create_cases"):
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_dir = RESULTS_DIR

                    created_cases = []

                    for i, case in enumerate(st.session_state.lang_guide_generated_cases):
                        # 创建案例目录
                        case_name = f"{case_prefix}_{case['name']}_{timestamp}"
                        case_dir = os.path.join(base_dir, case_name)
                        os.makedirs(case_dir, exist_ok=True)

                        # 获取模板路径
                        template_path = st.session_state.lang_guide_template_path
                        template_dir = os.path.dirname(template_path)

                        # 复制模板 FST 文件到案例目录
                        fst_filename = st.session_state.lang_guide_template_name
                        new_fst_path = os.path.join(case_dir, fst_filename)
                        shutil.copy2(template_path, new_fst_path)

                        # 更新 FST 文件中的参数
                        for param_name, param_info in case['parameters'].items():
                            update_fst_value(new_fst_path, param_name, param_info['value'])

                        # 复制依赖文件
                        copied_files = []
                        if os.path.exists(template_dir):
                            for file in os.listdir(template_dir):
                                if any(file.endswith(ext) for ext in ['.dat', '.inp', '.txt', '.json', '.yaml', '.yml']):
                                    src = os.path.join(template_dir, file)
                                    dst = os.path.join(case_dir, file)
                                    if not os.path.exists(dst):
                                        shutil.copy2(src, dst)
                                        copied_files.append(file)

                        created_cases.append({
                            'name': case_name,
                            'dir': case_dir,
                            'fst_file': fst_filename,
                            'copied_files': copied_files,
                            'parameters': case['parameters']
                        })

                    st.session_state.lang_guide_created_cases = created_cases
                    st.success(f"✅ 已创建 {len(created_cases)} 个仿真案例")
                    st.info("💡 现在可以点击【运行批量仿真】按钮开始计算")
                except Exception as e:
                    st.error(f"❌ 创建案例失败: {str(e)}")

        with col_final2:
            if st.button("▶️ 运行批量仿真", type="primary", key="lang_guide_run_simulation"):
                if 'lang_guide_created_cases' not in st.session_state or not st.session_state.lang_guide_created_cases:
                    st.warning("⚠️ 请先创建案例")
                else:
                    st.session_state.lang_guide_running = True
                    st.rerun()

        # 处理批量仿真运行
        if st.session_state.get('lang_guide_running', False) and 'lang_guide_created_cases' in st.session_state:
            st.markdown("---")
            st.markdown("#### 🔄 批量仿真运行中")

            progress_bar = st.progress(0)
            status_text = st.empty()
            output_placeholder = st.empty()

            results = []

            for i, case_info in enumerate(st.session_state.lang_guide_created_cases):
                status_text.text(f"正在处理 {i+1}/{len(st.session_state.lang_guide_created_cases)}: {case_info['name']}")

                try:
                    process = subprocess.Popen(
                        [OPENFAST_EXE, case_info['fst_file']],
                        cwd=case_info['dir'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )

                    output_lines = []
                    for line in process.stdout:
                        output_lines.append(line.rstrip())
                        if len(output_lines) <= 50:  # 只显示前50行
                            output_placeholder.text(line.rstrip())

                    return_code = process.wait()
                    success = return_code == 0

                    results.append({
                        'name': case_info['name'],
                        'case_dir': case_info['dir'],
                        'fst_file': case_info['fst_file'],
                        'success': success,
                        'output': '\n'.join(output_lines)
                    })

                    if success:
                        st.success(f"✅ {case_info['name']} 仿真成功")
                    else:
                        st.error(f"❌ {case_info['name']} 仿真失败")

                except Exception as e:
                    results.append({
                        'name': case_info['name'],
                        'case_dir': case_info['dir'],
                        'fst_file': case_info['fst_file'],
                        'success': False,
                        'output': str(e)
                    })
                    st.error(f"❌ {case_info['name']} 仿真出错: {str(e)}")

                progress_bar.progress((i + 1) / len(st.session_state.lang_guide_created_cases))

            status_text.text("批量仿真完成!")
            st.session_state.lang_guide_results = results
            st.session_state.lang_guide_running = False

            # 显示结果摘要
            st.markdown("---")
            st.markdown("#### 📊 批量仿真结果摘要")

            success_count = sum(1 for r in results if r['success'])
            fail_count = len(results) - success_count

            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric("成功", success_count)
            with col_res2:
                st.metric("失败", fail_count)

            if success_count > 0:
                st.success("✅ 批量仿真完成! 可以在【可视化分析】标签页中查看结果")

    # 使用说明
    with st.expander("💡 使用说明"):
        st.markdown("""
        **步骤说明**:

        1. **选择模板**: 选择一个 FST 模板文件作为基础
        2. **描述需求**: 用自然语言描述您需要的案例（如："创建TMax为1,2,3的三个案例"）
        3. **确认参数**: 检查 AI 生成的参数，可以进行手动修改
        4. **创建并运行**: 创建案例文件夹并运行批量仿真

        **参数名称注意事项**:
        - TMax: 总仿真时间
        - DT: 时间步长
        - WrVTK: VTK可视化 (0=关闭, 1=仅初始化, 2=动画, 3=模态)
        - VTK_type: VTK类型 (1=曲面, 2=线框, 3=全部)
        - VTK_fps: VTK帧率
        - Gravity: 重力加速度
        - AirDens: 空气密度
        - WtrDens: 水密度
        - WtrDpth: 水深

        **示例描述**:
        - "创建TMax分别为1,2,3的三个案例，都不需要VTK可视化"
        - "生成总仿真时间为10、20、30秒的三个案例"
        - "创建两个案例：一个开启VTK动画，另一个关闭VTK"
        """)
