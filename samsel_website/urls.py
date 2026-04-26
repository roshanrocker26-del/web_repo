from django.contrib import admin
from django.urls import path
from samsel_website import views
from .views import download_paper_pdf

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('our-story/', views.our_story, name='our_story'),
    path('request-demo/', views.request_demo, name='request_demo'),

    path('school-login/', views.school_login, name='school_login'),
    path('student-login/', views.student_login, name='student_login'),
    path('contact/', views.contact, name='contact'),
    path('products/', views.products, name='products'),
    path('school/dashboard/', views.school_dashboard, name='school_dashboard'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/', views.super_admin, name='super_admin'),
    path('super-admin-login/', views.super_admin_login, name='super_admin_login'),
    path('super-admin-logout/', views.super_admin_logout, name='super_admin_logout'),
    # School CRUD
    path('super-admin/school/add/', views.add_school, name='add_school'),
    path('super-admin/school/edit/<str:pk>/', views.edit_school, name='edit_school'),
    path('super-admin/school/delete/<str:pk>/', views.delete_school, name='delete_school'),
    # Book CRUD
    path('super-admin/book/add/', views.add_book, name='add_book'),
    path('super-admin/book/edit/<str:pk>/', views.edit_book, name='edit_book'),
    path('super-admin/book/delete/<str:pk>/', views.delete_book, name='delete_book'),

    path('logout/', views.admin_logout, name='admin_logout'),
    path('manage/assign-books/', views.assign_books, name='assign_books'),
    path('manage/delete-purchase/<int:pk>/', views.delete_purchase, name='delete_purchase'),
    path('manage/delete-school-purchases/<str:school_id>/', views.delete_school_purchases_admin, name='delete_school_purchases_admin'),
    path('super-admin/purchase/delete/<int:pk>/', views.delete_purchase_super, name='delete_purchase_super'),
    path('super-admin/purchase/assign/', views.assign_purchase_super, name='assign_purchase_super'),
    path('super-admin/get-school-info/', views.get_school_info, name='get_school_info'),
    path('super-admin/get-next-ids/', views.get_next_registration_ids, name='get_next_registration_ids'),

    path('manage/get-order-summary/', views.get_order_summary, name='get_order_summary'),
    path('manage/send-ebooks/', views.send_ebooks_to_school, name='send_ebooks_to_school'),
    path('manage/upload-syllabus/', views.upload_syllabus, name='upload_syllabus'),
    path('manage/revoke-syllabus/<int:pk>/', views.revoke_syllabus, name='revoke_syllabus'),
    path('manage/upload-question-paper/', views.upload_question_paper, name='upload_question_paper'),
    path('manage/upload-other-details/', views.upload_other_details, name='upload_other_details'),
    path('manage/revoke-other-details/<int:pk>/', views.revoke_other_details, name='revoke_other_details'),
    path('manage/delete-teacher-log/<int:pk>/', views.delete_teacher_log, name='delete_teacher_log'),
    path("get-chapters/", views.get_book_chapters, name="get_chapters_api"),
    path("generate-paper/", views.generate_paper, name="generate_paper"),
    path("download-paper/", download_paper_pdf, name="download_paper_pdf"),
    path('school-logout/', views.school_logout, name='school_logout'),
    path('school/upload-announcement/', views.upload_announcement, name='upload_announcement'),
    path('school/delete-announcement/<int:pk>/', views.delete_announcement, name='delete_announcement'),
    # OTP Authentication & Order Form
    path('order/send-otp/', views.send_otp, name='send_otp'),
    path('order/verify-otp/', views.verify_otp, name='verify_otp'),
    path('order-form/', views.order_form, name='order_form'),
    path('order/submit/', views.submit_order, name='submit_order'),

    # Product Detail Pages
    path('products/<slug:series_slug>/', views.series_detail, name='series_detail'),
    path('products/<slug:series_slug>/<slug:book_slug>/', views.book_detail, name='book_detail'),
]

