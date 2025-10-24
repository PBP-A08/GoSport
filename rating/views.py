from django.shortcuts import render, get_object_or_404
from .models import ProductReview
from rating.forms import ProductReviewForm
from main.models import Product
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.html import strip_tags

@csrf_exempt
@require_POST
def add_review_ajax(request, id):
    product = get_object_or_404(Product, id=id)

    rating_raw = request.POST.get("rating")
    review = strip_tags(request.POST.get("review"))

    try:
        rating = int(rating_raw)
        if rating < 1 or rating > 5:
            return JsonResponse({"error": "Rating harus antara 1 sampai 5."}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Rating harus berupa angka."}, status=400)
    
    ProductReview.objects.create(
        product = product,
        user = request.user,
        rating = rating,
        review = review
    )

    return JsonResponse({"message": "CREATED"}, status=201)

@csrf_exempt
@require_POST
def edit_review_ajax(request, id):
    product = get_object_or_404(Product, id=id)
    
    # Ambil review yang sudah ada
    review = ProductReview.objects.filter(product=product, user=request.user).first()
    if not review:
        return HttpResponse(b"NOT_FOUND", status=404)

    rating_raw = request.POST.get("rating")
    review_text = strip_tags(request.POST.get("review"))

    try:
        rating = int(rating_raw)
        if rating < 1 or rating > 5:
            return JsonResponse({"error": "Rating harus antara 1 sampai 5."}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Rating harus berupa angka."}, status=400)
    
    review.rating = rating
    review.review = review_text
    review.save()

    return HttpResponse(b"UPDATED", status=200)

@csrf_exempt
def delete_review_ajax(request, id):
    product = get_object_or_404(Product, id=id)
    review = ProductReview.objects.filter(product=product, user=request.user).first()

    if not review:
        return HttpResponse(b"NOT_FOUND", status=404)
    
    review.delete()

    return HttpResponse(b"DELETED", status=200)

def show_rating_review_ajax(request, id):
    product = get_object_or_404(Product, id=id)
    sort_order = request.GET.get('sort', 'desc')

    reviews = ProductReview.objects.filter(product=product)

    current_user = request.user
    if sort_order == 'asc':
        reviews = reviews.order_by('rating')
    else:
        reviews = reviews.order_by('-rating')

    data = [
        {
            "user": r.user.username,
            "rating": r.rating,
            "review": r.review,
            "is_owner": current_user == r.user
        }
        for r in reviews
    ]
    return JsonResponse({"product": product.product_name, "reviews": data})

def helper_function(request, id):
    product = get_object_or_404(Product,id=id)
    try:
        review = ProductReview.objects.get(product=product, user=request.user)
        return JsonResponse({
                'has_review': True,
                "rating": review.rating,
                "review": review.review,
            })
    except ProductReview.DoesNotExist:
        return JsonResponse({'has_review': False})
# Create your views here.
