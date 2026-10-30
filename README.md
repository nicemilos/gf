# 小雅

使用 PySide6 开发的透明悬浮桌宠，角色素材保存在本地，离线运行。

## 直接下载使用（无需 Python）

进入 [最新 Release 下载页](https://github.com/nicemilos/gf/releases/latest)，选择 **Assets** 中的文件：

- `Xiaoya-版本-windows-x64-setup.exe`：安装版，双击安装到当前用户目录，无需管理员权限。带开始菜单入口，可选桌面快捷方式，可在 Windows 设置中卸载。
- `Xiaoya-版本-windows-x64-portable.zip`：免安装版，完整解压后双击 `Xiaoya.exe`。请保留旁边的 `_internal` 文件夹，不要直接在 ZIP 中运行。
- `SHA256SUMS.txt`：下载文件校验值；`Source code` 是源码，不是可直接运行的程序。

仅提供 Windows x64（64位 Intel/AMD）版本，已在 Windows 11 验证；Windows 10 兼容性尚未实机验证。不提供 macOS/Linux 包，当前密钥加密依赖 Windows DPAPI。

v0.1.1 起安装及卸载向导使用简体中文，程序和快捷方式使用小雅头像。重复打开会找回已运行的小雅，不再创建多个窗口；源码、免安装版和安装版共用单实例。升级前仍需退出旧版（v0.1.0 没有单实例保护）。

升级前从右键菜单退出旧版，再覆盖解压或运行新版安装程序。安装版与免安装版共用当前 Windows 用户的聊天、记忆和设置；卸载不会删除这些个人数据。换电脑时加密 Key 不能直接解密，需要重新填写。当前发行包尚未购买代码签名证书，Windows 可能显示未知发布者提示。

## 功能

- 始终置顶，鼠标拖动时显示跑步动作与方向，松开后恢复站立。
- 默认显示 Q 版；单击角色显示文字气泡，右键菜单切换 Q 版与接近原照的形象。
- 原版和Q版分别使用8张完整人物跑步图，12帧/秒；运行 `python preview_whole_run.py` 可切换两版逐帧检查。原版保持更小的头部和更修长的躯干、四肢。
- 轻微呼吸；新形象暂无配套闭眼帧。
- 两版独立头身比例的正侧面大步跑，使用完整人物绘图，手腿交替；Q 版长发向后扬起。
- 双击角色跳一下。
- 右键调整三档大小、开关动画或退出。
- 托盘菜单支持移回屏幕内和退出；支持模型配置、聊天、性格与持续记忆。

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

创建可分发的 ZIP 和安装 EXE（需安装 [Inno Setup 6](https://jrsoftware.org/isdl.php)）：

```powershell
python scripts/build_release.py --version 0.1.0 --iscc "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
```

输出在 `dist/release/`，脚本会先检查打包后的程序能否启动，再生成 ZIP、安装程序和 SHA256 校验文件。只收集运行所需图片，不包含开发预览、历史草稿、API Key 或聊天数据库。省略 `--iscc` 且 PATH 中没有编译器时只生成 ZIP。

`assets/app-icon.ico` 包含16到256像素图标，嵌入程序和安装 EXE；`scripts/build_icon.py` 从已确认的 Q 版图片绘制头像徽章（重新生成需 Pillow）。`packaging/ChineseSimplified.isl` 使用 [Inno Setup 简体中文翻译](https://github.com/jrsoftware/issrc/blob/main/Files/Languages/ChineseSimplified.isl)，保留原作者说明。

`.github/workflows/release.yml` 在推送 `v0.1.0` 这样的版本标签时自动运行检查、打包并发布 GitHub Release；手动运行 workflow 仅生成可下载的构建产物。Windows 之外的平台需要先适配和验证，再增加对应构建任务。

打包配置过滤了曾导致 Qt 启动失败的外部 ICU DLL，使用当前 Windows 系统的 ICU。不同 Windows 版本需要重新验证兼容性。

## 启动检查

```powershell
.venv\Scripts\python pet.py --smoke-test
dist\Xiaoya\Xiaoya.exe --smoke-test
```

检查模式创建窗口后自动退出。程序不会设置开机启动或上传角色图片。模型检测、聊天及自动记忆摘要会连接用户配置的模型服务。

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

角色素材由用户提供的参考照片经 AI 生成。本仓库未包含原始照片。

## 聊天、模型与记忆

左键单击显示本地文字气泡，双击跳跃，拖动仍跑步。右键菜单放在角色旁边，可进入聊天、模型配置、性格与记忆；呼吸动画使用开/关子菜单。“移回屏幕内”用于找回屏幕外的角色，“退出桌宠”关闭整个程序。

模型配置支持 DeepSeek、OpenRouter、本地 Ollama 与自定义 Chat Completions 兼容接口。填写接口、API Key 和模型；输入完成失去焦点后自动检测，也可点击检测按钮。获取模型列表后发送简短测试消息验证真实聊天权限。检测与聊天可能计入厂商额度。DeepSeek 默认使用非思考模式减少闲聊延迟；其他原生协议（例如仅支持 Anthropic Messages 的地址）目前不能直接接入。

Key 不要发到聊天里，在本机配置窗口填写。Windows DPAPI 加密存储，仅当前 Windows 用户可解密；密钥不会加入模型上下文、聊天日志或仓库。

性格、用户资料、长期记忆及完整聊天历史存储于 `%LOCALAPPDATA%/XiaoyaLocal/Companion/memory.sqlite3`，重启保留。每次聊天使用最近上下文、长期摘要与关键词匹配的相关旧对话。默认每8轮额外调用一次模型整理长期记忆，可关闭；这属于有容量限制的摘要记忆，不保证所有细节都被模型正确回忆。用户可编辑、纠正或清空记忆。清空聊天历史不会删除独立长期记忆。

聊天会将所需上下文发送给用户配置的模型厂商，头像及桌面截图不发送。当前为文字聊天，没有麦克风、语音合成、文件读取或系统执行工具。`XIAOYA_DATA_DIR` 可指定测试数据目录。

`companion.py` 管理本地状态、兼容接口、DPAPI和记忆；`companion_ui.py` 管理异步任务、聊天窗口、配置和气泡。运行 `python -m unittest test_companion -v` 使用本机模拟服务验证连接、失败密钥、跨重启记忆和密钥加密。真实厂商仍需用户在界面填Key后检测。

## 参考的开源方向

- [Desktop Cat Companion](https://github.com/d011ar/Desktop-Cat-Companion)：Python/PySide6桌宠，兼容接口聊天与本地偏好记忆，技术栈最接近当前项目。
- [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber)：语音、Live2D、桌宠模式，适合后续需要语音或Live2D时评估。
- [AIRI](https://github.com/moeru-ai/airi)：Web/Electron虚拟伙伴系统，功能完整，但不是可直接装入当前Qt窗口的组件。
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)：Nous Research的通用agent框架。其[记忆文档](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/memory.md)区分持久记忆和历史会话检索；[文件说明](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/which-file-does-what.md)解释SOUL.md性格、USER.md用户资料、MEMORY.md长期笔记。

本版参考上述架构思路，复用现有Qt、SQLite和标准兼容接口，未复制这些项目代码，也未安装或内嵌Hermes。保留现有人物和动画可避免整体迁移到另一个桌宠前端。未来接Hermes需要另加服务桥接，其记忆不会自动与本程序SQLite同步。
