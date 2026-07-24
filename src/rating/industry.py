"""申万二级行业→五大类（brd.md §7.6 行业分类）纯映射。sw_l2_to_category 为唯一对外入口。"""

from __future__ import annotations

# 五大类标签
CAT_CYCLICAL = "周期资源"
CAT_CONSUMER = "大消费"
CAT_FINANCIAL = "证券金融"
CAT_TECH = "科技/制造"
CAT_UTILITY = "公用事业/基建"
CAT_UNKNOWN = "未分类"

FIVE_CATEGORIES: tuple[str, ...] = (CAT_CYCLICAL, CAT_CONSUMER, CAT_FINANCIAL, CAT_TECH, CAT_UTILITY)

# 申万二级行业名称 → 五大类
_SW_L2_TO_CATEGORY: dict[str, str] = {
    # ===== 周期资源 =====
    "石油开采": CAT_CYCLICAL,
    "石油化工": CAT_CYCLICAL,
    "油服工程": CAT_CYCLICAL,
    "煤炭开采": CAT_CYCLICAL,
    "焦炭": CAT_CYCLICAL,
    "贵金属": CAT_CYCLICAL,
    "工业金属": CAT_CYCLICAL,
    "能源金属": CAT_CYCLICAL,
    "小金属": CAT_CYCLICAL,
    "金属新材料": CAT_CYCLICAL,
    "普钢": CAT_CYCLICAL,
    "特钢": CAT_CYCLICAL,
    "冶钢原料": CAT_CYCLICAL,
    "化学原料": CAT_CYCLICAL,
    "化学制品": CAT_CYCLICAL,
    "农化制品": CAT_CYCLICAL,
    "化学纤维": CAT_CYCLICAL,
    "塑料": CAT_CYCLICAL,
    "橡胶": CAT_CYCLICAL,
    "非金属材料": CAT_CYCLICAL,
    "水泥": CAT_CYCLICAL,
    "玻璃玻纤": CAT_CYCLICAL,
    "装修建材": CAT_CYCLICAL,
    "种植业": CAT_CYCLICAL,
    "渔业": CAT_CYCLICAL,
    "饲料": CAT_CYCLICAL,
    "农产品加工": CAT_CYCLICAL,
    "养殖业": CAT_CYCLICAL,
    "动物保健": CAT_CYCLICAL,
    "林业": CAT_CYCLICAL,
    "造纸": CAT_CYCLICAL,
    # ===== 大消费 =====
    "白酒": CAT_CONSUMER,
    "非白酒": CAT_CONSUMER,
    "啤酒": CAT_CONSUMER,
    "其他酒类": CAT_CONSUMER,
    "食品加工": CAT_CONSUMER,
    "调味品": CAT_CONSUMER,
    "饮料乳品": CAT_CONSUMER,
    "休闲食品": CAT_CONSUMER,
    "服装家纺": CAT_CONSUMER,
    "饰品": CAT_CONSUMER,
    "纺织制造": CAT_CONSUMER,
    "包装印刷": CAT_CONSUMER,
    "文娱用品": CAT_CONSUMER,
    "家居用品": CAT_CONSUMER,
    "一般零售": CAT_CONSUMER,
    "专业连锁": CAT_CONSUMER,
    "互联网电商": CAT_CONSUMER,
    "旅游零售": CAT_CONSUMER,
    "酒店餐饮": CAT_CONSUMER,
    "旅游及景区": CAT_CONSUMER,
    "教育": CAT_CONSUMER,
    "专业服务": CAT_CONSUMER,
    "体育": CAT_CONSUMER,
    "化妆品": CAT_CONSUMER,
    "个护用品": CAT_CONSUMER,
    "医美": CAT_CONSUMER,
    "白色家电": CAT_CONSUMER,
    "黑色家电": CAT_CONSUMER,
    "小家电": CAT_CONSUMER,
    "家电零部件": CAT_CONSUMER,
    "照明设备": CAT_CONSUMER,
    "厨卫电器": CAT_CONSUMER,
    "化学制药": CAT_CONSUMER,
    "中药": CAT_CONSUMER,
    "生物制品": CAT_CONSUMER,
    "医疗器械": CAT_CONSUMER,
    "医药商业": CAT_CONSUMER,
    "医疗服务": CAT_CONSUMER,
    "房地产开发": CAT_CONSUMER,
    "房地产服务": CAT_CONSUMER,
    "乘用车": CAT_CONSUMER,
    "商用车": CAT_CONSUMER,
    "汽车零部件": CAT_CONSUMER,
    "汽车服务": CAT_CONSUMER,
    "摩托车及其他": CAT_CONSUMER,
    "游戏": CAT_CONSUMER,
    "影视院线": CAT_CONSUMER,
    "广告营销": CAT_CONSUMER,
    "数字媒体": CAT_CONSUMER,
    "出版": CAT_CONSUMER,
    "电视广播": CAT_CONSUMER,
    "贸易": CAT_CONSUMER,
    # ===== 证券金融 =====
    "国有大型银行": CAT_FINANCIAL,
    "股份制银行": CAT_FINANCIAL,
    "城商行": CAT_FINANCIAL,
    "农商行": CAT_FINANCIAL,
    "证券": CAT_FINANCIAL,
    "保险": CAT_FINANCIAL,
    "期货": CAT_FINANCIAL,
    "信托": CAT_FINANCIAL,
    "金融控股": CAT_FINANCIAL,
    "多元金融": CAT_FINANCIAL,
    "租赁": CAT_FINANCIAL,
    "综合": CAT_FINANCIAL,
    # ===== 科技/制造 =====
    "半导体": CAT_TECH,
    "元件": CAT_TECH,
    "光学光电子": CAT_TECH,
    "消费电子": CAT_TECH,
    "电子化学品": CAT_TECH,
    "软件开发": CAT_TECH,
    "IT服务": CAT_TECH,
    "计算机设备": CAT_TECH,
    "通信服务": CAT_TECH,
    "通信设备": CAT_TECH,
    "航空装备": CAT_TECH,
    "航天装备": CAT_TECH,
    "地面兵装": CAT_TECH,
    "航海装备": CAT_TECH,
    "军工电子": CAT_TECH,
    "通用设备": CAT_TECH,
    "专用设备": CAT_TECH,
    "自动化设备": CAT_TECH,
    "轨交设备": CAT_TECH,
    "工程机械": CAT_TECH,
    "光伏设备": CAT_TECH,
    "风电设备": CAT_TECH,
    "电池": CAT_TECH,
    "电网设备": CAT_TECH,
    "其他电源设备": CAT_TECH,
    "电机": CAT_TECH,
    "环境治理": CAT_TECH,
    "环保设备": CAT_TECH,
    # ===== 公用事业/基建 =====
    "电力": CAT_UTILITY,
    "燃气": CAT_UTILITY,
    "水务": CAT_UTILITY,
    "航空机场": CAT_UTILITY,
    "铁路公路": CAT_UTILITY,
    "航运港口": CAT_UTILITY,
    "物流": CAT_UTILITY,
    "房屋建设": CAT_UTILITY,
    "装修装饰": CAT_UTILITY,
    "基础建设": CAT_UTILITY,
    "专业工程": CAT_UTILITY,
    "工程咨询": CAT_UTILITY,
    "公交": CAT_UTILITY,
}


def sw_l2_to_category(l2_name: str) -> str:
    """申万二级行业名称 → 五大类标签。未知行业返回 ``未分类``。
    自动处理 SW 行业名中的罗马数字后缀（如 ``中药Ⅱ`` → ``中药``）。
    """
    if not l2_name:
        return CAT_UNKNOWN
    cat = _SW_L2_TO_CATEGORY.get(l2_name)
    if cat:
        return cat
    # 去掉末尾罗马数字 / 数字 / 空格后重试
    cleaned = l2_name.rstrip("ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ0123456789 ")
    if cleaned and cleaned != l2_name:
        cat = _SW_L2_TO_CATEGORY.get(cleaned)
        if cat:
            return cat
    return CAT_UNKNOWN
