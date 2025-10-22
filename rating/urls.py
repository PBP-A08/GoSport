from django.urls import path
from rating.views import add_review_ajax,edit_review_ajax,delete_review_ajax,show_rating_review_ajax

app_name = 'rating'

urlpatterns = [
    path('add-review-ajax/<uuid:id>/', add_review_ajax, name='add_review_ajax'),
    path('edit-review-ajax/<uuid:id>/', edit_review_ajax, name='edit_review_ajax'),
]
