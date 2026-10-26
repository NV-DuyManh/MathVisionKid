import re

definitions = {
    "số tự nhiên": "natural number",
    "số chẵn": "even number",
    "số lẻ": "odd number",
    "số bị trừ": "minuend",
    "số trừ": "subtrahend",
    "hiệu": "difference",
    "số hạng": "addend",
    "tổng": "sum",
    "thừa số": "factor",
    "tích": "product",
    "số bị chia": "dividend",
    "số chia": "divisor",
    "thương": "quotient",
    "số dư": "remainder",
    "phép chia hết": "division without remainders",
    "phép chia có dư": "division with remainders",
    "tính chất giao hoán": "commutative property",
    "tính chất kết hợpp": "associative property",
    "năm nhuận": "leap year",
}

unit_list = [
    'km', 'km^{2}', 'km^{3}', 'km2', 'km3',
    'hm', 'hm^{2}', 'hm^{3}', 'hm2', 'hm3', 'ha',
    'dam', 'dam^{2}', 'dam^{3}', 'dam2', 'dam3',
    'm', 'm^{2}', 'm^{3}', 'm2', 'm3',
    'dm', 'dm^{2}', 'dm^{3}', 'dm2', 'dm3',
    'cm', 'cm^{2}', 'cm^{3}', 'cm2', 'cm3',
    'mm', 'mm^{2}', 'mm^{3}', 'mm2', 'mm3',
    'tấn', 'tạ', 'yến', 'kg', 'hg', 'dag', 'g',
    'giờ', 'phút', 'ngày', 'tháng', 'năm'
]

unit_conversion_table = {
    "length": {
          "1 hm": "100 m",
          "1 dam": "10 m"
    },
    "mass": {
        "1 yến": "10 kg",
        "1 cân": "1 kg",
        "1 lạng": "100 g"
    },
    "area": [
        
    ],
    "volume": [],
    "time": []
}

TONENORMALIZE_DICT = (
    ("òa", "oà"),
    ("Òa", "Oà"),
    ("ÒA", "OÀ"),
    ("óa", "oá"),
    ("Óa", "Oá"),
    ("ÓA", "OÁ"),
    ("ỏa", "oả"),
    ("Ỏa", "Oả"),
    ("ỎA", "OẢ"),
    ("õa", "oã"),
    ("Õa", "Oã"),
    ("ÕA", "OÃ"),
    ("ọa", "oạ"),
    ("Ọa", "Oạ"),
    ("ỌA", "OẠ"),
    ("òe", "oè"),
    ("Òe", "Oè"),
    ("ÒE", "OÈ"),
    ("óe", "oé"),
    ("Óe", "Oé"),
    ("ÓE", "OÉ"),
    ("ỏe", "oẻ"),
    ("Ỏe", "Oẻ"),
    ("ỎE", "OẺ"),
    ("õe", "oẽ"),
    ("Õe", "Oẽ"),
    ("ÕE", "OẼ"),
    ("ọe", "oẹ"),
    ("Ọe", "Oẹ"),
    ("ỌE", "OẸ"),
    ("ùy", "uỳ"),
    ("Ùy", "Uỳ"),
    ("ÙY", "UỲ"),
    ("úy", "uý"),
    ("Úy", "Uý"),
    ("ÚY", "UÝ"),
    ("ủy", "uỷ"),
    ("Ủy", "Uỷ"),
    ("ỦY", "UỶ"),
    ("ũy", "uỹ"),
    ("Ũy", "Uỹ"),
    ("ŨY", "UỸ"),
    ("ụy", "uỵ"),
    ("Ụy", "Uỵ"),
    ("ỤY", "UỴ"),
)


close_tag_patterns = ["</span>", "</div>", "</p>", "</h[\d]>"]
open_tag_patterns = ["<div.*?>", "<span.*?>", "<p.*?>", "<h.*?>"]
CLOSE_TAG = re.compile("|".join(close_tag_patterns))
OPEN_TAG = re.compile("|".join(open_tag_patterns))


USER_PROMPT_TEMPLATE = r"""
{instruction}
{question}
{choices}
""".strip()
# Hãy suy luận từng bước và đặt đáp án mà bạn lựa chọn vào \box{{}}
