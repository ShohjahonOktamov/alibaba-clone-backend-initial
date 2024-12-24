from django.urls import path, include

from .views import RetrieveCategoryView, ListCategoriesView, ListCategoryProductsView

urlpatterns = [
    path("categories/", include(
        [
            path('', ListCategoriesView.as_view()),
            path("<uuid:pk>/", include(
                [
                    path("", RetrieveCategoryView.as_view()),
                    path("products/", ListCategoryProductsView.as_view())

                ]
            ))
        ]
    ))
]
