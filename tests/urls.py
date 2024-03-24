from django.urls import path

from tests.views import TestView

urlpatterns = [
    path('tests/', TestView.as_view(), name='test-view'),
]
