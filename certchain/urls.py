from django.urls import path
from . import views

urlpatterns = [
    path('',                      views.home,               name='home'),
    path('login/',                views.login_view,         name='login'),
    path('login/verify/',         views.verify_otp,         name='verify_otp'),
    path('logout/',               views.logout_view,        name='logout'),
    path('dashboard/',            views.dashboard,          name='dashboard'),
    path('dashboard/admin/',      views.dashboard_admin,    name='dashboard_admin'),
    path('dashboard/ente/',       views.dashboard_entecert, name='dashboard_entecert'),
    path('dashboard/ente/action/<int:student_id>/', views.ente_action, name='ente_action'),
    path('dashboard/student/',    views.dashboard_student,  name='dashboard_student'),
    path('dashboard/student/declare/', views.student_declare, name='student_declare'),
    path('dashboard/company/', views.dashboard_company, name='dashboard_company'),
    path('dashboard/admin/init-bn/',    views.init_bn,      name='init_bn'),
    path('dashboard/admin/create-user/', views.create_user, name='create_user'),
    path("deploy/", views.deploy_contract, name="deploy_contract"),
    path('dashboard/company/report/<int:student_id>/', views.company_view_report, name='azienda_view_report'),
]