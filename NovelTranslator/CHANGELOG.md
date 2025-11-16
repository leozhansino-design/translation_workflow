# 更新日志 - Changelog

所有重要的项目更改都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵守 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布] - Unreleased

### 计划添加
- [ ] 翻译暂停/恢复功能
- [ ] 拖拽添加文件
- [ ] 更详细的进度条
- [ ] 翻译预览功能
- [ ] 自定义Prompt模板编辑器

## [1.0.0] - 2025-11-16

### 新增 - Added
- ✅ 批量翻译功能（支持多文件/文件夹）
- ✅ 多线程并发翻译（1-20线程可配置）
- ✅ 15种小说类型支持（40+写作风格）
- ✅ 智能资源分配（风格轮换+人名去重）
- ✅ 100+英文人名库（50男+70女）
- ✅ 实时翻译状态显示
- ✅ 成本追踪和统计
- ✅ 翻译历史记录
- ✅ API连接测试功能
- ✅ GUI界面（tkinter）
- ✅ 配置管理系统
- ✅ 本土化翻译Prompt
- ✅ PyInstaller打包支持
- ✅ 跨平台支持（Windows/Linux/Mac）

### 核心文件
- `main.py` - GUI主程序
- `translator.py` - 翻译逻辑
- `resource_mgr.py` - 资源管理
- `config.py` - 配置管理
- `build_exe.py` - 打包脚本

### 数据文件
- `data/styles.json` - 风格库
- `data/names.json` - 人名库
- `data/summary.json` - 翻译记录
- `data/config.json` - 用户配置

### 文档
- `README.md` - 项目说明
- `USAGE.md` - 使用指南
- `TECHNICAL.md` - 技术文档
- `PROJECT_SUMMARY.md` - 项目总结
- `CHANGELOG.md` - 更新日志
- `LICENSE` - MIT许可证

### 脚本
- `run.bat` / `run.sh` - 启动脚本
- `install.bat` / `install.sh` - 安装脚本

### 示例
- `examples/示例小说_Romance.txt` - 示例文件

### 支持的小说类型
1. Fantasy - 玄幻/奇幻
2. Romance - 言情
3. Urban - 都市
4. Sci-Fi - 科幻
5. Mystery - 悬疑
6. Horror - 恐怖
7. Adventure - 冒险
8. Historical - 历史
9. Crime - 犯罪
10. LGBTQ+ - 同志
11. Paranormal - 超自然
12. System - 系统流
13. Reborn - 重生
14. Revenge - 复仇
15. Fanfiction - 同人

### 技术特性
- 多线程并发处理
- 线程安全的GUI更新
- 原子性资源分配
- 精确的成本计算
- 智能人名提取
- 批量文件处理

## [0.1.0] - 2025-11-16 (开发版)

### 初始开发
- 项目架构设计
- 核心模块实现
- 数据结构设计
- GUI原型开发

---

## 版本说明

### 版本号规则
- MAJOR.MINOR.PATCH (主版本.次版本.修订号)
- MAJOR: 重大架构变更或不兼容的API修改
- MINOR: 向后兼容的新功能
- PATCH: 向后兼容的bug修复

### 发布周期
- 稳定版: 每月发布
- 修复版: 按需发布
- 开发版: 持续更新

### 升级指南

#### 从未来版本升级到1.0.0
（暂无）

#### 数据迁移
- config.json: 自动兼容
- styles.json: 可手动添加新类型
- names.json: 可手动添加新名字
- summary.json: 自动追加记录

---

## 贡献者

- Claude Code - 初始开发

## 反馈渠道

- Issues: GitHub Issues
- Email: (待添加)
- Discussion: GitHub Discussions

---

**注**: 本项目遵循语义化版本控制，所有重要更改都会记录在此文件中。
