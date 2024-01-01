from django.urls import path
from my_app.views import keyword_view
from my_app.views import sign_up
from my_app.views import log_in,log_out,choose_chatbot

urlpatterns = [
    path('app/', keyword_view, name='keyword_form'),
    path('', sign_up, name='signup_form'),
    path("login/",log_in,name="login_form"),
    path("logout/",log_out,name="logout_form"),
    path("choose_chatbot/",choose_chatbot,name="choose_chatbot_form")
    
]