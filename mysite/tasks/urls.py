from django.urls import path

from .views import DashboardView, DemoApiView, TodoListDetailView

app_name = 'tasks'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('lists/<int:pk>/', TodoListDetailView.as_view(), name='list_detail'),
    path('api/demo/', DemoApiView.as_view(), name='demo_api'),
]
