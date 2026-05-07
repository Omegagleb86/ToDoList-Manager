from django.urls import path

from .views import AuthView, DashboardView, DemoApiView, LogoutView, TodoListDetailView

app_name = 'tasks'

urlpatterns = [
    path('auth/', AuthView.as_view(), name='auth'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('lists/<int:pk>/', TodoListDetailView.as_view(), name='list_detail'),
    path('api/demo/', DemoApiView.as_view(), name='demo_api'),
]
