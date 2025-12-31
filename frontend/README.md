# 前端项目说明

## 推荐方式：使用 HBuilderX（最简单）

1. 下载并安装 [HBuilderX](https://www.dcloud.io/hbuilderx.html)
2. 打开 HBuilderX
3. 文件 → 导入 → 从本地目录导入
4. 选择 `frontend` 目录
5. 运行 → 运行到小程序模拟器 → 微信开发者工具

## 方式二：使用 npm（需要手动配置）

如果使用 npm 方式，请按以下步骤：

### 1. 安装依赖

```powershell
npm install --legacy-peer-deps
```

如果仍有问题，尝试：

```powershell
npm cache clean --force
npm install --legacy-peer-deps
```

### 2. 运行项目

```powershell
npm run dev:mp-weixin
```

### 3. 在微信开发者工具中打开

编译完成后，在微信开发者工具中打开 `dist/dev/mp-weixin` 目录。

## 注意事项

- 确保已安装 Node.js（建议 16+ 版本）
- 如果遇到版本冲突，使用 `--legacy-peer-deps` 参数
- 推荐使用 HBuilderX，这是 Uni-app 官方推荐的开发工具

