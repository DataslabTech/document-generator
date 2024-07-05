from typing import Any

from latex2mathml import converter
from lxml import etree  # type: ignore


def format_xml_replace():
    return (
        '<m:oMath xmlns:mml="http://www.w3.org/1998/Math/MathML">',
        (
            "<m:oMath"
            ' xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'  # noqa
        ),
    )


def latex_to_word(latex_input: str) -> Any:
    """Конвертувати latex формулу в Word представлення.

    Args:
      latex_input: Рядок latex формули.
    """
    mathml = converter.convert(latex_input)
    tree = etree.fromstring(mathml)  # type: ignore
    xslt = etree.parse("app/MML2OMML.XSL")  # type: ignore
    transform = etree.XSLT(xslt)
    new_dom = transform(tree)
    return new_dom.getroot()
