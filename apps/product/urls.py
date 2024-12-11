from django.urls import path

from .views import GetCategoryView

urlpatterns = [
    path("categories/", GetCategoryView.as_view()),
    path("categories/<uuid:id>/", GetCategoryView.as_view())
]
