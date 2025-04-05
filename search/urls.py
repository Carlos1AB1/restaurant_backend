from django.urls import path

from .views import (
    SearchDishesView,
    SearchSuggestionsView,
    ReindexView
)

urlpatterns = [
    path('dishes/', SearchDishesView.as_view(), name='search-dishes'),
    path('suggestions/', SearchSuggestionsView.as_view(), name='search-suggestions'),
    path('reindex/', ReindexView.as_view(), name='reindex'),
]