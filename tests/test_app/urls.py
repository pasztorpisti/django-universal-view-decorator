from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^regular_view_function/(?P<number>\d{1,5})/$', views.regular_view_function, name='regular_view_function'),
    url(r'^view_class/(?P<number>\d{1,5})/$', views.ViewClass.as_view(), name='view_class'),
    url(r'^view_subclass/(?P<number>\d{1,5})/$', views.ViewSubclass.as_view(), name='view_subclass'),
    url(r'^view_subclass2/(?P<number>\d{1,5})/$', views.ViewSubclass2.as_view(), name='view_subclass2'),
]
