from django.shortcuts import render
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cookieCart, cartData, guestOrder


def login_view(request):
    username=request.POST["username"]
    password=request.POST["password"]
    user=authenticate(request,username=username,password=password)
    if user is not None:
        login(request,user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request,"login.html",{"message":"Invalid credentials"}) 

def logout_view(request):
    logout(request)
    return render(request,"login.html",{"message":"Logged out."})

def signin_view(request):
    if request.method == "POST":
        first_name=request.POST["first_name"]
        last_name=request.POST["last_name"]
        username=request.POST["username"]
        email=request.POST["email"]
        password=request.POST["password"]
        password2=request.POST["password2"]
        if not password==password2:
            return render(request,"signin.html",{"message":"Passwords don't match."})
        user=User.objects.create_user(username,email,password)
        user.first_name=first_name
        user.last_name=last_name
        user.save()
        counter=Order_counter.objects.first()
        order_number=User_order(user=user,order_number=counter.counter)
        order_number.save()
        counter.counter=counter.counter+1
        counter.save()
        
        
        return render(request,"login.html",{"message":"Registered. You can log in now."}) 
    return render(request,"signin.html") 


def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)


def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode'],
		)

	return JsonResponse('Payment submitted..', safe=False)