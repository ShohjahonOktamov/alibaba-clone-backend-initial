from django.urls import path, include

from .views import RetrieveCategoryView, ListCategoriesView

urlpatterns = [
    path("categories/", include(
        [
            path('', ListCategoriesView.as_view()),
            path("<uuid:pk>/", RetrieveCategoryView.as_view())
        ]
    ))
]
