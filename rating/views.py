from django.shortcuts import render, get_object_or_404
from .models import ProductReview
from rating.forms import ProductReviewForm
from main.models import Product
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.html import strip_tags
import uuid
import json

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

    ProductReview.update_avg_rating(product)
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
    
    ProductReview.update_avg_rating(product)

    return HttpResponse(b"UPDATED", status=200)

@csrf_exempt
def delete_review_ajax(request, id):
    product = get_object_or_404(Product, id=id)
    review = ProductReview.objects.filter(product=product, user=request.user).first()

    if not review:
        return HttpResponse(b"NOT_FOUND", status=404)
    
    review.delete()

    ProductReview.update_avg_rating(product)
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

def show_json(request, id):
    product = get_object_or_404(Product, id=id)
    reviews = ProductReview.objects.filter(product = product)
    current_user = request.user
    data = [
            {
                "user": r.user.username,
                "rating": r.rating,
                "review": r.review,
                "is_owner": current_user == r.user
            }
            for r in reviews
    ]

    data.sort(key=lambda x: (not x["is_owner"], -x["rating"]))

    return JsonResponse({"product_name": product.product_name, "id": id,"reviews": data})

@csrf_exempt
def add_and_edit_review_flutter(request, id):
    product = get_object_or_404(Product, id=id)
    old_review = ProductReview.objects.filter(product=product, user=request.user).first()
    if request.method == 'POST':
        if not old_review:
            try:
                data = json.loads(request.body)

                rate = int(data.get("rate", 0))
                review = strip_tags(data.get("review", ""))

                ProductReview.objects.create(
                    product = product,
                    user = request.user,
                    rating = rate,
                    review = review
                )
                ProductReview.update_avg_rating(product)
                return JsonResponse({"status": "success"}, status=201)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        try:
            data = json.loads(request.body)

            rate = int(data.get("rate", 0))
            review = strip_tags(data.get("review", ""))

            old_review.rating = rate
            old_review.review = review

            old_review.save()
            ProductReview.update_avg_rating(product)
            return JsonResponse({"status": "success"}, status=201)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
        
    return JsonResponse({"status": "error"}, status=401)

@csrf_exempt
def delete_review_flutter(request, id):
    product = get_object_or_404(Product, id=id)
    review = ProductReview.objects.filter(product=product, user=request.user).first()

    if not review:
        return JsonResponse({"status": "error"}, status=404)
    
    review.delete()

    ProductReview.update_avg_rating(product)

    return JsonResponse({"status": "success"}, status=200)

# Create your views here.
