# 🎯 公网访问配置 - 最后一步

## ✅ 已完成
- ✅ 网络连接正常
- ✅ SSH服务已运行
- ✅ 前端服务运行中 (端口3000)
- ✅ 后端服务运行中 (端口8000)

## ⏳ 还需一步：配置路由器端口转发

### 📱 图形界面操作（最简单）

1. **打开浏览器**
   ```
   http://192.168.0.1
   ```

2. **登录路由器**
   - 查看路由器背面标签上的账号密码
   - 常见默认账号：
     - admin / admin
     - admin / password
     - root / admin

3. **找到端口转发**

   根据路由器品牌，在以下位置之一寻找：
   - "端口转发" / "Port Forwarding"
   - "虚拟服务器" / "Virtual Server"
   - "NAT设置" / "NAT Settings"
   - "高级设置" → "端口转发"

4. **添加规则**

   点击"添加"或"新增"，填写：

   | 配置项 | 填写内容 |
   |-------|---------|
   | 服务名称 | SSH |
   | 外部端口 | 22 |
   | 内部IP | 192.168.0.137 |
   | 内部端口 | 22 |
   | 协议 | TCP |

5. **保存并重启**
   - 点击"应用"或"保存"
   - 重启路由器

### 🔧 配置完成后测试

运行测试脚本：
```bash
cd /Users/liulinlang/Documents/liulinlang/ai-study-companion
./test-public-access.sh
```

选择"y"测试公网SSH连接。

### 🎉 配置成功后使用

#### 从Mac/Linux建立隧道：
```bash
ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207
# 浏览器访问: http://localhost:3000
```

#### 从Windows建立隧道：
```powershell
ssh -f -N -L 3000:localhost:3000 liulinlang@125.118.5.207
```

#### 使用自动化脚本：
```bash
cd /Users/liulinlang/Documents/liulinlang/ai-study-companion
./ssh-tunnel.sh public frontend
```

### 📱 从手机访问

**iPhone/iPad：**
1. App Store下载"Termius"
2. 配置：Host=125.118.5.207, User=liulinlang
3. 设置端口转发：Local 3000 → localhost:3000
4. Safari访问：http://localhost:3000

**Android：**
1. Google Play下载"Termius"
2. 配置相同
3. Chrome访问：http://localhost:3000

---

## 📚 常见路由器端口转发位置

### TP-Link
转发规则 → 虚拟服务器

### 华为/中兴
高级设置 → NAT → 端口映射

### 小米
高级设置 → 端口转发

### 华硕(ASUS)
外部网络(WAN) → 端口转发

### 网件(Netgear)
高级 → 高级设置 → 端口转发

### 腾达
NAT → NAT设置 → 虚拟服务器

---

## ❓ 找不到端口转发？

1. **查看路由器说明书**
2. **访问路由器品牌官网支持页面**
3. **搜索"路由器型号 + 端口转发"**

---

## ✅ 验证配置

配置完成后，运行：
```bash
# 检查配置
./test-public-access.sh

# 测试公网SSH（选择y）
# 应该显示: ✓ 公网SSH端口可达！

# 建立隧道
./ssh-tunnel.sh public frontend

# 浏览器访问
# http://localhost:3000
```
