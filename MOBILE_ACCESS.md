# 手机访问说明

## 局域网访问地址

确保手机和电脑连接到**同一个WiFi网络**，然后在手机浏览器中访问：

### 前端地址
```
http://192.168.0.137:3000
```

### 后端API
```
http://192.168.0.137:8000
```

## 检查网络连接

1. 确认电脑IP地址：`ifconfig | grep "inet " | grep -v 127.0.0.1`
2. 确认手机和电脑在同一WiFi
3. 在手机浏览器中访问 `http://192.168.0.137:3000`

## 如果无法访问

### 检查防火墙设置
```bash
# macOS 允许传入连接
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/python3
```

### 检查服务是否运行
```bash
# 检查后端
curl http://192.168.0.137:8000/health

# 检查前端
curl -I http://192.168.0.137:3000
```

### 查看服务状态
```bash
# 后端日志
tail -f backend.log

# 前端日志
tail -f frontend.log
```

## 更新IP地址

如果IP地址变化，需要更新以下文件：

1. **frontend/.env**
   ```
   VITE_API_URL=http://新IP:8000
   ```

2. **重启前端**
   ```bash
   kill -9 $(cat .frontend_pid)
   npm run dev -- --host
   ```

3. **重新构建前端**
   ```bash
   cd frontend
   npm run build
   ```
