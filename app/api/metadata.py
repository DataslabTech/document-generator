"""Метадані для документації Swagger."""

tags_metadata = [
    {
        "name": "Шаблони",
        "description": "CRUD операції над шаблонами документів.",
    },
    {
        "name": "Версії шаблону",
        "description": "CRUD операції над версіями шаблону документу.",
    },
    {"name": "docx", "description": "Генерація .docx документів"},
    {"name": "Healthcheck", "description": "Первірка сервісу на доступність."},
]

template_json_body_example = {
    "DOC_TITLE": "My awesome document",
    "COL_ROWS": [
        {
            "COL1": "col11",
            "COL2": "col12",
            "COL3": "col13",
            "IMG|COL4": {
                "source": "https://logos-world.net/wp-content/uploads/2021/10/Python-Logo.png",
                "width": 5,
                "height": 5,
            },
        },
        {
            "COL1": "col21",
            "COL2": "col22",
            "COL3": "col23",
            "IMG|COL4": {
                "source": "https://logos-world.net/wp-content/uploads/2021/10/Python-Logo.png",
                "width": 5,
                "height": 5,
            },
        },
    ],
    "HEADER": "some header",
    "HEADER_MIDDLER": "middle header",
    "CONDITIONAL_P": True,
    "P_TEXT": "some paragraph if true",
    "QR|YOUTUBE": {
        "data": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "width": 15,
        "height": 15,
    },
    "MATH|FORMULA654": {
        "formula": "\\sum_{i=1}^{10}{\\frac{\\sigma_{zp,i}}{E_i} kN"
    },
    "IMG|IMAGE123": {
        "source": "https://logos-world.net/wp-content/uploads/2021/10/Python-Logo.png",
        "width": 15,
        "height": 15,
    },
}
