# alpha-jerry 开发日志

- [ ] csv 数据字段名为中文，增强可读性
- [ ] csv 字段单元格长度同字段值以及字段名长度对齐，不要我在 csv 中手动调整
- [ ] csv 中所有涉及到百分比的字段都有百分号后缀，保留两位小数
- [ ] 体现接口采用字段以及输出的供分析 csv 字段对应表
- [ ] 采用最新报告期的三表数据
- [ ] 替换科学计数法，用汉字表达数量级，保留两位小数
- [ ] 单列 csv 体现选择的接口对应的文档 URL
- [ ] 高速采集全部 A 股市场数据，文件格式，缓存和性能搭配策略

### 总结

- 数据子目录不手动建、不入库，由代码运行时自动创建，这样目录结构跟随数据生命周期，不污染版本库
- 先定义"接口"再写"实现"，未来换数据源时减少业务代码修改

## 待定

- [ ] 基于素材提炼各主要文件规范
- [ ] 搞懂架构的巧思和意义，为什么这么做
- [ ] 知识产权保护
- [ ] 法律风险
- [ ] 评审：果哥、昂哥、哥、郑哥
- [ ] 小红书收藏购物车
- [ ] 需求编程的 agent

## 参考资料

- [openclaw 源码解读和开发文档范例](https://www.moely.ai/resources/openclaw-framework-source-code-review)
- [RAG 公众号 * 2](https://mp.weixin.qq.com/s/t20kNKfMgdnUmUsD603p7g)
- [网页](https://wikimind.top/)
- [界面](https://quanttide.github.io/qtcloud-devops/)
- https://tushare.pro/document/2