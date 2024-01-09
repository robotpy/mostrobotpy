# Force RTD to build zip with regular html builder, not single html
# The builder is preloaded after all extensions are loaded, so we can
# change the registered class here.

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.application import Sphinx
import sphinxext.photofinish as photofinish


class ReadtheDocsBuilderLocalMedia(StandaloneHTMLBuilder):
    name = "readthedocssinglehtmllocalmedia"


def setup(app):
    app.add_builder(ReadtheDocsBuilderLocalMedia, override=True)
