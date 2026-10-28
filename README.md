# 小雅 · Windows 桌宠

使用 PySide6 开发的透明悬浮桌宠，角色素材保存在本地，离线运行。

## 功能

- 始终置顶，可用鼠标拖动。
- 轻微呼吸与随机眨眼。
- 双击角色跳一下。
- 右键调整三档大小、开关动画或退出。
- 托盘菜单支持找回角色和退出。

## 从源码运行

需要 Windows 和 Python 3.10+；当前已在 Windows 11、Python 3.13 上验证。

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python pet.py
```

## 打包 EXE

在仓库根目录执行：

```powershell
.venv\Scripts\python -m pip install -r requirements-build.txt
.venv\Scripts\python -m PyInstaller --noconfirm Xiaoya.spec
```

产物为 `dist/Xiaoya/Xiaoya.exe`。分发时保留整个 `dist/Xiaoya` 文件夹，包含 `_internal` 依赖目录。

打包配置过滤了曾导致 Qt 启动失败的外部 ICU DLL，使用当前 Windows 系统的 ICU。不同 Windows 版本需要重新验证兼容性。

## 启动检查

```powershell
.venv\Scripts\python pet.py --smoke-test
dist\Xiaoya\Xiaoya.exe --smoke-test
```

检查模式创建窗口后自动退出。正常模式不会设置开机启动，也不会上传图片或连接网络。

## 文件

- `pet.py`：桌宠窗口、动画与菜单。
- `assets/open.png`：已确认的睁眼角色。
- `assets/blink.png`：基于相同角色生成的闭眼帧。
- `Xiaoya.spec`：Windows 打包配置。

角色素材由用户提供的参考照片经 AI 生成。本仓库未包含原始照片。当前版本不包含跑动或对话功能。
