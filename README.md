# Metroid Dread Recomp v0.5.9 简体中文补丁

适用于 [Metroid Dread Recomp v0.5.9 Windows x64](https://github.com/yozander2009-stack/Metroid-Dread-Recomp/releases/tag/v0.5.9)。将 PC 启动器和游戏中按 **F1** 打开的设置菜单汉化，覆盖显示、图形、游戏、音频、控制、模组、高级设置和帮助等页面。游戏正文使用本体自带的简体中文，安装器默认选中它。诊断日志和部分上游错误提示可能显示英文。

补丁包含 PC 运行程序和对应的构建源码。请自行准备上游 Windows 原包及本地的《密特罗德：生存恐惧》2.1.0 数据。本仓库及发布包均不包含游戏本体、游戏代码 DLL、游戏资源、密钥或存档。

## 安装

需要 Windows 10/11 x64、Python 3.11 或更新版本。菜单加载系统自带的微软雅黑等中文字体。

1. 下载并解压上游原包 [MetroidDread-PC-v0.5.9-Windows-x64.zip](https://github.com/yozander2009-stack/Metroid-Dread-Recomp/releases/download/v0.5.9/MetroidDread-PC-v0.5.9-Windows-x64.zip)。
2. 在本仓库点 **Code → Download ZIP**，解压后在该目录打开 PowerShell。从 [补丁发布页](https://github.com/Passerby-real/metroid-dread-recomp-zh-cn/releases/tag/v0.5.9-zh.1) 下载 `MetroidDread-Recomp-v0.5.9-zh.1-Windows-x64.zip`，保留 ZIP。
3. 运行以下命令。把路径换成你的实际位置。`--source` 指向含原版 `Metroid Dread.exe` 的内层目录。`--output` 必须尚未存在，父目录需要已经存在。

   ```powershell
   py -3 .\install.py --source "D:\Games\Metroid Dread" --patch "D:\Downloads\MetroidDread-Recomp-v0.5.9-zh.1-Windows-x64.zip" --output "D:\Games\Metroid Dread 中文版"
   ```

   没有 `py` 命令时，可用 `python` 替换 `py -3`。

4. 双击输出目录中的 **Play Metroid Dread CN.cmd**。这个入口也适用于带中文的安装路径。若原版已完成 2.1.0 的首次设置，安装器会复制已验证的游戏模块和本地数据，可直接点「开始游戏」。若原版是刚解压的，请在中文版的「首次设置」中选含 `exefs` 和 `romfs` 的 2.1.0 目录，再点「开始安装」。进入游戏后按 **F1**。

### 校验、存档与更新

- 只校验文件时，把命令中的 `--output "…"` 替换成 `--check`。安装器校验原版 EXE、汉化 EXE 和已安装的 2.1.0 游戏 DLL。遇到错误或安装中断时，可以换一个新的输出目录重试。
- 中文版独立保存设置与存档。安装器只读取原安装所需文件，并在新目录写入，原安装和已有存档继续由原版入口使用。若想沿用进度，在两边都关闭后，可自行将旧版 `Metroid Dread_data\save` 复制到尚无存档的中文版目录。
- 本补丁针对 **PC 运行程序 v0.5.9**。游戏数据仍要求 **Switch 游戏数据 2.1.0**。上游「更新」会替换汉化运行程序。升级前请先查看仓库是否提供该版本的适配。

## 从源码构建

- Python 3.11 或更新版本。
- [上游 v0.5.9 标签源码 ZIP](https://codeload.github.com/yozander2009-stack/Metroid-Dread-Recomp/zip/refs/tags/v0.5.9)。构建脚本会校验这个归档。
- [WinLibs GCC 14.2.0 x64 UCRT POSIX](https://github.com/brechtsanders/winlibs_mingw/releases/tag/14.2.0posix-12.0.0-ucrt-r3) 和 [glslang 16.6.0 Windows x64](https://github.com/KhronosGroup/glslang/releases/tag/16.6.0)。请将工具解压在不含中文的路径中。

```powershell
py -3 .\build.py --upstream-zip "D:\Downloads\Metroid-Dread-Recomp-0.5.9.zip" --gcc-bin "D:\Tools\winlibs\mingw64\bin" --glslang "D:\Tools\glslang\bin\glslang.exe" --work "D:\DreadZhBuild"
```

构建目录必须尚未存在，也请使用纯英文路径。脚本用 `localize_ui.py` 将 [词表](zh-CN.txt) 接入上游的启动器和 F1 菜单，构建 Dear ImGui、原生 Vulkan 渲染器和 Windows x64 运行程序。构建运行程序无需游戏数据。自建程序的哈希可能与发布包不同，可以用自建 EXE 在独立的上游副本中测试。发布包的安装器只接受本仓库发布的预编译运行程序。

编辑词表时，每行按 `英文原文|简体中文` 编写，保留 `%s`、`%d` 等格式参数。首次发布的运行程序通过了链接、词表格式和中文字形检查，界面显示与游戏运行请以本机为准。

## 许可与致谢

本项目提供界面汉化及构建代码。含 ScarletNX 原生 Vulkan 渲染器的运行程序采用 [GPL-3.0](LICENSE-GPL-3.0.txt)。按上游要求保留 [Apache-2.0](LICENSE-Apache-2.0.txt) 及 [NOTICE](NOTICE.txt)。感谢 yozander2009-stack 的 Metroid Dread Recomp、**SwitchRecomp by MZ Labs**、ScarletNX、Dear ImGui 和各上游贡献者。《密特罗德：生存恐惧》的游戏版权归原权利人所有。
