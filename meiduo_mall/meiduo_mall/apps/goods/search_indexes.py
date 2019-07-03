import datetime
from haystack import indexes
from goods.models import SKU


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    #1,document=True,use_template=True可以单独提供模板来显示text字段
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return SKU

    def index_queryset(self, using=None):
        "Used when the entire index for model is updated."
        return self.get_model().objects.filter(is_launched=True)