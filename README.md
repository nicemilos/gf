# 小雅 · Windows 桌宠

使用 PySide6 开发的透明悬浮桌宠，角色素材保存在本地，离线运行。

## 功能

- 始终置顶，鼠标拖动时显示跑步动作与方向，松开后恢复站立。
- 默认显示 Q 版；单击角色可在 Q 版与接近原照的形象之间切换，右键菜单也可切换。
- 原版和Q版分别使用8张完整人物跑步图，12帧/秒；运行 `python preview_whole_run.py` 可切换两版逐帧检查。原版保持更小的头部和更修长的躯干、四肢。
- 轻微呼吸；新形象暂无配套闭眼帧。
- 两版独立头身比例的正侧面大步跑：16帧完整循环，包含落地、后蹬、收腿、前摆和腾空；左右腿相差半个周期，上臂与同侧大腿反向摆动。
- 夸张展臂与动态屈肘、脚掌翻转、身体俯仰和衣摆回弹；Q 版长发向后扬起。
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
- `assets/q-open.png`、`assets/natural-open.png`：两版站立素材。
- `run_rig.py`：四肢关节轨迹、身体起伏、发梢摆动与16帧渲染。
- `assets/rig/`：内置 imagegen 生成的独立部件和原版侧面头部。
- `preview_run.py`：并排播放、逐帧、慢放和四肢颜色标记。运行 `python preview_run.py`。
- `test_run_rig.py`：检查半周期换边、手腿前后顺序、反向摆臂、骨长、大步幅、收腿、支撑/腾空、脚部轨迹连续性和绘制边界。
- `Xiaoya.spec`：Windows 打包配置。

角色素材由用户提供的参考照片经 AI 生成。本仓库未包含原始照片。当前版本不包含对话功能。
