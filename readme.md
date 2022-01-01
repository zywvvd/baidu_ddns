### 百度云 DDNS 使用说明文档

利用百度 API 中的[ DNS 更新模块 ](https://cloud.baidu.com/doc/BCD/s/4jwvymhs7#%E6%9B%B4%E6%96%B0%E5%9F%9F%E5%90%8D%E8%A7%A3%E6%9E%90%E8%AE%B0%E5%BD%95)封装而成

#### 功能
- 动态获取本机指定 IP
- 自动对比当前本地 IP 与域名指向的IP
- 当本地 IP 发生变化时自动向远程同步
- 可以同步 A 记录（IPv4）和 AAAA 记录（IPv6）
- 可以配置同步频率，同步IP类型
- 保留较为完整的日志

#### 使用方法
1. 在 `assets/config.json` 中配置自己的一级域名和 AK、SK
2. 在 `main.py` 中配置更新频率与同步 IP 类型
3. 安装相关依赖包
```bash
pip install -r requirement.txt
```
4. 运行 `main.y`
```bash
python main.py
```

#### 参考资料
- https://cloud.baidu.com/doc/BCD/s/4jwvymhs7#%E6%9B%B4%E6%96%B0%E5%9F%9F%E5%90%8D%E8%A7%A3%E6%9E%90%E8%AE%B0%E5%BD%95
- https://blog.csdn.net/weixin_42169081/article/details/119299368